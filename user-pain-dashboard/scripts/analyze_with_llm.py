#!/usr/bin/env python3
"""
用户痛点 AI 分析脚本
用途：读取采集的评论数据，调用 LLM 按"AI 介入机会"维度分析输出

使用方法：
    python3 analyze_with_llm.py [--category wechat|social|ai|more|all] [--output json|markdown]
    
环境变量：
    DEEPSEEK_API_KEY: DeepSeek API 密钥（默认使用 DeepSeek）
    OPENAI_API_KEY: OpenAI API 密钥（可选）
    
示例：
    export DEEPSEEK_API_KEY="sk-xxx"
    python3 analyze_with_llm.py --category all --output markdown
"""

import json
import os
import sys
import argparse
from pathlib import Path
from datetime import datetime

# ============================================
# Prompt 模板
# ============================================

ANALYSIS_PROMPT_TEMPLATE = """
你是一个产品需求分析师，擅长从用户负面反馈中挖掘"AI 可介入解决"的产品机会。

## 你的任务

分析以下用户评论数据，找出 **AI 能介入解决的需求机会**。

## 分析维度

1. **只关注 AI 能解决的问题**
   - 信息过载 → AI 摘要/整理
   - 重复劳动 → AI 自动化
   - 理解困难 → AI 解释/翻译
   - 发现困难 → AI 推荐/搜索
   - 创作门槛 → AI 辅助创作
   - 沟通障碍 → AI 翻译/润色
   - 决策困难 → AI 分析/建议

2. **忽略以下问题**（非 AI 能解决）
   - 封号/违规处罚
   - 付费/退款纠纷
   - App 崩溃/闪退
   - 广告过多
   - 客服态度差

## 输出格式

请严格按以下 JSON 格式输出：

```json
{{
  "opportunities": [
    {{
      "id": "opp-1",
      "title": "机会名称（10字以内）",
      "painPoint": "用户痛点描述（30字以内）",
      "aiSolution": "AI 如何解决（50字以内）",
      "priority": "P0/P1/P2",
      "sourceApps": ["App1", "App2"],
      "typicalQuotes": ["典型用户评论1", "典型用户评论2"],
      "keywords": ["关键词1", "关键词2"]
    }}
  ],
  "summary": {{
    "totalReviews": 123,
    "lowRatingCount": 45,
    "topOpportunity": "最大机会点",
    "insight": "核心洞察（100字以内）"
  }}
}}
```

## 优先级定义

- **P0**: 高频刚需，AI 已有成熟方案，可快速落地
- **P1**: 有明确需求，AI 有能力解决，需要一定开发
- **P2**: 需求存在，AI 是可选方案之一

## 数据来源

类目：{category}
评论数量：{review_count} 条
低分评论（1-3星）：{low_rating_count} 条
数据日期：{date}

## 用户评论

{reviews_text}
"""

# ============================================
# 数据加载
# ============================================

def load_reviews(category: str, data_dir: Path) -> dict:
    """加载指定类目的评论数据"""
    file_path = data_dir / f"{category}_20260423.json"
    if not file_path.exists():
        print(f"⚠️ 文件不存在: {file_path}")
        return {"reviews": [], "apps_crawled": []}
    
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)

def prepare_reviews_text(reviews: list, max_reviews: int = 100) -> str:
    """将评论整理成文本，供 LLM 分析"""
    # 优先取低分评论
    low_reviews = [r for r in reviews if r.get("rating", 5) <= 3]
    # 过滤太短的
    low_reviews = [r for r in low_reviews if len(r.get("content", "")) >= 20]
    # 取前 max_reviews 条
    sampled = low_reviews[:max_reviews]
    
    lines = []
    for r in sampled:
        app = r.get("app_name", "未知")
        rating = r.get("rating", "?")
        content = r.get("content", "").replace("\n", " ")[:150]
        lines.append(f"[{app}][{rating}星] {content}")
    
    return "\n".join(lines)

# ============================================
# LLM 调用
# ============================================

def call_deepseek(prompt: str, api_key: str) -> str:
    """调用 DeepSeek API"""
    try:
        from openai import OpenAI
    except ImportError:
        print("❌ 请先安装 openai 库: pip install openai")
        sys.exit(1)
    
    client = OpenAI(
        api_key=api_key,
        base_url="https://api.deepseek.com"
    )
    
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": "你是一个专业的产品需求分析师。请严格按照用户要求的 JSON 格式输出。"},
            {"role": "user", "content": prompt}
        ],
        temperature=0.3,
        max_tokens=4000
    )
    
    return response.choices[0].message.content

def call_openai(prompt: str, api_key: str) -> str:
    """调用 OpenAI API（备用）"""
    try:
        from openai import OpenAI
    except ImportError:
        print("❌ 请先安装 openai 库: pip install openai")
        sys.exit(1)
    
    client = OpenAI(api_key=api_key)
    
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "你是一个专业的产品需求分析师。请严格按照用户要求的 JSON 格式输出。"},
            {"role": "user", "content": prompt}
        ],
        temperature=0.3,
        max_tokens=4000
    )
    
    return response.choices[0].message.content

# ============================================
# 分析主流程
# ============================================

