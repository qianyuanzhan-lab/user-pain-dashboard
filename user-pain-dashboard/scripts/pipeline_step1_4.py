#!/usr/bin/env python3
"""
赛道管线 - Step 1-4: 加载 → 时间过滤 → 质量过滤 → 优质加分
================================================================
输入：三个数据源 (App Store / Google Play / Hacker News)
输出：data/processed/{category}_candidates.json
      - 统一的候选评论池，包含原始文本、元数据、来源、权重
      - 为后续 Step 5 (LLM 需求抽取) 提供输入

用法:
  python3 pipeline_step1_4.py --category social
  python3 pipeline_step1_4.py --category ai --since 2025-04-28
  python3 pipeline_step1_4.py --category all
"""

import os
import re
import json
import html
import argparse
from pathlib import Path
from datetime import datetime, timezone
from collections import defaultdict, Counter

ROOT = Path(__file__).parent.parent
RAW_DIR = ROOT / "data/raw"
TRANS_DIR = ROOT / "data/processed/hackernews_translated"
OUT_DIR = ROOT / "data/processed"
OUT_DIR.mkdir(parents=True, exist_ok=True)

DEFAULT_CUTOFF = datetime(2025, 4, 28, tzinfo=timezone.utc)

# 文件命名
APPSTORE_FILES = {"wechat": "wechat_20260423.json", "social": "social_20260423.json",
                  "ai": "ai_20260423.json", "more": "more_20260423.json"}
GOOGLEPLAY_FILES = {"wechat": "wechat_20260424.json", "social": "social_20260424.json",
                    "ai": "ai_20260424.json", "more": "more_20260424.json"}
HACKERNEWS_FILES = {"wechat": "wechat_20260423.json", "social": "social_20260423.json",
                    "ai": "ai_20260423.json", "more": "more_20260423.json"}

# ============================================
# HTML 实体清洗 (沿用 HN 翻译脚本)
# ============================================
HTML_ENTITIES = {
    "&#x27;": "'", "&quot;": '"', "&gt;": ">", "&lt;": "<",
    "&#x2F;": "/", "&amp;": "&", "&#x3D;": "=", "&nbsp;": " ",
    "&#32;": " ", "&#39;": "'", "&#34;": '"',
}

def clean_html(text):
    if not text: return ""
    for k, v in HTML_ENTITIES.items():
        text = text.replace(k, v)
    text = html.unescape(text)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text

# ============================================
# 筛选规则 (沿用自 convert_v3_to_json.py —— 微信 App Store 测试沉淀)
# ============================================
LOW_QUALITY_PATTERNS = [
    r'^.{0,15}$',                                           # 太短 (<=15字)
    r'^(垃圾|真垃圾|垃圾软件|差评|一星).{0,10}$',            # 纯情绪发泄
    r'(加两个0|加个0|给我加钱|还给我钱|还我钱)',             # 无意义玩笑/无理诉求
    r'^(好|不好|可以|还行|一般).{0,5}$',                     # 过于简短的评价
    r'(.)\1{5,}',                                            # 重复字符超过5个
    r'^(差评)+\s*(差评)*',                                   # "差评差评"重复开头
    r'搞抽象|整活|玩梗|os[:：]',                              # 网络梗/玩梗内容
    r'[😭🙃😅🤣😂💀]{2,}',                                   # emoji堆砌
    r'人民的好软件|良心软件',                                 # 反讽表达
    r'(一|有)?个叫.{2,8}的.{0,15}(花|扣|偷|拿).{0,5}(我的)?(钱|money)',
    r'(看|等)\d+秒.{0,5}广告',                               # 夸张反讽
    r'先看.{0,5}广告.{0,10}再看.{0,5}广告',                  # 重复夸张
]

INCOHERENT_PATTERNS = [
    r'。\s*[？?]', r'[？?]\s*[？?]', r'什么意思.{0,10}[？?]',
    r'我请问', r'你们能不能.{0,10}(管|处理)', r'太倒霉',
]

HIGH_QUALITY_INDICATORS = [
    '希望', '建议', '能不能', '可以', '如果', '为什么',
    '每次', '总是', '经常', '一直', '有时候',
    '之前', '以前', '更新后', '现在',
    '工作', '生活', '学习', '重要',
    '导致', '影响', '无法', '不能',
    # 英文补充 (给 HN 未翻译兜底用)
    'I wish', 'I hope', 'should', 'would be', "can't", 'cannot',
    'every time', 'always', 'since update', 'broken', 'frustrating',
]

def is_incoherent_content(content):
    sentences = [s.strip() for s in re.split(r'[。！？?!]', content) if len(s.strip()) > 3]
    q_marks = content.count('？') + content.count('?')
    if len(sentences) > 0 and q_marks > len(sentences) * 0.5:
        return True
    if sum(1 for p in INCOHERENT_PATTERNS if re.search(p, content)) >= 2:
        return True
    if len(sentences) >= 4:
        kws = [set(re.findall(r'[\u4e00-\u9fa5]{2,4}', s)) for s in sentences]
        if len(kws) >= 3:
            overlaps = [len(kws[i] & kws[i+1]) for i in range(len(kws)-1)]
            if sum(overlaps) / len(overlaps) < 0.5:
                return True
    return False

