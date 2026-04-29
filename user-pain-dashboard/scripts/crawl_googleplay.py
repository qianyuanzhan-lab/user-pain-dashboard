#!/usr/bin/env python3
"""
Google Play 评论采集器
数据源：Google Play 公开页面
"""

import json
import time
import os
import urllib.request
import urllib.error
import re
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

# 采集配置
CONFIG = {
    'output_dir': '../data/raw/googleplay',
    'delay_seconds': 3,  # 请求间隔（比 App Store 更保守）
    'time_range_days': 365,
}

# Google Play 包名配置
CATEGORY_APPS = {
    'wechat': [
        {'name': '微信', 'package': 'com.tencent.mm'},
    ],
    'social': [
        {'name': 'Soul', 'package': 'me.soul.android'},
        {'name': '探探', 'package': 'com.p1.mobile.putong'},
        {'name': '陌陌', 'package': 'com.immomo.momo'},
        {'name': '小宇宙', 'package': 'com.jimu.xiaoyuzhou'},
        {'name': '即刻', 'package': 'com.ruguoapp.jike'},
    ],
    'ai': [
        {'name': 'ChatGPT', 'package': 'com.openai.chatgpt'},
        {'name': 'Kimi', 'package': 'com.moonshot.kimi'},
        {'name': '豆包', 'package': 'com.bytedance.doubao'},
        {'name': 'Character.AI', 'package': 'ai.character.app'},
    ],
    'more': [
        {'name': '作业帮', 'package': 'com.baidu.homework'},
        {'name': '飞书', 'package': 'com.ss.android.lark'},
        {'name': '钉钉', 'package': 'com.alibaba.android.rimet'},
    ],
}


def fetch_googleplay_reviews_serpapi(package: str, app_name: str) -> List[Dict]:
    """
    通过 SerpAPI 获取 Google Play 评论（如果有 API key）
    这是最可靠的方式，但需要付费
    """
    # 如果没有 API key，返回空
    api_key = os.environ.get('SERPAPI_KEY')
    if not api_key:
        return []
    
    url = f'https://serpapi.com/search?engine=google_play_product&product_id={package}&reviews=true&api_key={api_key}'
    
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=30) as response:
            data = json.loads(response.read().decode('utf-8'))
        
        reviews = []
        for r in data.get('reviews', []):
            reviews.append({
                'app_name': app_name,
                'package': package,
                'author': r.get('author', ''),
                'rating': r.get('rating', 0),
                'title': r.get('title', ''),
                'content': r.get('snippet', ''),
                'date': r.get('date', ''),
                'source': 'Google Play',
                'url': f'https://play.google.com/store/apps/details?id={package}',
            })
        return reviews
    except Exception as e:
        print(f"  SerpAPI Error: {e}")
        return []


def fetch_googleplay_basic(package: str, app_name: str) -> List[Dict]:
    """
    基础方式：直接从 Google Play 页面获取评论
    注意：Google Play 有反爬机制，成功率不高
    """
    url = f'https://play.google.com/store/apps/details?id={package}&hl=zh&gl=cn'
    
    try:
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Accept-Language': 'zh-CN,zh;q=0.9',
        })
        with urllib.request.urlopen(req, timeout=30) as response:
            html = response.read().decode('utf-8')
        
        # 简单解析评论（这只是示例，实际 Google Play 用 JS 动态加载）
        # 真实场景需要用 Selenium 或付费 API
        reviews = []
        
        # 提取评分
        rating_match = re.search(r'"([\d.]+)"\s*星', html)
        if rating_match:
            print(f"  发现评分: {rating_match.group(1)}")
        
        return reviews
        
    except Exception as e:
        print(f"  Error: {e}")
        return []


def crawl_category(category_id: str) -> Dict[str, Any]:
    """采集单个类目"""
    
    print(f"\n{'='*50}")
    print(f"Google Play 采集: {category_id}")
    print(f"{'='*50}")
    
    if category_id not in CATEGORY_APPS:
        return {'category': category_id, 'reviews': [], 'error': 'Unknown category'}
    
    all_reviews = []
    apps_crawled = []
    
    for app in CATEGORY_APPS[category_id]:
        app_name = app['name']
        package = app['package']
        
        print(f"\n📱 采集 {app_name} ({package})")
        
        # 优先尝试 SerpAPI
        reviews = fetch_googleplay_serpapi(package, app_name)
        
        if not reviews:
            # 回退到基础方式
            print("  尝试基础方式...")
            reviews = fetch_googleplay_basic(package, app_name)
        
        all_reviews.extend(reviews)
        apps_crawled.append({
            'name': app_name,
            'package': package,
            'review_count': len(reviews),
        })
        
        print(f"  ✓ {app_name}: {len(reviews)} 条评论")
        time.sleep(CONFIG['delay_seconds'])
    
    return {
        'category': category_id,
        'crawl_date': datetime.now().isoformat(),
        'apps_crawled': apps_crawled,
        'total_reviews': len(all_reviews),
        'reviews': all_reviews,
        'note': 'Google Play 需要 SerpAPI key 或 Selenium 才能获取完整评论',
    }


def save_results(category_id: str, data: Dict):
    """保存结果"""
    output_dir = os.path.join(os.path.dirname(__file__), CONFIG['output_dir'])
    os.makedirs(output_dir, exist_ok=True)
    
    filename = f"{category_id}_{datetime.now().strftime('%Y%m%d')}.json"
    filepath = os.path.join(output_dir, filename)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 保存到: {filepath}")
    return filepath


def main(categories: Optional[List[str]] = None):
    """主函数"""
    target_categories = categories or list(CATEGORY_APPS.keys())
    
    print("=" * 60)
    print("Google Play 评论采集器")
    print(f"目标类目: {', '.join(target_categories)}")
    print("=" * 60)
    print("\n⚠️ 注意: Google Play 完整采集需要 SERPAPI_KEY 环境变量")
    
    results = {}
    
    for cat_id in target_categories:
        data = crawl_category(cat_id)
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
