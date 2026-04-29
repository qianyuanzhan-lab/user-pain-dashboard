#!/usr/bin/env python3
"""
类目级 AI 介入机会分析器

核心逻辑：
1. 读取某类目下所有产品的用户反馈
2. 跨产品聚合，识别类目级共性痛点
3. 筛选出 AI 可介入的未被满足的底层需求
4. 每个需求都有精准溯源：数量统计 + ≥5条原始样本 + 跳转链接

输出数据结构：
{
  "category": "wechat",
  "category_name": "微信生态",
  "analysis_date": "2026-04-23",
  "products_analyzed": ["微信", ...],
  "total_reviews_analyzed": 500,
  "ai_opportunities": [
    {
      "id": "opp_001",
      "title": "智能待办提取",
      "description": "从聊天记录中自动识别待办事项",
      "ai_intervention_type": "轻量介入",  // 或 "重量介入"
      "user_pain_summary": "用户在聊天中讨论的计划、约定容易遗忘",
      "cross_product_relevance": ["社交娱乐", "AI应用"],  // 跨类目共性标签
      "source_stats": {
        "exact_match_count": 47,  // 精准相关数量
        "products_mentioned": ["微信"]
      },
      "evidence_samples": [
        {
          "id": "sample_001",
          "app_name": "微信",
          "author": "用户A",
          "content": "希望微信能出个待办事项功能...",
          "rating": 4,
          "date": "2026-04-21",
          "source_url": "https://apps.apple.com/cn/app/id414478124?see-all=reviews",
          "relevance_note": "直接提出待办需求"
        },
        // ... 至少5条
      ]
    }
  ]
}
"""

import json
import os
from datetime import datetime
from typing import List, Dict, Any

# 类目配置
CATEGORY_CONFIG = {
    "wechat": {
        "name": "微信生态",
        "description": "微信及其小程序、公众号等生态产品",
        "cross_relevance_tags": ["社交娱乐", "AI应用", "更多场景"]
    },
    "social": {
        "name": "社交娱乐",
        "description": "社交、内容、音视频等泛娱乐产品",
        "cross_relevance_tags": ["微信生态", "AI应用", "更多场景"]
    },
    "ai": {
        "name": "AI应用",
        "description": "AI对话、AI工具、AI创作等产品",
        "cross_relevance_tags": ["微信生态", "社交娱乐", "更多场景"]
    },
    "more": {
        "name": "更多场景",
        "description": "效率工具、生活服务等其他场景",
        "cross_relevance_tags": ["微信生态", "社交娱乐", "AI应用"]
    }
}


# ====== LLM Prompt 模板 ======

ANALYSIS_PROMPT_TEMPLATE = '''你是一个产品需求分析专家，专注于发现 AI 可介入的用户需求。

## 任务
分析「{category_name}」类目下的用户反馈数据，识别出 **AI 可以介入解决** 的底层需求。

## 类目信息
- 类目：{category_name}
- 描述：{category_description}
- 涉及产品：{products_list}
- 总评论数：{total_reviews}

## 分析要求

### 1. 识别 AI 介入机会
从用户反馈中找出满足以下条件的需求：
- 用户明确表达了某种未被满足的需求或痛点
- 该需求可以通过 AI 技术（轻量或重量级）来解决或改善
- 该需求具有一定普遍性（跨用户/跨产品出现）

### 2. AI 介入类型判断
- **轻量介入**：AI 作为辅助工具，增强现有功能（如智能推荐、自动分类、内容摘要）
- **重量介入**：AI 作为核心能力，重构用户体验（如 AI 对话、AI 生成、AI 决策）

### 3. 跨类目共性判断
判断该需求是否也是其他类目的共性需求：{cross_relevance_tags}
如果是，标注出来。

### 4. 精准溯源要求（极其重要）
对于每个识别出的 AI 机会，你必须：
- 统计原始数据中**精准相关**的评论数量（不是模糊匹配，是语义强相关）
- 选取 **至少3条** 最能代表该需求的原始评论作为样本
- 每条样本必须包含：原文内容、来源产品、用户名、评分、日期、原始URL
- 解释每条样本为何与该需求强相关

## 输入数据
以下是该类目下收集的用户评论（JSON格式）：

```json
{reviews_json}
```

## 输出格式
请严格按照以下 JSON 格式输出：

```json
{{
  "ai_opportunities": [
    {{
      "id": "opp_001",
      "title": "简洁的机会标题（10字以内）",
      "description": "一句话描述这个 AI 介入机会",
      "ai_intervention_type": "轻量介入 或 重量介入",
      "user_pain_summary": "用户痛点的底层本质是什么",
      "cross_product_relevance": ["如果是其他类目的共性需求，列出类目名"],
      "source_stats": {{
        "exact_match_count": 47,
        "products_mentioned": ["涉及的产品名"]
      }},
      "evidence_samples": [
        {{
          "app_name": "产品名",
          "author": "用户名",
          "content": "原始评论内容（完整保留）",
          "rating": 4,
          "date": "2026-04-21",
          "source_url": "原始URL",
          "relevance_note": "为什么这条评论与该需求强相关"
        }}
      ]
    }}
  ]
}}
```

## 重要提醒
1. 每个机会的 evidence_samples 必须至少有3条，且必须来自原始数据
2. exact_match_count 必须是你在原始数据中实际数出来的数量，不能编造
3. source_url 必须使用原始数据中的 url 字段，不能编造
4. 只输出 AI 有机会介入的需求，普通的 bug 反馈或运营吐槽不算
5. 优先输出高价值、高普遍性的机会
6. 尽可能识别更多细分需求，不要只输出宏观的大需求
'''