def assess_quality(content):
    """返回 (score, reason)。score<=0 即淘汰。"""
    if not content or len(content) < 20:
        return 0, "too_short"
    score = 5.0
    length = len(content)
    if length < 30: score -= 2
    elif length >= 100: score += 2
    elif length >= 50: score += 1

    for p in LOW_QUALITY_PATTERNS:
        if re.search(p, content):
            return 0, f"low_quality_pattern:{p[:30]}"

    if is_incoherent_content(content):
        return 0, "incoherent"

    hq = sum(1 for ind in HIGH_QUALITY_INDICATORS if ind in content)
    score += min(hq * 0.5, 2)
    return score, f"hq={hq}"

# ============================================
# 时间解析
# ============================================
def parse_date(s):
    if not s: return None
    try:
        s = str(s).replace("Z", "+00:00")
        d = datetime.fromisoformat(s)
        if d.tzinfo is None:
            d = d.replace(tzinfo=timezone.utc)
        return d
    except Exception:
        return None

# ============================================
# 三源 loader
# ============================================
def load_appstore(category, cutoff):
    path = RAW_DIR / "appstore" / APPSTORE_FILES[category]
    if not path.exists(): return []
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    out = []
    for r in data.get("reviews", []):
        dt = parse_date(r.get("date"))
        if not dt or dt < cutoff: continue
        out.append({
            "id": f"as_{r.get('id') or hash(r.get('content',''))}",
            "content": r.get("content", "").strip(),
            "content_zh": r.get("content", "").strip(),   # 原本就是中文
            "rating": r.get("rating", 0),
            "author": r.get("author", ""),
            "date": dt.strftime("%Y-%m-%d"),
            "app_name": r.get("app_name", ""),
            "source": "appstore",
            "source_url": r.get("url", ""),
            "weight_signal": r.get("rating", 3),           # 低评分 = 痛点强
        })
    return out

def load_googleplay(category, cutoff):
    path = RAW_DIR / "googleplay" / GOOGLEPLAY_FILES[category]
    if not path.exists(): return []
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    out = []
    for r in data.get("reviews", []):
        dt = parse_date(r.get("date"))
        if not dt or dt < cutoff: continue
        out.append({
            "id": f"gp_{r.get('reviewId') or r.get('id') or hash(r.get('content',''))}",
            "content": r.get("content", "").strip(),
            "content_zh": r.get("content", "").strip(),
            "rating": r.get("rating", 0),
            "author": r.get("author", ""),
            "date": dt.strftime("%Y-%m-%d"),
            "app_name": r.get("app_name", ""),
            "source": "googleplay",
            "source_url": r.get("url", ""),
            "weight_signal": r.get("rating", 3),
        })
    return out

def load_hackernews(category, cutoff):
    """优先使用翻译后的中文，回退到原文。
    
    关键：对 HN 做主题相关性过滤，只保留真正讨论该赛道的评论。
    HN 的话题极其发散，大量评论只是顺带提及某个产品 —— 如果不过滤，
    会把"讨论 Apple 政策时顺带提了一句 WeChat"的噪声混进微信赛道。
    """
    trans_path = TRANS_DIR / f"{category}_20260423_translated.json"
    raw_path = RAW_DIR / "hackernews" / HACKERNEWS_FILES[category]

    # 各赛道的强主题关键词（HN story_title 或评论正文里必须命中其一才保留）
    TOPIC_KEYWORDS = {
        "wechat": ["wechat", "微信", "weixin", "tencent", "mini program", "小程序"],
        "social": ["social media", "dating", "tiktok", "instagram", "discord",
                   "reddit", "twitter", " x ", "facebook", "meta", "telegram",
                   "whatsapp", "signal", "messaging", "community", "社交"],
        "ai": ["ai ", "llm", "gpt", "chatgpt", "claude", "gemini", "copilot",
               "openai", "anthropic", "model ", "prompt", "agent", "neural",
               "machine learning", "deep learning", "人工智能", "大模型", "coding assistant"],
        "more": ["productivity", "workflow", "note", "obsidian", "notion",
                 "calendar", "task", "todo", "spreadsheet", "form",
                 "api ", "saas", "tool", "app store", "effic"],
    }
    keywords = [k.lower() for k in TOPIC_KEYWORDS.get(category, [])]

    def is_on_topic(story_title, content_text):
        """命中：story_title 或 content 里至少出现一个主题关键词"""
        if not keywords:
            return True
        text = (f"{story_title} {content_text}").lower()
        return any(kw in text for kw in keywords)

    trans_map = {}
    if trans_path.exists():
        with open(trans_path, encoding="utf-8") as f:
            td = json.load(f)
        for c in td.get("comments", []):
            zh = c.get("content_zh", "")
            if zh and any('\u4e00' <= ch <= '\u9fff' for ch in zh):
                trans_map[c.get("id")] = zh

    if not raw_path.exists(): return []
    with open(raw_path, encoding="utf-8") as f:
        data = json.load(f)

    out = []
    skipped_off_topic = 0
    for c in data.get("comments", []):
        dt = parse_date(c.get("created_at"))
        if not dt or dt < cutoff: continue
        en = clean_html(c.get("content", ""))
        zh = trans_map.get(c.get("id"), "")
        story_title = c.get("story_title", "")

        # 主题相关性过滤
        if category == "wechat":
            # 微信赛道完全不用 HN 数据 —— HN 讨论的是苹果政策/tencent 生态等
            # 技术视角，与微信本地用户的真实痛点无关。保留下来只会引入噪声。
            skipped_off_topic += 1
            continue
        else:
            if not is_on_topic(story_title, f"{en} {zh}"):
                skipped_off_topic += 1
                continue

        out.append({
            "id": f"hn_{c.get('id')}",
            "content": en,
            "content_zh": zh or en,
            "rating": 0,     # HN 没评分
            "author": c.get("author", ""),
            "date": dt.strftime("%Y-%m-%d"),
            "app_name": "",
            "story_title": story_title,
            "points": c.get("points", 0),
            "source": "hackernews",
            "source_url": c.get("source_url", ""),
            "weight_signal": min((c.get("points", 0) or 0) / 10 + 1, 5),   # upvote 权重归一到 1-5
            "has_translation": bool(zh),
        })

    if skipped_off_topic:
        print(f"    [HN] 过滤掉 {skipped_off_topic} 条主题不相关的评论")
    return out

