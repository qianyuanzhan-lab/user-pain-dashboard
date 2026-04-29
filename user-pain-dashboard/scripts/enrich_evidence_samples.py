#!/usr/bin/env python3
"""
补充样本的完整信息（作者、日期、跳转链接等）
从原始评论数据中匹配并补全 evidence_samples 的字段
"""

import json
import os
from typing import Dict, List, Optional
from datetime import datetime


def load_raw_reviews(data_dir: str, category: str) -> List[Dict]:
    """加载某个类目的所有原始评论"""
    all_reviews = []
    
    # App Store 数据
    appstore_files = [
        f'data/raw/appstore/{category}_20260423.json',
        f'data/raw/appstore/wechat_20260423.json',  # 微信生态
    ]
    
    for file_path in appstore_files:
        full_path = os.path.join(data_dir, '..', file_path)
        if os.path.exists(full_path):
            try:
                with open(full_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    reviews = data.get('reviews', [])
                    all_reviews.extend(reviews)
                    print(f"    从 {file_path} 加载 {len(reviews)} 条评论")
            except Exception as e:
                print(f"    ⚠️ 加载 {file_path} 失败: {e}")
    
    # Google Play 数据
    gplay_path = os.path.join(data_dir, '..', f'data/raw/googleplay/{category}_20260424.json')
    if os.path.exists(gplay_path):
        try:
            with open(gplay_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                reviews = data.get('reviews', [])
                all_reviews.extend(reviews)
                print(f"    从 Google Play 加载 {len(reviews)} 条评论")
        except Exception as e:
            print(f"    ⚠️ 加载 Google Play 数据失败: {e}")
    
    # Hacker News 数据
    hn_path = os.path.join(data_dir, '..', f'data/raw/hackernews/{category}_20260423.json')
    if os.path.exists(hn_path):
        try:
            with open(hn_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                comments = data.get('comments', [])
                all_reviews.extend(comments)
                print(f"    从 Hacker News 加载 {len(comments)} 条评论")
        except Exception as e:
            print(f"    ⚠️ 加载 Hacker News 数据失败: {e}")
    
    # 黑猫投诉数据
    heimao_files = [
        f'data/raw/heimao/{category}_20260423.json',
        f'data/raw/heimao/{category}_20260424.json',
    ]
    for file_path in heimao_files:
        full_path = os.path.join(data_dir, '..', file_path)
        if os.path.exists(full_path):
            try:
                with open(full_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    complaints = data.get('complaints', [])
                    all_reviews.extend(complaints)
                    print(f"    从 {file_path} 加载 {len(complaints)} 条投诉")
            except Exception as e:
                pass
    
    return all_reviews


def build_review_index(reviews: List[Dict]) -> Dict[str, Dict]:
    """构建评论内容到完整评论的索引"""
    index = {}
    
    for review in reviews:
        # 评论内容可能在不同字段
        content = review.get('content') or review.get('text') or ''
        if not content:
            continue
        
        # 用前 50 个字符作为 key（去除空白）
        key = content.strip().replace('\n', ' ')[:50]
        
        if key and key not in index:
            index[key] = review
    
    return index


def find_matching_review(sample_text: str, review_index: Dict[str, Dict]) -> Optional[Dict]:
    """根据样本文本查找匹配的原始评论"""
    if not sample_text:
        return None
    
    # 清理文本
    clean_text = sample_text.strip().replace('\n', ' ')
    
    # 精确匹配（前50字符）
    key = clean_text[:50]
    if key in review_index:
        return review_index[key]
    
    # 模糊匹配（找包含关系）
    for idx_key, review in review_index.items():
        if idx_key in clean_text or clean_text[:30] in idx_key:
            return review
    
    return None


def format_date(date_str: str) -> str:
    """格式化日期为 YYYY-MM-DD 格式"""
    if not date_str:
        return ''
    
    try:
        # 尝试解析 ISO 格式
        if 'T' in date_str:
            dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            return dt.strftime('%Y-%m-%d')
        # 尝试其他格式
        for fmt in ['%Y-%m-%d', '%Y/%m/%d', '%d/%m/%Y']:
            try:
                dt = datetime.strptime(date_str[:10], fmt)
                return dt.strftime('%Y-%m-%d')
            except:
                pass
    except:
        pass
    
    return date_str[:10] if len(date_str) >= 10 else date_str


def generate_source_url(review: Dict) -> str:
    """生成跳转链接"""
    # 优先使用原始 URL
    if review.get('url'):
        return review['url']
    
    source = review.get('source', '')
    app_id = review.get('app_id', '')
    
    # App Store
    if 'App Store' in source or app_id:
        if app_id:
            return f"https://apps.apple.com/cn/app/id{app_id}?see-all=reviews"
        return ''
    
    # Google Play
    if 'Google Play' in source:
        package = review.get('package_name', '')
        if package:
            return f"https://play.google.com/store/apps/details?id={package}&showAllReviews=true"
        return ''
    
    # Hacker News
    if 'Hacker News' in source:
        item_id = review.get('id') or review.get('item_id')
        if item_id:
            return f"https://news.ycombinator.com/item?id={item_id}"
        return ''
    
    # 黑猫投诉
    if '黑猫' in source:
        complaint_id = review.get('id') or review.get('complaint_id')
        if complaint_id:
            return f"https://tousu.sina.com.cn/complaint/view/{complaint_id}/"
        return ''
    
    return ''


def enrich_sample(sample: Dict, review_index: Dict[str, Dict]) -> Dict:
    """补充单个样本的完整信息"""
    # 获取原始文本
    text = sample.get('original_text') or sample.get('content') or ''
    
    # 查找匹配的原始评论
    review = find_matching_review(text, review_index)
    
    if review:
        # 补充字段
        return {
            **sample,
            'content': review.get('content') or review.get('text') or text,
            'app_name': review.get('app_name') or sample.get('app_name', ''),
            'author': review.get('author') or sample.get('author', '匿名用户'),
            'date': format_date(review.get('date', '')),
            'rating': review.get('rating') or sample.get('rating'),
            'source_url': generate_source_url(review),
            'source': sample.get('source', review.get('source', '')),
        }
    else:
        # 无法匹配，使用默认值
        source = sample.get('source', '')
        app_name = ''
        if ' - ' in source:
            _, app_name = source.split(' - ', 1)
        
        return {
            **sample,
            'content': text,
            'app_name': app_name,
            'author': '用户',
            'date': '',
            'rating': sample.get('sentiment_score', 0.5) * 5 if sample.get('sentiment_score') else None,
            'source_url': '',
        }


def enrich_category(category: str, data_dir: str):
    """补充某个类目的样本信息"""
    print(f"\n📂 处理类目: {category}")
    
    # 加载原始评论并建立索引
    reviews = load_raw_reviews(data_dir, category)
    if not reviews:
        print(f"  ⚠️ 无原始评论数据")
        return
    
    print(f"  📊 共加载 {len(reviews)} 条原始评论")
    review_index = build_review_index(reviews)
    print(f"  🔍 建立索引，共 {len(review_index)} 条唯一评论")
    
    # 加载 consolidated 数据
    input_path = os.path.join(data_dir, 'processed', f'{category}_ai_opportunities_consolidated.json')
    if not os.path.exists(input_path):
        print(f"  ⚠️ 文件不存在: {input_path}")
        return
    
    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 补充每个需求的样本信息
    opportunities = data.get('ai_opportunities', [])
    enriched_count = 0
    total_samples = 0
    matched_samples = 0
    
    for opp in opportunities:
        samples = opp.get('evidence_samples', [])
        enriched_samples = []
        
        for sample in samples:
            total_samples += 1
            enriched = enrich_sample(sample, review_index)
            enriched_samples.append(enriched)
            
            # 统计匹配成功率
            if enriched.get('author') and enriched['author'] != '用户':
                matched_samples += 1
        
        opp['evidence_samples'] = enriched_samples
        if enriched_samples:
            enriched_count += 1
    
    # 保存更新后的数据
    with open(input_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    match_rate = (matched_samples / total_samples * 100) if total_samples > 0 else 0
    print(f"  ✅ 补充了 {enriched_count} 个需求的样本，匹配率: {match_rate:.1f}% ({matched_samples}/{total_samples})")


def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(script_dir, '..', 'data')
    
    print("=" * 60)
    print("补充样本的完整信息（作者、日期、跳转链接）")
    print("=" * 60)
    
    for category in ['wechat', 'social', 'ai', 'more']:
        enrich_category(category, data_dir)
    
    print("\n" + "=" * 60)
    print("✅ 全部完成！")
    print("=" * 60)


if __name__ == '__main__':
    main()
