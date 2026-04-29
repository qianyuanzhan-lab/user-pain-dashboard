#!/usr/bin/env python3
"""
App Store 评论采集器
数据源：Apple 官方 RSS Feed（完全安全合规）
"""

import json
import time
import os
import urllib.request
import urllib.error
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

# 采集配置
CONFIG = {
    'output_dir': '../data/raw/appstore',
    'delay_seconds': 2,  # 请求间隔
    'max_pages': 10,     # 每个 App 最多采集页数
    'time_range_days': 365,  # 采集近 1 年
}

# 类目关键词配置（用于泛化检索）
CATEGORY_KEYWORDS = {
    'wechat': {
        'apps': [
            {'name': '微信', 'id': '414478124'},
        ],
        'search_terms': ['微信', 'WeChat'],
    },
    'social': {
        'apps': [
            # 社交/社区
            {'name': 'Soul', 'id': '1032287195'},
            {'name': '探探', 'id': '861891048'},
            {'name': '陌陌', 'id': '448165862'},
            {'name': '即刻', 'id': '1483536498'},
            {'name': '小红书', 'id': '741292507'},
            {'name': '微博', 'id': '350962117'},
            # 播客/音频
            {'name': '小宇宙', 'id': '1488894313'},
            {'name': '喜马拉雅', 'id': '876336838'},
            # 知识社区
            {'name': '知乎', 'id': '432274380'},
        ],
        'search_terms': ['社交', '交友', '社区', '播客', '知识分享'],
    },
    'ai': {
        'apps': [
            # 通用 AI 助手
            {'name': 'Kimi', 'id': '6474233312'},
            {'name': '豆包', 'id': '6459478672'},
            {'name': 'DeepSeek', 'id': '6737597349'},
            {'name': '通义千问', 'id': '6466733523'},
            {'name': '元宝', 'id': '6480446430'},
            {'name': '文心一言', 'id': '6447073600'},
            # AI 创作
            {'name': '妙鸭相机', 'id': '6450646823'},
            {'name': '醒图', 'id': '1454744064'},
            # AI 翻译/学习
            {'name': '有道翻译官', 'id': '1537247947'},
            {'name': '网易有道词典', 'id': '353115739'},
        ],
        'search_terms': ['AI助手', 'AI对话', 'AI绘画', 'AI翻译', 'AI学习'],
    },
    'more': {
        'apps': [
            # 办公协作
            {'name': '飞书', 'id': '1440246959'},
            {'name': '钉钉', 'id': '930368978'},
            {'name': '腾讯会议', 'id': '1484048379'},
            {'name': '企业微信', 'id': '1087897068'},
            # 效率工具
            {'name': '滴答清单', 'id': '626144601'},
            {'name': '印象笔记', 'id': '1356054761'},
            {'name': '石墨文档', 'id': '1107227378'},
            # 教育
            {'name': '作业帮', 'id': '907890637'},
            {'name': '有道精品课', 'id': '1447447996'},
            # 医疗健康
            {'name': '好大夫', 'id': '393715498'},
            {'name': '丁香医生', 'id': '507608618'},
            {'name': '微医', 'id': '642624698'},
        ],
        'search_terms': ['办公', '效率', '教育', '医疗', '协作'],
    },
}


def fetch_appstore_reviews(app_id: str, app_name: str, country: str = 'cn', page: int = 1) -> List[Dict]:
    """
    通过 App Store RSS Feed 获取评论
    官方接口，完全安全
    """
    url = f'https://itunes.apple.com/{country}/rss/customerreviews/page={page}/id={app_id}/sortby=mostrecent/json'
    
    try:
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })
        with urllib.request.urlopen(req, timeout=30) as response:
            data = json.loads(response.read().decode('utf-8'))
        
        entries = data.get('feed', {}).get('entry', [])
        if not entries:
            return []
        
        # 第一个 entry 通常是 App 信息，跳过
        reviews = []
        for entry in entries:
            if 'im:rating' not in entry:
                continue
            
            review = {
                'app_id': app_id,
                'app_name': app_name,
                'author': entry.get('author', {}).get('name', {}).get('label', ''),
                'rating': int(entry.get('im:rating', {}).get('label', 0)),
                'title': entry.get('title', {}).get('label', ''),
                'content': entry.get('content', {}).get('label', ''),
                'version': entry.get('im:version', {}).get('label', ''),
                'date': entry.get('updated', {}).get('label', ''),
                'source': 'App Store',
                'url': f'https://apps.apple.com/{country}/app/id{app_id}?see-all=reviews',
            }
            reviews.append(review)
        
        return reviews
        
    except urllib.error.HTTPError as e:
        print(f"  HTTP Error {e.code} for {app_name}")
        return []
    except Exception as e:
        print(f"  Error fetching {app_name}: {e}")
        return []