def load_category_reviews(category: str, data_dir: str) -> tuple[List[Dict], List[str]]:
    """加载某类目下所有来源的评论数据"""
    all_reviews = []
    products = set()
    
    sources = ['appstore', 'heimao', 'googleplay']
    
    for source in sources:
        source_dir = os.path.join(data_dir, 'raw', source)
        if not os.path.exists(source_dir):
            continue
            
        # 查找该类目的数据文件
        for filename in os.listdir(source_dir):
            if filename.startswith(category) and filename.endswith('.json'):
                filepath = os.path.join(source_dir, filename)
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                # 提取评论
                reviews_key = 'reviews' if 'reviews' in data else 'complaints'
                reviews = data.get(reviews_key, [])
                all_reviews.extend(reviews)
                
                # 提取产品列表
                apps_key = 'apps_crawled' if 'apps_crawled' in data else 'companies_crawled'
                for app in data.get(apps_key, []):
                    products.add(app['name'])
    
    return all_reviews, list(products)


def prepare_prompt(category: str, reviews: List[Dict], products: List[str]) -> str:
    """准备 LLM 分析 Prompt"""
    config = CATEGORY_CONFIG[category]
    
    # 限制评论数量，避免超出 token 限制
    # 优先保留低评分（1-3分）的评论，因为更可能包含真实需求
    low_rating = [r for r in reviews if r.get('rating', 5) <= 3]
    high_rating = [r for r in reviews if r.get('rating', 5) > 3]
    
    # 最多取 200 条低分 + 50 条高分
    selected_reviews = low_rating[:200] + high_rating[:50]
    
    # 简化评论数据，只保留必要字段
    simplified_reviews = []
    for r in selected_reviews:
        simplified_reviews.append({
            'app_name': r.get('app_name', ''),
            'author': r.get('author', ''),
            'rating': r.get('rating', 0),
            'title': r.get('title', ''),
            'content': r.get('content', ''),
            'date': r.get('date', ''),
            'url': r.get('url', '')
        })
    
    prompt = ANALYSIS_PROMPT_TEMPLATE.format(
        category_name=config['name'],
        category_description=config['description'],
        products_list='、'.join(products),
        total_reviews=len(reviews),
        cross_relevance_tags='、'.join(config['cross_relevance_tags']),
        reviews_json=json.dumps(simplified_reviews, ensure_ascii=False, indent=2)
    )
    
    return prompt


def save_analysis_result(category: str, result: Dict, output_dir: str):
    """保存分析结果"""
    config = CATEGORY_CONFIG[category]
    
    output = {
        'category': category,
        'category_name': config['name'],
        'analysis_date': datetime.now().strftime('%Y-%m-%d'),
        'products_analyzed': result.get('products', []),
        'total_reviews_analyzed': result.get('total_reviews', 0),
        'ai_opportunities': result.get('ai_opportunities', [])
    }
    
    # 为每个机会生成唯一 ID
    for i, opp in enumerate(output['ai_opportunities']):
        opp['id'] = f"{category}_opp_{i+1:03d}"
        # 为每个样本生成唯一 ID
        for j, sample in enumerate(opp.get('evidence_samples', [])):
            sample['id'] = f"{opp['id']}_sample_{j+1:03d}"
    
    output_path = os.path.join(output_dir, f'{category}_ai_opportunities.json')
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 分析结果已保存: {output_path}")
    return output_path


def main():
    """主流程"""
    import argparse
    
    parser = argparse.ArgumentParser(description='类目级 AI 介入机会分析')
    parser.add_argument('--category', required=True, choices=list(CATEGORY_CONFIG.keys()),
                        help='要分析的类目')
    parser.add_argument('--data-dir', default='./data',
                        help='数据目录路径')
    parser.add_argument('--output-dir', default='./data/processed',
                        help='输出目录路径')
    parser.add_argument('--print-prompt', action='store_true',
                        help='只打印 Prompt，不执行分析')
    
    args = parser.parse_args()
    
    # 加载数据
    print(f"📂 加载 {args.category} 类目数据...")
    reviews, products = load_category_reviews(args.category, args.data_dir)
    print(f"   - 产品数: {len(products)}")
    print(f"   - 评论数: {len(reviews)}")
    
    if not reviews:
        print("❌ 未找到评论数据")
        return
    
    # 准备 Prompt
    prompt = prepare_prompt(args.category, reviews, products)
    
    if args.print_prompt:
        print("\n" + "="*60)
        print("生成的 Prompt:")
        print("="*60)
        print(prompt)
        return
    
    # TODO: 调用 LLM API 进行分析
    # 这里需要集成实际的 LLM 调用逻辑
    print("\n⚠️ 请将上述 Prompt 发送给 LLM，获取分析结果后保存")
    print(f"   Prompt 长度: {len(prompt)} 字符")
    
    # 保存 Prompt 到文件，方便手动执行
    prompt_path = os.path.join(args.output_dir, f'{args.category}_analysis_prompt.txt')
    os.makedirs(args.output_dir, exist_ok=True)
    with open(prompt_path, 'w', encoding='utf-8') as f:
        f.write(prompt)
    print(f"   Prompt 已保存: {prompt_path}")


if __name__ == '__main__':
    main()
