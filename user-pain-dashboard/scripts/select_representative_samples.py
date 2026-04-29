#!/usr/bin/env python3
"""
从原始评论数据中选取代表性样本的工具
选取标准：
1. 时间分散：覆盖近一年，避免集中在近一周
2. 语气客观：避免脏话、情绪化表达
3. 信息量足：内容长度适中，有具体描述
"""

import json
import os
import re
from datetime import datetime, timedelta
from collections import defaultdict

# 情绪化/不文明词汇过滤列表（真正的脏话和人身攻击）
OFFENSIVE_PATTERNS = [
    r'傻[逼比bB]', r'妈的', r'尼玛', r'sb', r'傻叉', r'操你',
    r'日你', r'去死', r'脑残', r'智障', r'滚蛋', 
    r'fuck', r'shit', r'damn', r'tmd', r'cnm',
    r'弱智', r'废物', r'蠢', r'贱', r'恶心死',
]

# 高度情绪化表达（允许出现一次，但多次出现则过滤）
EMOTIONAL_PATTERNS = [
    r'垃圾', r'辣鸡', r'差评', r'骗子', r'坑爹', r'坑人', r'恶心',
    r'无语', r'呵呵', r'服了', r'醉了', r'吐了', r'烦死', r'气死',
    r'！{3,}', r'？{3,}', r'\.{5,}',  # 过多的标点
]

def is_civil_tone(content: str) -> bool:
    """检查评论是否语气相对文明（允许描述问题的词，但过滤人身攻击和极端情绪化）"""
    content_lower = content.lower()
    
    # 硬性过滤：脏话和人身攻击
    for pattern in OFFENSIVE_PATTERNS:
        if re.search(pattern, content_lower):
            return False
    
    # 软性过滤：情绪化表达过多
    emotional_count = 0
    for pattern in EMOTIONAL_PATTERNS:
        matches = re.findall(pattern, content_lower)
        emotional_count += len(matches)
    
    # 如果情绪化表达超过 2 次，认为过于情绪化
    if emotional_count > 2:
        return False
    
    # 检查是否全是泄愤（无实质内容）
    if len(content) < 30 and emotional_count > 0:
        return False
    
    return True

def has_information_value(content: str) -> bool:
    """检查评论是否有信息价值"""
    # 长度适中
    if len(content) < 30 or len(content) > 300:
        return False
    # 不能全是标点/特殊字符
    text_only = re.sub(r'[^\u4e00-\u9fa5a-zA-Z0-9]', '', content)
    if len(text_only) < 20:
        return False
    # 不能是纯重复字符
    if len(set(content)) < 10:
        return False
    return True

def parse_date(date_str: str) -> datetime:
    """解析日期字符串，返回 naive datetime"""
    try:
        # 格式: 2026-04-16T11:51:07-07:00
        dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        # 转为 naive datetime（去掉时区信息）
        return dt.replace(tzinfo=None)
    except:
        return None

def is_strongly_relevant(content: str, keywords: list) -> bool:
    """
    检查评论是否与关键词强相关
    强相关定义：
    1. 至少匹配 2 个不同关键词，或
    2. 关键词在内容中出现多次，或
    3. 内容详细描述了该问题（长度 > 50 且包含关键词）
    """
    content_lower = content.lower()
    
    # 统计匹配的关键词数量
    matched_keywords = []
    total_matches = 0
    for kw in keywords:
        kw_lower = kw.lower()
        count = content_lower.count(kw_lower)
        if count > 0:
            matched_keywords.append(kw)
            total_matches += count
    
    # 强相关条件
    # 1. 匹配 2 个以上不同关键词
    if len(matched_keywords) >= 2:
        return True
    
    # 2. 同一关键词出现多次（说明在强调这个问题）
    if total_matches >= 2:
        return True
    
    # 3. 内容较长且包含关键词（有详细描述）
    if len(content) >= 60 and len(matched_keywords) >= 1:
        return True
    
    return False

