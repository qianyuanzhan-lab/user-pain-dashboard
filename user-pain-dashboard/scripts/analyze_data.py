#!/usr/bin/env python3
"""
数据分析与痛点聚类器
从采集的原始数据中提炼痛点主题
"""

import json
import os
import re
from datetime import datetime
from typing import List, Dict, Any, Optional
from collections import Counter

# 配置
CONFIG = {
    'raw_data_dir': '../data/raw',
    'output_dir': '../data/processed',
    'min_cluster_size': 3,  # 至少 3 条评论才算一个痛点
}

# 痛点关键词库（用于聚类）
PAIN_KEYWORDS = {
    'wechat': {
        '多设备登录': ['两台手机', '多设备', '双手机', '登录', '切换设备', '同时登录'],
        '聊天记录备份': ['聊天记录', '备份', '迁移', '换手机', '云同步', '恢复'],
        '撤回时间': ['撤回', '2分钟', '时间太短', '来不及'],
        '朋友圈画质': ['画质', '压缩', '糊', '图片质量', '朋友圈'],
        '群消息管理': ['群消息', '太多', '漏看', '重要', '免打扰'],
        '朋友圈编辑': ['编辑', '修改', '错别字', '重发'],
        '已读状态': ['已读', '看没看', '回复'],
    },
    'social': {
        '匿名骚扰': ['骚扰', '匿名', '不当内容', '举报', '安全'],
        '虚假账号': ['机器人', '假', '营销号', '真人认证', '虚假'],
        '匹配精准度': ['匹配', '不准', '没有共同', '算法'],
        '播客发现': ['播客', '推荐', '找不到', '发现'],
        '语音破冰': ['语音', '冷场', '尴尬', '话题', '破冰'],
        '社区融入': ['新人', '融入', '圈子', '门槛'],
        'AI身份': ['AI', '机器人', '不是真人', '身份'],
    },
    'ai': {
        '上下文记忆': ['忘记', '上下文', '记忆', '前面说的', '长对话'],
        '回答准确性': ['错误', '编造', '幻觉', '不准确', '胡说'],
        '搜索时效性': ['过时', '时效', '最新', '实时', '旧的'],
        '风格一致性': ['风格', '不一样', '统一', '系列'],
        '物理效果': ['物理', '不自然', '奇怪', '走路', '视频'],
        '情感真实感': ['空虚', '不理解', '情感', '陪伴', '孤独'],
        '代码质量': ['代码', '报错', '运行', 'bug', '编程'],
    },
    'more': {
        '解题准确率': ['答案错', '正确率', '解题', '错误'],
        '问诊可靠性': ['诊断', '医生', '问诊', '不准'],
        '会议纪要': ['会议', '纪要', '漏掉', '要点'],
        '跨设备同步': ['同步', '延迟', '冲突', '设备'],
        '合同审查': ['合同', '条款', '漏掉', '法律'],
        '版权问题': ['版权', '商用', '侵权', '授权'],
    },
}


def load_raw_data(category_id: str) -> List[Dict]:
    """加载某个类目的原始数据"""
    raw_dir = os.path.join(os.path.dirname(__file__), CONFIG['raw_data_dir'])
    all_data = []
    
    # 遍历所有数据源目录
    for source in ['appstore', 'googleplay', 'heimao']:
        source_dir = os.path.join(raw_dir, source)
        if not os.path.exists(source_dir):
            continue
        
        for filename in os.listdir(source_dir):
            if filename.startswith(category_id) and filename.endswith('.json'):
                filepath = os.path.join(source_dir, filename)
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # 提取评论/投诉
                items = data.get('reviews', []) or data.get('complaints', [])
                for item in items:
                    item['source_file'] = filename
                all_data.extend(items)
    
    return all_data


def classify_pain_point(text: str, category_id: str) -> Optional[str]:
    """根据文本内容分类到痛点"""
    if category_id not in PAIN_KEYWORDS:
        return None
    
    text_lower = text.lower()
    
    for pain_name, keywords in PAIN_KEYWORDS[category_id].items():
        for kw in keywords:
            if kw.lower() in text_lower:
                return pain_name
    
    return None