def analyze_category(category: str, data_dir: Path, api_key: str, provider: str = "deepseek") -> dict:
    """分析单个类目"""
    print(f"\n📊 分析类目: {category}")
    
    # 加载数据
    data = load_reviews(category, data_dir)
    reviews = data.get("reviews", [])
    
    if not reviews:
        print(f"  ⚠️ 无评论数据")
        return {}
    
    low_reviews = [r for r in reviews if r.get("rating", 5) <= 3]
    
    print(f"  📝 评论总数: {len(reviews)}")
    print(f"  📉 低分评论: {len(low_reviews)}")
    
    # 准备 prompt
    reviews_text = prepare_reviews_text(reviews, max_reviews=100)
    prompt = ANALYSIS_PROMPT_TEMPLATE.format(
        category=category,
        review_count=len(reviews),
        low_rating_count=len(low_reviews),
        date=datetime.now().strftime("%Y-%m-%d"),
        reviews_text=reviews_text
    )
    
    # 调用 LLM
    print(f"  🤖 调用 {provider} 分析中...")
    
    if provider == "deepseek":
        result_text = call_deepseek(prompt, api_key)
    else:
        result_text = call_openai(prompt, api_key)
    
    # 解析 JSON
    try:
        # 提取 JSON 部分
        if "```json" in result_text:
            json_str = result_text.split("```json")[1].split("```")[0]
        elif "```" in result_text:
            json_str = result_text.split("```")[1].split("```")[0]
        else:
            json_str = result_text
        
        result = json.loads(json_str.strip())
        result["category"] = category
        print(f"  ✅ 分析完成，发现 {len(result.get('opportunities', []))} 个机会点")
        return result
    
    except json.JSONDecodeError as e:
        print(f"  ❌ JSON 解析失败: {e}")
        print(f"  原始输出: {result_text[:500]}...")
        return {"category": category, "error": str(e), "raw": result_text}

def analyze_all(data_dir: Path, api_key: str, provider: str = "deepseek") -> list:
    """分析所有类目"""
    categories = ["wechat", "social", "ai", "more"]
    results = []
    
    for cat in categories:
        result = analyze_category(cat, data_dir, api_key, provider)
        if result:
            results.append(result)
    
    return results

# ============================================
# 输出格式化
# ============================================

def to_markdown(results: list) -> str:
    """将分析结果转换为 Markdown"""
    lines = [
        "# AI 介入机会分析报告",
        "",
        f"> 生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "> 数据来源：App Store 用户评论",
        "",
    ]
    
    for result in results:
        category = result.get("category", "未知")
        opportunities = result.get("opportunities", [])
        summary = result.get("summary", {})
        
        lines.append(f"## {category.upper()} 类目")
        lines.append("")
        
        if summary:
            lines.append(f"**核心洞察**：{summary.get('insight', '-')}")
            lines.append("")
        
        for i, opp in enumerate(opportunities, 1):
            lines.append(f"### {i}. {opp.get('title', '未命名')} [{opp.get('priority', 'P2')}]")
            lines.append("")
            lines.append(f"**痛点**：{opp.get('painPoint', '-')}")
            lines.append("")
            lines.append(f"**AI 解决方案**：{opp.get('aiSolution', '-')}")
            lines.append("")
            
            quotes = opp.get("typicalQuotes", [])
            if quotes:
                lines.append("**典型评论**：")
                for q in quotes[:2]:
                    lines.append(f'- "{q}"')
                lines.append("")
            
            lines.append("---")
            lines.append("")
    
    return "\n".join(lines)

# ============================================
# CLI 入口
# ============================================

def main():
    parser = argparse.ArgumentParser(description="用户痛点 AI 分析脚本")
    parser.add_argument("--category", default="all", help="类目: wechat/social/ai/more/all")
    parser.add_argument("--output", default="markdown", help="输出格式: json/markdown")
    parser.add_argument("--provider", default="deepseek", help="LLM 提供商: deepseek/openai")
    args = parser.parse_args()
    
    # 获取 API Key
    if args.provider == "deepseek":
        api_key = os.getenv("DEEPSEEK_API_KEY")
        if not api_key:
            print("❌ 请设置环境变量 DEEPSEEK_API_KEY")
            sys.exit(1)
    else:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            print("❌ 请设置环境变量 OPENAI_API_KEY")
            sys.exit(1)
    
    # 数据目录
    script_dir = Path(__file__).parent
    data_dir = script_dir.parent / "data" / "raw" / "appstore"
    
    if not data_dir.exists():
        print(f"❌ 数据目录不存在: {data_dir}")
        sys.exit(1)
    
    # 执行分析
    print("🚀 开始 AI 痛点分析")
    print(f"   数据目录: {data_dir}")
    print(f"   LLM 提供商: {args.provider}")
    
    if args.category == "all":
        results = analyze_all(data_dir, api_key, args.provider)
    else:
        result = analyze_category(args.category, data_dir, api_key, args.provider)
        results = [result] if result else []
    
    # 输出结果
    output_dir = script_dir.parent / "data" / "processed"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    if args.output == "json":
        output_file = output_dir / f"ai_analysis_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
    else:
        output_file = output_dir / f"ai_analysis_{datetime.now().strftime('%Y%m%d_%H%M')}.md"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(to_markdown(results))
    
    print(f"\n✅ 分析完成，结果已保存到: {output_file}")

if __name__ == "__main__":
    main()
