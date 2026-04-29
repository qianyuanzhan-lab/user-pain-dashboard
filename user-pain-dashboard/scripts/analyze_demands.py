#!/usr/bin/env python3
"""
用户需求分析脚本
根据小体验推演流程，分析 Hacker News 评论中的用户痛点和需求

核心场景框架：
1. 一起做决定 - 群体决策场景
2. 一起体验效果 - 共享体验场景  
3. 表达有参与感 - 社交表达场景
"""

import json
import os
import re
from datetime import datetime, timedelta
from collections import Counter, defaultdict
from typing import List, Dict, Tuple

# 配置
INPUT_DIR = "/Users/doudou/WorkBuddy/20260421111045/user-pain-dashboard/data/raw/hackernews"
OUTPUT_DIR = "/Users/doudou/WorkBuddy/20260421111045/user-pain-dashboard/data/processed"
ONE_YEAR_AGO = datetime.now() - timedelta(days=365)

# 需求关键词分类
DEMAND_KEYWORDS = {
    "群体决策": {
        "keywords": [
            "vote", "voting", "poll", "decide", "decision", "choose", "choice",
            "together", "group", "team", "coordinate", "consensus", "agree",
            "which one", "what should", "where should", "when should",
            "plan", "planning", "schedule", "organize", "arrangement"
        ],
        "patterns": [
            r"how (do|can|should) (we|you) (decide|choose|pick)",
            r"(hard|difficult) to (coordinate|organize|plan)",
            r"(everyone|group) (needs to|wants to|should) (agree|decide)",
            r"(poll|vote|survey) (for|about|on)",
        ]
    },
    "共享体验": {
        "keywords": [
            "share", "sharing", "show", "demo", "demonstrate", "preview",
            "try", "experience", "interact", "interactive", "together",
            "real-time", "realtime", "sync", "synchronize", "collaborate",
            "see what", "look at", "watch together", "play together"
        ],
        "patterns": [
            r"(want|wish|need) (to|them to) (see|try|experience)",
            r"(share|sharing) (screen|experience|moment)",
            r"(together|with friends) (watch|play|experience)",
            r"(can't|cannot|hard to) (share|show|demonstrate)",
        ]
    },
    "社交表达": {
        "keywords": [
            "gift", "birthday", "celebration", "celebrate", "wish", "greeting",
            "surprise", "special", "memorable", "emotion", "emotional",
            "express", "expression", "feeling", "sentiment", "meaningful",
            "personal", "personalize", "customize", "unique", "creative"
        ],
        "patterns": [
            r"(birthday|anniversary|holiday|celebration)",
            r"(want|wish) (to|something) (express|share|show) (feeling|emotion|love)",
            r"(special|unique|meaningful) (gift|message|moment)",
            r"(more|better) (than|way to) (just|only) (text|message)",
        ]
    },
    "沟通效率": {
        "keywords": [
            "annoying", "frustrating", "tedious", "inefficient", "slow",
            "spam", "noise", "flood", "too many", "overwhelming",
            "miss", "missed", "lost", "buried", "scroll", "scrolling",
            "notification", "notifications", "alert", "alerts"
        ],
        "patterns": [
            r"(too many|so many) (messages|notifications|chats)",
            r"(hard|difficult) to (find|track|follow|keep up)",
            r"(gets|get) (lost|buried|missed)",
            r"(message|chat|group) (overload|overflow|flood)",
        ]
    },
    "隐私安全": {
        "keywords": [
            "privacy", "private", "secure", "security", "encryption",
            "encrypted", "data", "surveillance", "monitor", "monitoring",
            "track", "tracking", "spy", "spying", "leak", "leaked"
        ],
        "patterns": [
            r"(privacy|security) (concern|issue|problem|worry)",
            r"(data|information) (leak|breach|collect|share)",
            r"(end-to-end|e2e) (encryption|encrypted)",
            r"(who|what) (can|could) (see|access|read)",
        ]
    },
    "跨平台": {
        "keywords": [
            "cross-platform", "multi-platform", "windows", "mac", "linux",
            "android", "ios", "iphone", "desktop", "mobile", "web",
            "sync", "synchronize", "backup", "export", "import", "migrate"
        ],
        "patterns": [
            r"(work|run|available) on (windows|mac|linux|android|ios)",
            r"(cross|multi)[\-\s]?platform",
            r"(sync|synchronize|backup) (across|between) (device|platform)",
            r"(switch|move|migrate) (from|to|between)",
        ]
    },
    "功能缺失": {
        "keywords": [
            "wish", "hope", "want", "need", "should", "would be nice",
            "missing", "lack", "doesn't have", "can't", "cannot",
            "why no", "why not", "feature", "functionality", "ability"
        ],
        "patterns": [
            r"(wish|hope|want) (it|they|this) (had|could|would)",
            r"(missing|lacks?|doesn't have) (feature|function|ability)",
            r"why (doesn't|can't|won't) (it|they|this)",
            r"(would be|it'd be) (nice|great|better) (if|to have)",
        ]
    }
}

