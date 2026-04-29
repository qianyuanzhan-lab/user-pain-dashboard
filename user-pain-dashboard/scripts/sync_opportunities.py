#!/usr/bin/env python3
"""
同步产品需求数据到前端 TypeScript 文件
"""

import json
import os
import re
from datetime import datetime

def sanitize_text(text: str) -> str:
    """清理文本，确保可以安全嵌入 JS 单引号字符串"""
    if not text:
        return ''
    # 移除换行符
    text = text.replace('\n', ' ').replace('\r', ' ')
    # 转义单引号
    text = text.replace("'", "\\'")
    # 转义反斜杠
    text = text.replace("\\", "\\\\")
    # 移除可能导致问题的特殊字符（emoji 等）
    # 只保留基本的 Unicode 字符
    cleaned = []
    for char in text:
        code = ord(char)
        # 保留基本拉丁、中文、日文、韩文、标点符号
        if code < 0x10000 and (
            code < 0x1F600 or code > 0x1F64F  # 排除表情符号
        ):
            cleaned.append(char)
    return ''.join(cleaned).strip()


def main():
    base_dir = os.path.dirname(__file__)
    data_path = os.path.join(base_dir, '..', 'data', 'processed', 'product_opportunities_v2.json')
    ts_path = os.path.join(base_dir, '..', 'src', 'data', 'dashboardData.ts')
    
    print("=" * 60)
    print("同步产品需求数据到前端")
    print("=" * 60)
    
    # 读取数据
    with open(data_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    opportunities = data['opportunities']
    print(f"📊 加载 {len(opportunities)} 个产品机会")
    
    # 生成 TypeScript 代码
    ts_items = []
    for opp in opportunities:
        # 构建 AI 机会数组
        ai_opps = []
        for ai in opp['ai_opportunities']:
            ai_type = sanitize_text(ai['type'])
            ai_desc = sanitize_text(ai['desc'])
            ai_opps.append(f"""{{
      type: '{ai_type}',
      desc: '{ai_desc}',
    }}""")
        
        # 构建数据源对象
        sources_parts = []
        for src, count in opp['data_sources'].items():
            sources_parts.append(f"'{src}': {count}")
        
        # 构建用户声音数组
        voices = []
        for v in opp.get('user_voices', [])[:3]:
            escaped = sanitize_text(v[:80])
            voices.append(f"'{escaped}'")
        
        # 构建样本数组
        samples = []
        for s in opp.get('evidence_samples', [])[:5]:
            text_escaped = sanitize_text(s['text'][:100])
            source_escaped = sanitize_text(s['source'])
            app_escaped = sanitize_text(s.get('app', ''))
            samples.append(f"""{{
      text: '{text_escaped}',
      source: '{source_escaped}',
      app: '{app_escaped}',
      sentiment: '{s.get('sentiment', 'neutral')}',
    }}""")
        
        title_escaped = sanitize_text(opp['title'])
        desc_escaped = sanitize_text(opp['description'])
        
        ts_item = f"""  {{
    id: '{opp['id']}',
    scenarioId: '{opp['scenario_id']}',
    title: '{title_escaped}',
    description: '{desc_escaped}',
    priority: '{opp['priority']}',
    productValue: '{opp['product_value']}',
    mentionCount: {opp['mention_count']},
    avgRating: {opp['avg_rating']},
    userVoices: [{', '.join(voices)}],
    aiOpportunities: [
    {','.join(ai_opps)}
    ],
    dataSources: {{ {', '.join(sources_parts)} }},
    evidenceSamples: [
    {','.join(samples)}
    ],
  }}"""
        ts_items.append(ts_item)
    
    ts_array = f"""// 产品需求机会（自动生成于 {datetime.now().strftime('%Y-%m-%d %H:%M')}）
export const PRODUCT_OPPORTUNITIES = [
{','.join(ts_items)}
];

export const OPPORTUNITIES_META = {{
  generatedAt: '{data['generated_at']}',
  totalReviewsAnalyzed: {data['total_reviews_analyzed']},
  scenariosIdentified: {data['scenarios_identified']},
}};
"""
    
    # 读取现有 TS 文件
    with open(ts_path, 'r', encoding='utf-8') as f:
        ts_content = f.read()
    
    # 查找或添加 PRODUCT_OPPORTUNITIES
    pattern = r'// 产品需求机会.*?export const OPPORTUNITIES_META = \{[^}]+\};'
    if re.search(pattern, ts_content, re.DOTALL):
        ts_content = re.sub(pattern, ts_array.strip(), ts_content, flags=re.DOTALL)
        print("✓ 已替换现有 PRODUCT_OPPORTUNITIES")
    else:
        # 添加到文件末尾
        ts_content = ts_content.rstrip() + '\n\n' + ts_array
        print("✓ 已添加 PRODUCT_OPPORTUNITIES")
    
    # 写回文件
    with open(ts_path, 'w', encoding='utf-8') as f:
        f.write(ts_content)
    
    print(f"💾 已更新: {ts_path}")
    print("=" * 60)


if __name__ == '__main__':
    main()
