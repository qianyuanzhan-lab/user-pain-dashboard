#!/usr/bin/env python3
"""
Hacker News 评论全量翻译脚本 V3
- 近1年评论 + 低质量过滤 + 增量翻译（已翻过的跳过）
- DeepSeek-Chat 并发翻译，版本B润色 prompt
- 输出 data/processed/hackernews_translated/{cat}_20260423_translated.json
  保留 content / content_zh 两个字段

用法：
  python3 translate_hn_v3.py --dry-run            # 只统计，不调 API
  python3 translate_hn_v3.py --cat wechat         # 只翻某个分类
  python3 translate_hn_v3.py                      # 全量翻译 4 个分类
"""

import os
import re
import sys
import json
import time
import html
import argparse
import urllib.request
import urllib.error
from pathlib import Path
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed

# ============================================
# 配置
# ============================================
ROOT = Path(__file__).parent.parent
RAW_DIR = ROOT / "data/raw/hackernews"
OUT_DIR = ROOT / "data/processed/hackernews_translated"
OUT_DIR.mkdir(parents=True, exist_ok=True)

CUTOFF = datetime(2025, 4, 28, tzinfo=timezone.utc)   # 近1年起点
API_URL = "https://api.deepseek.com/v1/chat/completions"
MODEL = "deepseek-chat"
MAX_WORKERS = 20
TIMEOUT = 60
MAX_RETRY = 3

# 加载 .env
def load_env():
    env_path = ROOT.parent / ".env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

load_env()
API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")

# ============================================
# HTML 实体清洗
# ============================================
HTML_ENTITIES = {
    "&#x27;": "'", "&quot;": '"', "&gt;": ">", "&lt;": "<",
    "&#x2F;": "/", "&amp;": "&", "&#x3D;": "=", "&nbsp;": " ",
    "&#32;": " ", "&#39;": "'", "&#34;": '"',
}

def clean_html(text: str) -> str:
    if not text:
        return ""
    for k, v in HTML_ENTITIES.items():
        text = text.replace(k, v)
    text = html.unescape(text)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text

# ============================================
# 低质量过滤（参考微信 convert_v3_to_json.py 的规则，适配英文）
# ============================================
LOW_QUALITY_PHRASES = {
    # 英文无意义短评
    "lol", "lmao", "rofl", "this", "that", "yes", "no", "yep", "nope",
    "+1", "-1", "ok", "k", "idk", "tbh", "imo", "fyi", "same",
    "indeed", "true", "false", "agreed", "disagree", "exactly",
    "right", "wrong", "wow", "huh", "meh", "bruh", "lmfao",
    "based", "cringe", "cope", "seethe", "mid", "sus",
    # 中文
    "哈哈", "呵呵", "同意", "不同意", "顶", "踩", "+1", "-1",
}

def is_low_quality(text: str) -> bool:
    """低质量判定：过短、纯短语、纯标点/emoji、纯链接"""
    if not text:
        return True
    t = text.strip()
    # 1. 太短
    if len(t) < 30:
        return True
    # 2. 纯标点/符号/emoji
    alnum = sum(1 for c in t if c.isalnum() or '\u4e00' <= c <= '\u9fff')
    if alnum / max(len(t), 1) < 0.4:
        return True
    # 3. 去除标点后落在无意义短语集合里
    stripped = re.sub(r"[^\w\u4e00-\u9fff]", "", t.lower())
    if stripped in LOW_QUALITY_PHRASES:
        return True
    # 4. 纯 URL
    if re.match(r"^https?://\S+$", t):
        return True
    # 5. 全大写怒吼且短（<60字）
    if len(t) < 60 and t.isupper():
        return True
    # 6. 重复字符
    if re.search(r"(.)\1{6,}", t):
        return True
    return False

# ============================================
# 时间过滤
# ============================================
def parse_date(s):
    if not s:
        return None
    try:
        s = str(s).replace("Z", "+00:00")
        d = datetime.fromisoformat(s)
        if d.tzinfo is None:
            d = d.replace(tzinfo=timezone.utc)
        return d
    except Exception:
        return None

def is_recent(item):
    dt = parse_date(item.get("created_at"))
    return dt is not None and dt >= CUTOFF

# ============================================
# 中文检测（判断是否已翻译）
# ============================================
def is_chinese(text: str) -> bool:
    if not text:
        return False
    chinese = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
    return chinese / max(len(text), 1) > 0.3