def cluster_reviews(reviews: List[Dict], category_id: str) -> Dict[str, List[Dict]]:
    """将评论聚类到痛点"""
    clusters = {}
    
    for review in reviews:
        # 合并标题和内容
        text = f"{review.get('title', '')} {review.get('content', '')} {review.get('snippet', '')}"
        
        pain_point = classify_pain_point(text, category_id)
        if pain_point:
            if pain_point not in clusters:
                clusters[pain_point] = []
            clusters[pain_point].append(review)
    
    # 过滤太小的聚类
    return {k: v for k, v in clusters.items() if len(v) >= CONFIG['min_cluster_size']}


def generate_pain_summary(pain_name: str, reviews: List[Dict]) -> Dict:
    """生成单个痛点的摘要"""
    
    # 统计来源
    sources = Counter(r.get('source', 'Unknown') for r in reviews)
    
    # 提取代表性评论
    representative = []
    seen_content = set()
    for r in reviews[:10]:
        content = r.get('content', '') or r.get('snippet', '')
        if content and content not in seen_content:
            seen_content.add(content)
            representative.append({
                'snippet': content[:200],
                'source': r.get('source', ''),
                'url': r.get('url', ''),
                'date': r.get('date', ''),
            })
        if len(representative) >= 5:
            break
    
    # 提取涉及的 App
    apps = list(set(r.get('app_name', '') or r.get('company', '') for r in reviews if r.get('app_name') or r.get('company')))
    
    return {
        'pain_name': pain_name,
        'mention_count': len(reviews),
        'sources': dict(sources),
        'apps': apps[:10],
        'representative_reviews': representative,
    }


def analyze_category(category_id: str) -> Dict:
    """分析单个类目"""
    print(f"\n分析类目: {category_id}")
    print("-" * 40)
    
    # 加载数据
    reviews = load_raw_data(category_id)
    print(f"  加载 {len(reviews)} 条原始数据")
    
    if not reviews:
        return {
            'category': category_id,
            'error': '无数据',
            'pain_points': [],
        }
    
    # 聚类
    clusters = cluster_reviews(reviews, category_id)
    print(f"  识别 {len(clusters)} 个痛点主题")
    
    # 生成摘要
    pain_points = []
    for pain_name, cluster_reviews in sorted(clusters.items(), key=lambda x: -len(x[1])):
        summary = generate_pain_summary(pain_name, cluster_reviews)
        pain_points.append(summary)
        print(f"    - {pain_name}: {summary['mention_count']} 条")
    
    return {
        'category': category_id,
        'analysis_date': datetime.now().isoformat(),
        'total_reviews_analyzed': len(reviews),
        'pain_points_found': len(pain_points),
        'pain_points': pain_points,
    }


def save_analysis(category_id: str, data: Dict):
    """保存分析结果"""
    output_dir = os.path.join(os.path.dirname(__file__), CONFIG['output_dir'])
    os.makedirs(output_dir, exist_ok=True)
    
    filename = f"{category_id}_analysis_{datetime.now().strftime('%Y%m%d')}.json"
    filepath = os.path.join(output_dir, filename)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"  保存到: {filepath}")
    return filepath


def main(categories: Optional[List[str]] = None):
    """主函数"""
    target_categories = categories or ['wechat', 'social', 'ai', 'more']
    
    print("=" * 60)
    print("痛点分析与聚类器")
    print("=" * 60)
    
    results = {}
    
    for cat_id in target_categories:
        analysis = analyze_category(cat_id)
        filepath = save_analysis(cat_id, analysis)
        results[cat_id] = {
            'file': filepath,
            'pain_points': analysis['pain_points_found'],
        }
    
    print("\n" + "=" * 60)
    print("分析完成汇总:")
    for cat_id, info in results.items():
        print(f"  {cat_id}: {info['pain_points']} 个痛点")
    print("=" * 60)
    
    return results


if __name__ == '__main__':
    import sys
    categories = sys.argv[1:] if len(sys.argv) > 1 else None
    main(categories)
