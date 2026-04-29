#!/usr/bin/env python3
"""
将 V3 版需求点数据转换为 Dashboard 兼容的 JSON 格式 - 修正版V2
样本格式是两行：
  [1] ★☆☆☆☆ (1星)
      「内容...」
"""
import json
import re
from datetime import datetime

# 数据来源配置
DATA_SOURCE = {
    "platform": "App Store",
    "app": "微信"
}

def parse_v3_file():
    """解析 V3 格式的需求点文本"""
    with open('data/processed/demand_points_with_samples_v3.txt', 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    demands = []
    current_category = None
    current_demand = None
    current_samples = []
    pending_sample_rating = None
    
    for i, line in enumerate(lines):
        line_stripped = line.strip()
        
        # 检测分类
        if '【功能需求】' in line:
            current_category = 'feature'
        elif '【问题反馈】' in line:
            current_category = 'issue'
        elif '【平台策略】' in line:
            current_category = 'policy'
        
        # 检测新需求点开始
        demand_match = re.match(r'^#(\d+)\s+(.+)$', line_stripped)
        if demand_match:
            # 保存上一个需求点
            if current_demand:
                current_demand['samples'] = current_samples
                demands.append(current_demand)
            
            demand_id = int(demand_match.group(1))
            title = demand_match.group(2).strip()
            current_demand = {
                "id": demand_id,
                "title": title,
                "category": current_category,
                "mentionCount": 0,
                "aiScore": 0,
                "aiKeywords": []
            }
            current_samples = []
            pending_sample_rating = None
            continue
        
        # 检测提及数和AI分数
        stats_match = re.match(r'^\s*提及:\s*(\d+)条\s*\|\s*AI介入分:\s*(\d+)/10\s*\|\s*(.+)$', line_stripped)
        if stats_match and current_demand:
            current_demand['mentionCount'] = int(stats_match.group(1))
            current_demand['aiScore'] = int(stats_match.group(2))
            current_demand['aiKeywords'] = [kw.strip() for kw in stats_match.group(3).split('、')]
            continue
        
        # 检测样本标题行: [1] ★☆☆☆☆ (1星)
        sample_header = re.match(r'^\s*\[(\d+)\]\s*([★☆]+)\s*\((\d+)星\)\s*$', line_stripped)
        if sample_header:
            pending_sample_rating = int(sample_header.group(3))
            continue
        
        # 检测样本内容行: 「...」
        if pending_sample_rating is not None and line_stripped.startswith('「') and '」' in line_stripped:
            content = line_stripped[1:]  # 去掉开头的「
            if content.endswith('」'):
                content = content[:-1]  # 去掉结尾的」
            current_samples.append({
                "rating": pending_sample_rating,
                "snippet": content
            })
            pending_sample_rating = None
            continue
    
    # 别忘了最后一个需求点
    if current_demand:
        current_demand['samples'] = current_samples
        demands.append(current_demand)
    
    return demands

def convert_to_dashboard_format(demands):
    """转换为 Dashboard 兼容格式"""
    # 分类映射
    category_map = {
        'feature': {'label': '功能需求', 'sentiment': 'negative'},
        'issue': {'label': '问题反馈', 'sentiment': 'negative'},
        'policy': {'label': '平台策略', 'sentiment': 'mixed'}
    }
    
    dashboard_needs = []
    
    for d in demands:
        cat_info = category_map.get(d['category'], {'label': '其他', 'sentiment': 'mixed'})
        
        # 构建 references
        references = []
        for idx, sample in enumerate(d.get('samples', [])):
            references.append({
                "id": f"wechat_sample_{d['id']}_{idx + 1}",
                "source": f"App Store - {DATA_SOURCE['app']}",
                "product": DATA_SOURCE['app'],
                "snippet": sample['snippet'],
                "rating": sample['rating'],
                "author": "",
                "date": "",
                "url": "https://apps.apple.com/cn/app/微信/id414478124?see-all=reviews"
            })
        
        # 选取用户原声（第一条样本的内容）
        user_voice = ""
        if references:
            first_snippet = references[0]['snippet']
            if len(first_snippet) > 120:
                user_voice = first_snippet[:117] + "..."
            else:
                user_voice = first_snippet
        
        need = {
            "id": f"wechat_demand_{d['id']}",
            "title": d['title'],
            "description": f"用户反馈：{d['mentionCount']}条 | AI介入评分：{d['aiScore']}/10",
            "userVoice": user_voice,
            "keywords": d.get('aiKeywords', [])[:4],
            "sentiment": cat_info['sentiment'],
            "priority": get_priority(d['mentionCount'], d['aiScore']),
            "category": "wechat",
            "subcategory": cat_info['label'],
            "apps": ["微信"],
            "mentionCount": d['mentionCount'],
            "mentionSources": [
                {"source": "App Store", "count": d['mentionCount']}
            ],
            "references": references,
            "aiSolution": get_ai_solution(d),
            "aiDescription": f"基于 {d['mentionCount']} 条用户反馈，AI介入可行性评分 {d['aiScore']}/10",
            "aiKeywords": d.get('aiKeywords', [])
        }
        
        dashboard_needs.append(need)
    
    return dashboard_needs

def get_priority(mention_count, ai_score):
    """根据提及数和AI分数计算优先级"""
    if mention_count >= 20 and ai_score >= 7:
        return "P0"
    elif mention_count >= 10 or ai_score >= 6:
        return "P1"
    elif mention_count >= 5:
        return "P2"
    else:
        return "P3"

def get_ai_solution(demand):
    """生成AI方案描述"""
    keywords = demand.get('aiKeywords', [])
    if keywords:
        return f"AI方向：{', '.join(keywords[:3])}"
    return ""

def main():
    print("=" * 60)
    print("微信生态需求数据转换 - V2")
    print("=" * 60)
    
    # 1. 解析 V3 需求点
    print("\n[1/2] 解析 V3 需求点数据...")
    demands = parse_v3_file()
    print(f"    解析到 {len(demands)} 个需求点")
    
    # 统计样本
    total_samples = sum(len(d.get('samples', [])) for d in demands)
    print(f"    共计 {total_samples} 条样本")
    
    # 显示前3个需求点的样本数
    for d in demands[:3]:
        print(f"      #{d['id']} {d['title'][:20]}... - {len(d.get('samples', []))} 条样本")
    
    # 2. 转换格式
    print("\n[2/2] 转换为 Dashboard 格式...")
    dashboard_needs = convert_to_dashboard_format(demands)
    
    # 输出统计
    print("\n" + "=" * 60)
    print("转换完成")
    print("=" * 60)
    
    by_subcategory = {}
    for n in dashboard_needs:
        sub = n['subcategory']
        by_subcategory[sub] = by_subcategory.get(sub, 0) + 1
    
    for sub, count in by_subcategory.items():
        print(f"  {sub}: {count} 个")
    
    # 检查样本完整性
    needs_with_refs = sum(1 for n in dashboard_needs if len(n['references']) > 0)
    print(f"\n  有样本的需求点: {needs_with_refs}/{len(dashboard_needs)}")
    
    # 保存 JSON
    output = {
        "lastUpdated": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "source": "App Store - 微信",
        "totalNeeds": len(dashboard_needs),
        "needs": dashboard_needs
    }
    
    output_path = "data/processed/wechat_demands_dashboard.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    print(f"\n已保存到: {output_path}")
    
    # 生成 TypeScript 数据文件
    generate_ts_data(dashboard_needs)

def generate_ts_data(needs):
    """生成 TypeScript 数据文件"""
    ts_content = '''// 微信生态需求数据 - 自动生成
// 生成时间: ''' + datetime.now().strftime("%Y-%m-%d %H:%M") + '''

import { UserNeed } from '../types';

export const WECHAT_DEMANDS: UserNeed[] = ''' + json.dumps(needs, ensure_ascii=False, indent=2) + ''';

export const WECHAT_STATS = {
  totalNeeds: ''' + str(len(needs)) + ''',
  byCategory: {
    feature: ''' + str(len([n for n in needs if n['subcategory'] == '功能需求'])) + ''',
    issue: ''' + str(len([n for n in needs if n['subcategory'] == '问题反馈'])) + ''',
    policy: ''' + str(len([n for n in needs if n['subcategory'] == '平台策略'])) + '''
  },
  lastUpdated: "''' + datetime.now().strftime("%Y-%m-%d %H:%M") + '''"
};
'''
    
    ts_path = "src/data/wechatDemands.ts"
    with open(ts_path, 'w', encoding='utf-8') as f:
        f.write(ts_content)
    
    print(f"已生成 TypeScript 数据: {ts_path}")

if __name__ == "__main__":
    main()