# ============================================
# 翻译 prompt (版本B：意译润色)
# ============================================
PROMPT_TEMPLATE = """你是一名熟悉技术社区与中文互联网表达的翻译。请把下面这条 Hacker News 评论翻译成自然的中文，规则：
1. 保留作者的吐槽/建议/抱怨/反思的真实语气，不要美化或拔高
2. 技术术语（如 API、token、prompt、LLM、SaaS 等）可保留英文
3. 让中文读者读起来像中文用户的真实表达，不要翻译腔
4. 只输出译文本身，不要解释、不要加引号、不要"译文："等前缀
5. 如果原文本就是中文，原样返回

英文原文：
"""

def translate_one(text: str, retry: int = 0) -> str:
    body = {
        "model": MODEL,
        "messages": [{"role": "user", "content": PROMPT_TEMPLATE + text}],
        "temperature": 0.3,
        "max_tokens": 800,
    }
    req = urllib.request.Request(
        API_URL,
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            result = json.loads(resp.read())
        return result["choices"][0]["message"]["content"].strip()
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as e:
        if retry < MAX_RETRY:
            time.sleep(2 * (retry + 1))
            return translate_one(text, retry + 1)
        return f"[翻译失败] {type(e).__name__}"

# ============================================
# 主流程
# ============================================
def process_category(cat: str, dry_run: bool = False):
    raw_path = RAW_DIR / f"{cat}_20260423.json"
    out_path = OUT_DIR / f"{cat}_20260423_translated.json"

    with open(raw_path, encoding="utf-8") as f:
        data = json.load(f)
    items = data.get("comments", [])

    # 加载已翻译映射
    existing = {}
    if out_path.exists():
        with open(out_path, encoding="utf-8") as f:
            old = json.load(f)
        for it in old.get("comments", []):
            if is_chinese(it.get("content_zh", "")):
                existing[it.get("id")] = it["content_zh"]

    # 过滤 + 分组
    recent = [it for it in items if is_recent(it)]
    cleaned = []
    skip_lowq = 0
    for it in recent:
        c = clean_html(it.get("content", ""))
        if is_low_quality(c):
            skip_lowq += 1
            continue
        it["content"] = c
        cleaned.append(it)

    to_translate = [it for it in cleaned if it.get("id") not in existing]
    already = len(cleaned) - len(to_translate)

    print(f"\n=== [{cat}] ===")
    print(f"  原始        : {len(items)}")
    print(f"  近1年       : {len(recent)}")
    print(f"  过滤低质量  : -{skip_lowq}  → 剩 {len(cleaned)}")
    print(f"  已翻译      : {already}")
    print(f"  本次待翻译  : {len(to_translate)}")

    if dry_run:
        return len(to_translate), 0

    # 真正翻译（并发）
    translated_map = dict(existing)
    t0 = time.time()
    done = 0

    def _task(item):
        zh = translate_one(item["content"])
        return item["id"], zh

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        futures = [pool.submit(_task, it) for it in to_translate]
        for fu in as_completed(futures):
            item_id, zh = fu.result()
            translated_map[item_id] = zh
            done += 1
            if done % 50 == 0 or done == len(to_translate):
                elapsed = time.time() - t0
                rate = done / max(elapsed, 0.001)
                eta = (len(to_translate) - done) / max(rate, 0.001)
                print(f"  [{cat}] 进度 {done}/{len(to_translate)}  "
                      f"速度 {rate:.1f}/s  剩 {eta:.0f}s")

    # 组装输出
    out_items = []
    for it in cleaned:
        it_out = dict(it)
        it_out["content_zh"] = translated_map.get(it["id"], "")
        out_items.append(it_out)

    out_data = {
        "category": cat,
        "source": "hackernews",
        "translated_at": datetime.now(timezone.utc).isoformat(),
        "total": len(out_items),
        "translated_count": sum(1 for x in out_items if is_chinese(x.get("content_zh", ""))),
        "comments": out_items,
    }
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out_data, f, ensure_ascii=False, indent=2)

    print(f"  ✅ 写入 {out_path}  用时 {time.time()-t0:.1f}s")
    return len(to_translate), time.time() - t0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="只统计不调 API")
    ap.add_argument("--cat", choices=["wechat", "social", "ai", "more"], help="只处理某分类")
    args = ap.parse_args()

    if not args.dry_run and not API_KEY:
        print("❌ DEEPSEEK_API_KEY 未设置")
        sys.exit(1)

    cats = [args.cat] if args.cat else ["wechat", "social", "ai", "more"]

    total_todo = 0
    total_time = 0
    for cat in cats:
        todo, elapsed = process_category(cat, dry_run=args.dry_run)
        total_todo += todo
        total_time += elapsed

    print(f"\n{'='*50}")
    print(f"总计待翻译 {total_todo} 条" + (f"，总用时 {total_time:.1f}s" if not args.dry_run else ""))


if __name__ == "__main__":
    main()