def select_representative_samples(
    reviews: list,
    keywords: list,
    max_samples: int = 5,
    target_date: datetime = None,
    year_range: int = 1
) -> list:
    """
    从评论列表中选取代表性样本
    
    Args:
        reviews: 原始评论列表
        keywords: 关键词列表，用于筛选相关评论
        max_samples: 最大样本数
        target_date: 目标日期（通常是今天），用于计算时间范围
        year_range: 时间范围（年）
        
    Returns:
        选中的样本列表
    """
    if target_date is None:
        target_date = datetime(2026, 4, 23)  # 默认数据采集日期
    
    # 计算时间边界
    start_date = target_date - timedelta(days=year_range * 365)
    
    # 第一步：筛选强相关且语气客观的评论
    relevant_reviews = []
    for r in reviews:
        content = r.get('content', '')
        
        # 检查强相关性（不只是简单的关键词匹配）
        if keywords and not is_strongly_relevant(content, keywords):
            continue
        
        # 检查日期范围
        date = parse_date(r.get('date', ''))
        if date is None or date < start_date or date > target_date:
            continue
        
        # 检查语气（无脏话、不过度情绪化）
        if not is_civil_tone(content):
            continue
        
        # 检查信息量
        if not has_information_value(content):
            continue
        
        relevant_reviews.append(r)
    
    if not relevant_reviews:
        return []
    
    # 第二步：时间分散选取
    # 将一年分成 max_samples 个时间段，每段选一条
    time_span = (target_date - start_date).days
    segment_days = time_span // max_samples
    
    selected = []
    used_apps = set()  # 避免同一 App 过多
    used_reviews = set()  # 避免重复选取
    
    # 按时间段分组
    segments_data = []
    for i in range(max_samples):
        segment_start = start_date + timedelta(days=i * segment_days)
        segment_end = start_date + timedelta(days=(i + 1) * segment_days)
        
        segment_reviews = [
            r for r in relevant_reviews
            if segment_start <= parse_date(r.get('date', '')) < segment_end
        ]
        segments_data.append({
            'start': segment_start,
            'end': segment_end,
            'reviews': segment_reviews
        })
    
    # 第一轮：每个时间段选一条
    for seg in segments_data:
        if not seg['reviews']:
            continue
        
        # 优先选择不同 App 的评论
        for r in seg['reviews']:
            r_id = r.get('id', r.get('content', '')[:50])
            if r_id in used_reviews:
                continue
            app = r.get('app_name', '')
            if app not in used_apps:
                selected.append(r)
                used_apps.add(app)
                used_reviews.add(r_id)
                break
        else:
            # 所有 App 都用过，选第一条未用过的
            for r in seg['reviews']:
                r_id = r.get('id', r.get('content', '')[:50])
                if r_id not in used_reviews:
                    selected.append(r)
                    used_reviews.add(r_id)
                    break
    
    # 第二轮：如果还不够，从剩余评论中补充（优先选不同 App）
    if len(selected) < max_samples:
        remaining = [r for r in relevant_reviews if r.get('id', r.get('content', '')[:50]) not in used_reviews]
        # 按日期排序，时间分散
        remaining.sort(key=lambda x: parse_date(x.get('date', '')) or datetime.min)
        
        # 均匀抽取
        step = max(1, len(remaining) // (max_samples - len(selected)))
        for i in range(0, len(remaining), step):
            if len(selected) >= max_samples:
                break
            r = remaining[i]
            app = r.get('app_name', '')
            # 优先不同 App
            if app not in used_apps or len(selected) >= max_samples - 1:
                selected.append(r)
                used_apps.add(app)
    
    return selected[:max_samples]

def load_raw_reviews(data_dir: str, category: str) -> list:
    """加载某个类目的原始评论数据"""
    reviews = []
    raw_dir = os.path.join(data_dir, 'raw', 'appstore')
    
    # 根据类目选择对应的数据文件
    files = {
        'wechat': ['wechat_20260423.json'],
        'social': ['social_20260423.json'],
        'ai': ['ai_20260423.json'],
        'more': ['more_20260423.json'],
    }
    
    for filename in files.get(category, []):
        filepath = os.path.join(raw_dir, filename)
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # 数据结构是 { "reviews": [...] }
                if isinstance(data, dict) and 'reviews' in data:
                    reviews.extend(data['reviews'])
                elif isinstance(data, list):
                    reviews.extend(data)
    
    return reviews

def search_reviews_by_topic(reviews: list, topic_keywords: list, exclude_keywords: list = None) -> list:
    """按主题关键词搜索评论"""
    results = []
    for r in reviews:
        content = r.get('content', '').lower()
        # 检查是否匹配任一关键词
        if any(kw.lower() in content for kw in topic_keywords):
            # 检查排除词
            if exclude_keywords and any(ex.lower() in content for ex in exclude_keywords):
                continue
            results.append(r)
    return results

def main():
    """测试脚本"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(script_dir, '..', 'data')
    
    # 加载社交类目数据
    reviews = load_raw_reviews(data_dir, 'social')
    print(f"加载了 {len(reviews)} 条社交类目评论")
    
    # 测试：搜索"诈骗"相关评论
    fraud_keywords = ['诈骗', '骗子', '酒托', '婚托', '杀猪盘', '骗钱', '上当']
    fraud_reviews = search_reviews_by_topic(reviews, fraud_keywords)
    print(f"找到 {len(fraud_reviews)} 条诈骗相关评论")
    
    # 选取代表性样本
    samples = select_representative_samples(
        reviews=fraud_reviews,
        keywords=fraud_keywords,
        max_samples=5
    )
    
    print(f"\n选出 {len(samples)} 条代表性样本：")
    for s in samples:
        date = parse_date(s.get('date', '')).strftime('%Y-%m-%d') if parse_date(s.get('date', '')) else '未知'
        print(f"\n[{s.get('app_name')}] [{date}] [{s.get('rating')}星]")
        print(f"  {s.get('content')[:100]}...")

if __name__ == '__main__':
    main()
