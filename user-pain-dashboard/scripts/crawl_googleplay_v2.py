#!/usr/bin/env python3
"""
Google Play 评论采集器 V2
使用多种免费方案采集评论
"""

import json
import time
import os
import subprocess
import sys
from datetime import datetime
from typing import List, Dict, Any, Optional

# 配置
CONFIG = {
    'output_dir': '../data/raw/googleplay',
    'delay_seconds': 2,
}

# 应用包名
CATEGORY_APPS = {
    'wechat': [
        {'name': '微信', 'package': 'com.tencent.mm'},
    ],
    'social': [
        {'name': 'Soul', 'package': 'me.soul.android'},
        {'name': '探探', 'package': 'com.p1.mobile.putong'},
        {'name': '陌陌', 'package': 'com.immomo.momo'},
        {'name': '即刻', 'package': 'com.ruguoapp.jike'},
    ],
    'ai': [
        {'name': 'ChatGPT', 'package': 'com.openai.chatgpt'},
        {'name': 'Kimi', 'package': 'com.moonshot.kimichat'},
        {'name': '豆包', 'package': 'com.larus.nova'},
        {'name': 'Character.AI', 'package': 'ai.character.app'},
        {'name': 'Claude', 'package': 'com.anthropic.claude'},
    ],
    'more': [
        {'name': '飞书', 'package': 'com.ss.android.lark'},
        {'name': '钉钉', 'package': 'com.alibaba.android.rimet'},
        {'name': '企业微信', 'package': 'com.tencent.wework'},
    ],
}


def install_scraper():
    """安装 google-play-scraper"""
    try:
        import google_play_scraper
        return True
    except ImportError:
        print("安装 google-play-scraper...")
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 
                              'google-play-scraper', '-q'])
        return True


def fetch_reviews_with_scraper(package: str, app_name: str, count: int = 200) -> List[Dict]:
    """使用 google-play-scraper 库获取评论"""
    try:
        from google_play_scraper import reviews, Sort
        
        result, _ = reviews(
            package,
            lang='zh',
            country='cn',
            sort=Sort.NEWEST,
            count=count,
        )
        
        parsed = []
        for r in result:
            parsed.append({
                'app_name': app_name,
                'package': package,
                'author': r.get('userName', ''),
                'rating': r.get('score', 0),
                'title': '',
                'content': r.get('content', ''),
                'date': r.get('at').isoformat() if r.get('at') else '',
                'thumbs_up': r.get('thumbsUpCount', 0),
                'source': 'Google Play',
                'source_id': 'googleplay',
                'url': f'https://play.google.com/store/apps/details?id={package}',
            })
        return parsed
    except Exception as e:
        print(f"  Scraper error: {e}")
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
        
        reviews = fetch_reviews_with_scraper(package, app_name, count=300)
        
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
        'source': 'Google Play',
        'source_id': 'googleplay',
        'apps_crawled': apps_crawled,
        'total_reviews': len(all_reviews),
        'reviews': all_reviews,
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
    # 先安装依赖
    install_scraper()
    
    target_categories = categories or list(CATEGORY_APPS.keys())

    print("=" * 60)
    print("Google Play 评论采集器 V2")
    print(f"目标类目: {', '.join(target_categories)}")
    print("=" * 60)

    results = {}
    total_all = 0

    for cat_id in target_categories:
        data = crawl_category(cat_id)
        filepath = save_results(cat_id, data)
        results[cat_id] = {
            'file': filepath,
            'total': data['total_reviews'],
        }
        total_all += data['total_reviews']

    print("\n" + "=" * 60)
    print("采集完成汇总:")
    for cat_id, info in results.items():
        print(f"  {cat_id}: {info['total']} 条评论")
    print(f"\n总计: {total_all} 条")
    print("=" * 60)

    return results


if __name__ == '__main__':
    import sys
    categories = sys.argv[1:] if len(sys.argv) > 1 else None
    main(categories)