def crawl_category(category_id: str, category_config: Dict) -> Dict[str, Any]:
    """采集单个类目的所有 App 评论"""
    
    print(f"\n{'='*50}")
    print(f"采集类目: {category_id}")
    print(f"{'='*50}")
    
    all_reviews = []
    apps_crawled = []
    cutoff_date = datetime.now() - timedelta(days=CONFIG['time_range_days'])
    
    for app in category_config['apps']:
        app_name = app['name']
        app_id = app['id']
        
        print(f"\n📱 采集 {app_name} (ID: {app_id})")
        app_reviews = []
        
        for page in range(1, CONFIG['max_pages'] + 1):
            print(f"  页码 {page}...", end=' ')
            reviews = fetch_appstore_reviews(app_id, app_name, page=page)
            
            if not reviews:
                print("无数据")
                break
            
            # 过滤近 1 年的评论
            filtered = []
            for r in reviews:
                try:
                    review_date = datetime.fromisoformat(r['date'].replace('Z', '+00:00'))
                    if review_date.replace(tzinfo=None) >= cutoff_date:
                        filtered.append(r)
                except:
                    filtered.append(r)  # 日期解析失败也保留
            
            app_reviews.extend(filtered)
            print(f"获取 {len(filtered)} 条")
            
            time.sleep(CONFIG['delay_seconds'])
        
        all_reviews.extend(app_reviews)
        apps_crawled.append({
            'name': app_name,
            'id': app_id,
            'review_count': len(app_reviews),
        })
        print(f"  ✓ {app_name} 共 {len(app_reviews)} 条评论")
    
    return {
        'category': category_id,
        'crawl_date': datetime.now().isoformat(),
        'apps_crawled': apps_crawled,
        'total_reviews': len(all_reviews),
        'reviews': all_reviews,
    }


def save_results(category_id: str, data: Dict):
    """保存采集结果"""
    output_dir = os.path.join(os.path.dirname(__file__), CONFIG['output_dir'])
    os.makedirs(output_dir, exist_ok=True)
    
    filename = f"{category_id}_{datetime.now().strftime('%Y%m%d')}.json"
    filepath = os.path.join(output_dir, filename)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 保存到: {filepath}")
    return filepath


def main(categories: Optional[List[str]] = None):
    """
    主函数
    categories: 要采集的类目列表，None 表示全部
    """
    target_categories = categories or list(CATEGORY_KEYWORDS.keys())
    
    print("=" * 60)
    print("App Store 评论采集器")
    print(f"目标类目: {', '.join(target_categories)}")
    print(f"时间范围: 近 {CONFIG['time_range_days']} 天")
    print("=" * 60)
    
    results = {}
    
    for cat_id in target_categories:
        if cat_id not in CATEGORY_KEYWORDS:
            print(f"⚠️ 未知类目: {cat_id}")
            continue
        
        data = crawl_category(cat_id, CATEGORY_KEYWORDS[cat_id])
        filepath = save_results(cat_id, data)
        results[cat_id] = {
            'file': filepath,
            'total': data['total_reviews'],
        }
    
    print("\n" + "=" * 60)
    print("采集完成汇总:")
    for cat_id, info in results.items():
        print(f"  {cat_id}: {info['total']} 条评论")
    print("=" * 60)
    
    return results


if __name__ == '__main__':
    import sys
    categories = sys.argv[1:] if len(sys.argv) > 1 else None
    main(categories)