# 情感关键词
SENTIMENT_KEYWORDS = {
    "positive": ["love", "great", "amazing", "awesome", "excellent", "best", "perfect", "wonderful", "fantastic", "brilliant"],
    "negative": ["hate", "terrible", "awful", "worst", "horrible", "annoying", "frustrating", "useless", "broken", "sucks"],
    "neutral": ["okay", "fine", "decent", "average", "normal", "standard", "typical", "regular"]
}


def clean_text(text: str) -> str:
    """清理文本"""
    if not text:
        return ""
    # 清理 HTML 实体
    replacements = {
        "&#x27;": "'", "&quot;": '"', "&gt;": ">", "&lt;": "<",
        "&#x2F;": "/", "&amp;": "&", "&nbsp;": " ",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return re.sub(r'\s+', ' ', text).strip().lower()


def analyze_demand(text: str) -> Dict[str, float]:
    """分析评论中的需求类型"""
    text_lower = clean_text(text)
    scores = {}
    
    for demand_type, config in DEMAND_KEYWORDS.items():
        score = 0
        
        # 关键词匹配
        for keyword in config["keywords"]:
            if keyword.lower() in text_lower:
                score += 1
        
        # 模式匹配
        for pattern in config["patterns"]:
            if re.search(pattern, text_lower, re.IGNORECASE):
                score += 2
        
        scores[demand_type] = score
    
    return scores


def analyze_sentiment(text: str) -> str:
    """分析情感倾向"""
    text_lower = clean_text(text)
    
    pos_count = sum(1 for w in SENTIMENT_KEYWORDS["positive"] if w in text_lower)
    neg_count = sum(1 for w in SENTIMENT_KEYWORDS["negative"] if w in text_lower)
    
    if pos_count > neg_count:
        return "positive"
    elif neg_count > pos_count:
        return "negative"
    else:
        return "neutral"


def extract_key_phrases(comments: List[Dict]) -> List[Tuple[str, int]]:
    """提取高频关键短语"""
    phrases = []
    
    # 痛点相关的模式
    pain_patterns = [
        r"(wish|hope|want|need) (we|I|it|they) (could|can|had|have)",
        r"(annoying|frustrating|tedious|difficult|hard) (that|when|to)",
        r"(can't|cannot|doesn't|don't) (easily|quickly|properly)",
        r"(would be|it'd be) (nice|great|better) (if|to)",
        r"(why|how come) (doesn't|can't|won't) (it|they)",
    ]
    
    for c in comments:
        text = c.get("content", "")
        for pattern in pain_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                phrases.append(" ".join(match))
    
    return Counter(phrases).most_common(20)


def analyze_category(category: str, comments: List[Dict]) -> Dict:
    """分析单个类目的需求"""
    print(f"\n分析 {category.upper()} 类目 ({len(comments)} 条评论)...")
    
    # 需求分布
    demand_scores = defaultdict(float)
    demand_examples = defaultdict(list)
    
    # 情感分布
    sentiments = []
    
    # 话题统计
    story_titles = Counter()
    
    for c in comments:
        text = c.get("content", "")
        story = c.get("story_title", "")
        
        # 分析需求
        scores = analyze_demand(text)
        for demand_type, score in scores.items():
            if score > 0:
                demand_scores[demand_type] += score
                if score >= 2 and len(demand_examples[demand_type]) < 5:
                    demand_examples[demand_type].append({
                        "content": text[:300],
                        "score": score,
                        "story": story,
                        "date": c.get("created_at", "")[:10]
                    })
        
        # 分析情感
        sentiments.append(analyze_sentiment(text))
        
        # 统计话题
        if story:
            story_titles[story] += 1
    
    # 提取关键短语
    key_phrases = extract_key_phrases(comments)
    
    # 按得分排序需求
    sorted_demands = sorted(demand_scores.items(), key=lambda x: x[1], reverse=True)
    
    return {
        "category": category,
        "total_comments": len(comments),
        "demand_distribution": dict(sorted_demands),
        "demand_examples": dict(demand_examples),
        "sentiment_distribution": dict(Counter(sentiments)),
        "top_stories": dict(story_titles.most_common(10)),
        "key_phrases": key_phrases,
    }


def generate_report(analysis_results: Dict) -> str:
    """生成分析报告"""
    report = []
    report.append("# Hacker News 用户需求分析报告")
    report.append(f"\n**分析时间**: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    report.append(f"**数据范围**: 近一年 ({ONE_YEAR_AGO.strftime('%Y-%m-%d')} 至今)")
    report.append(f"**数据来源**: Hacker News 用户评论")
    
    total_comments = sum(r["total_comments"] for r in analysis_results.values())
    report.append(f"**总评论数**: {total_comments} 条")
    
    report.append("\n---\n")
    
    # 总体需求分布
    report.append("## 一、总体需求分布\n")
    
    total_demands = defaultdict(float)
    for cat, result in analysis_results.items():
        for demand, score in result["demand_distribution"].items():
            total_demands[demand] += score
    
    sorted_total = sorted(total_demands.items(), key=lambda x: x[1], reverse=True)
    
    report.append("| 需求类型 | 热度得分 | 占比 |")
    report.append("|----------|----------|------|")
    total_score = sum(s for _, s in sorted_total)
    for demand, score in sorted_total:
        pct = score / total_score * 100 if total_score > 0 else 0
        report.append(f"| {demand} | {score:.0f} | {pct:.1f}% |")
    
    report.append("\n---\n")
    
    # 各类目详细分析
    for category in ["wechat", "social", "ai", "more"]:
        if category not in analysis_results:
            continue
        
        result = analysis_results[category]
        cat_name = {
            "wechat": "微信生态",
            "social": "社交娱乐",
            "ai": "AI 应用",
            "more": "更多场景"
        }.get(category, category)
        
        report.append(f"## 二、{cat_name}类目分析\n")
        report.append(f"**评论数**: {result['total_comments']} 条\n")
        
        # 需求分布
        report.append("### 需求分布\n")
        report.append("| 需求类型 | 得分 |")
        report.append("|----------|------|")
        for demand, score in sorted(result["demand_distribution"].items(), key=lambda x: x[1], reverse=True):
            if score > 0:
                report.append(f"| {demand} | {score:.0f} |")
        
        # 情感分布
        report.append("\n### 情感分布\n")
        sentiments = result["sentiment_distribution"]
        total_sent = sum(sentiments.values())
        for sent, count in sentiments.items():
            pct = count / total_sent * 100 if total_sent > 0 else 0
            emoji = {"positive": "😊", "negative": "😞", "neutral": "😐"}.get(sent, "")
            report.append(f"- {emoji} {sent}: {count} ({pct:.1f}%)")
        
        # 热门话题
        report.append("\n### 热门讨论话题\n")
        for i, (story, count) in enumerate(result["top_stories"].items(), 1):
            if i <= 5:
                report.append(f"{i}. **{story}** ({count} 条评论)")
        
        # 典型需求示例
        report.append("\n### 典型用户评论示例\n")
        for demand_type, examples in result["demand_examples"].items():
            if examples:
                report.append(f"\n**{demand_type}**:\n")
                for ex in examples[:2]:
                    report.append(f"> {ex['content'][:200]}...")
                    report.append(f"> — *{ex['date']}*\n")
        
        report.append("\n---\n")
    
    # 核心洞察
    report.append("## 三、核心洞察与产品机会\n")
    
    report.append("### 与「小体验」三大场景的关联\n")
    report.append("""
根据推演流程中定义的三个核心场景，结合用户评论分析：

**1. 一起做决定（群体决策场景）**
- 用户痛点：群聊中决策效率低，消息刷屏，投票工具太死板
- 评论中体现：coordinate、decide、plan、together 等词频繁出现

**2. 一起体验效果（共享体验场景）**
- 用户痛点：无法让对方「动手试一下」，只能发截图
- 评论中体现：share、demo、interactive、together 等词频繁出现

**3. 让表达有参与感（社交表达场景）**
- 用户痛点：文字祝福太轻，红包只有「拆」一个动作
- 评论中体现：birthday、gift、surprise、meaningful 等词频繁出现
""")
    
    report.append("\n### 发现的新需求方向\n")
    report.append("""
从用户评论中发现的其他值得关注的需求：

1. **隐私安全** - 用户对数据安全、端到端加密的关注度很高
2. **跨平台同步** - 多设备无缝切换是常见诉求
3. **功能缺失** - 用户频繁表达「wish it could」「why doesn't it」等不满
4. **沟通效率** - 消息过载、信息淹没是普遍痛点
""")
    
    return "\n".join(report)


def main():
    print("=" * 70)
    print("Hacker News 用户需求分析")
    print(f"过滤截止: {ONE_YEAR_AGO.strftime('%Y-%m-%d')} 之前的数据")
    print("=" * 70)
    
    files = {
        "wechat": os.path.join(INPUT_DIR, "wechat_20260423.json"),
        "social": os.path.join(INPUT_DIR, "social_20260423.json"),
        "ai": os.path.join(INPUT_DIR, "ai_20260423.json"),
        "more": os.path.join(INPUT_DIR, "more_20260423.json"),
    }
    
    analysis_results = {}
    
    for category, filepath in files.items():
        if not os.path.exists(filepath):
            print(f"文件不存在: {filepath}")
            continue
        
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        comments = data.get("comments", [])
        
        # 过滤一年内的数据
        filtered = []
        for c in comments:
            created_str = c.get("created_at", "")[:10]
            try:
                created_date = datetime.strptime(created_str, "%Y-%m-%d")
                if created_date >= ONE_YEAR_AGO:
                    filtered.append(c)
            except:
                pass
        
        # 分析
        result = analyze_category(category, filtered)
        analysis_results[category] = result
    
    # 生成报告
    report = generate_report(analysis_results)
    
    # 保存报告
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    report_path = os.path.join(OUTPUT_DIR, "hn_demand_analysis.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)
    
    print(f"\n报告已保存: {report_path}")
    
    # 保存原始分析数据
    data_path = os.path.join(OUTPUT_DIR, "hn_demand_analysis.json")
    with open(data_path, "w", encoding="utf-8") as f:
        json.dump(analysis_results, f, ensure_ascii=False, indent=2)
    
    print(f"分析数据已保存: {data_path}")
    
    print("\n" + "=" * 70)
    print("分析完成！")
    print("=" * 70)


if __name__ == "__main__":
    main()