# ============================================
# 主流程
# ============================================
def process_category(category, cutoff, min_score=2.0):
    print(f"\n{'='*70}")
    print(f"【处理赛道】{category}  (时间窗口 >= {cutoff.strftime('%Y-%m-%d')})")
    print(f"{'='*70}")

    # Step 1: 三源加载 + 时间过滤
    as_items = load_appstore(category, cutoff)
    gp_items = load_googleplay(category, cutoff)
    hn_items = load_hackernews(category, cutoff)
    all_items = as_items + gp_items + hn_items
    print(f"\n[Step 1-2] 三源加载 + 时间过滤:")
    print(f"  App Store:   {len(as_items)}")
    print(f"  Google Play: {len(gp_items)}")
    print(f"  Hacker News: {len(hn_items)} (含翻译 {sum(1 for x in hn_items if x.get('has_translation'))})")
    print(f"  合计: {len(all_items)}")

    # Step 3+4: 质量过滤 + 优质加分
    candidates = []
    reason_stats = Counter()
    for it in all_items:
        # 选用中文文本做质量判定（HN 已翻译，AS/GP 原本就是中文）
        text = it.get("content_zh") or it.get("content", "")
        score, reason = assess_quality(text)
        if score >= min_score:
            it["quality_score"] = round(score, 2)
            it["quality_reason"] = reason
            candidates.append(it)
        else:
            reason_stats[reason.split(":")[0]] += 1

    print(f"\n[Step 3-4] 质量过滤 + 优质加分:")
    print(f"  输入: {len(all_items)}  →  候选池: {len(candidates)}  (保留率 {len(candidates)/max(len(all_items),1)*100:.1f}%)")
    print(f"  淘汰原因 Top5:")
    for r, c in reason_stats.most_common(5):
        print(f"    {r}: {c}")

    # 按来源 & 产品分布
    src_count = Counter(c.get("source") for c in candidates)
    app_count = Counter(c.get("app_name") or c.get("story_title", "HN")[:30] for c in candidates)
    print(f"\n  候选池来源分布:")
    for s, n in src_count.most_common():
        print(f"    {s}: {n}")
    print(f"  Top 10 产品/话题:")
    for a, n in app_count.most_common(10):
        print(f"    [{n:>4}] {a}")

    # 输出
    out_path = OUT_DIR / f"{category}_candidates.json"
    out_data = {
        "category": category,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "cutoff": cutoff.isoformat(),
        "stats": {
            "raw_total": len(all_items),
            "candidate_total": len(candidates),
            "by_source": dict(src_count),
            "by_app": dict(app_count.most_common(30)),
        },
        "candidates": candidates,
    }
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out_data, f, ensure_ascii=False, indent=2)
    print(f"\n✅ 写入 {out_path}")
    return out_data


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--category", required=True, choices=["wechat", "social", "ai", "more", "all"])
    ap.add_argument("--since", default="2025-04-28", help="时间窗口起点 YYYY-MM-DD")
    ap.add_argument("--min-score", type=float, default=2.0, help="质量分阈值")
    args = ap.parse_args()

    cutoff = datetime.strptime(args.since, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    cats = ["wechat", "social", "ai", "more"] if args.category == "all" else [args.category]
    for c in cats:
        process_category(c, cutoff, args.min_score)

if __name__ == "__main__":
    main()
