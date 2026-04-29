#!/usr/bin/env python3
"""
Google Play 评论采集器（使用 google-play-scraper）
直接抓取，无需 API key
"""

import json
import time
import os
import subprocess
import sys
from datetime import datetime
from typing import List, Dict, Any, Optional

# 采集配置
CONFIG = {
    'output_dir': '../data/raw/googleplay',
    'reviews_per_app': 200,  # 每个 App 采集评论数
    'delay_seconds': 2,
}

# Google Play 包名配置（按类目）
CATEGORY_APPS = {
    'wechat': [
        {'name': 'WeChat', 'package': 'com.tencent.mm'},
    ],
    'social': [
        # 社交/约会
        {'name': 'Tinder', 'package': 'com.tinder'},
        {'name': 'Bumble', 'package': 'com.bumble.app'},
        {'name': 'Hinge', 'package': 'co.hinge.app'},
        # 通讯
        {'name': 'Telegram', 'package': 'org.telegram.messenger'},
        {'name': 'Discord', 'package': 'com.discord'},
        {'name': 'Signal', 'package': 'org.thoughtcrime.securesms'},
        # 社区
        {'name': 'Reddit', 'package': 'com.reddit.frontpage'},
        {'name': 'Twitter/X', 'package': 'com.twitter.android'},
    ],
    'ai': [
        {'name': 'ChatGPT', 'package': 'com.openai.chatgpt'},
        {'name': 'Gemini', 'package': 'com.google.android.apps.bard'},
        {'name': 'Microsoft Copilot', 'package': 'com.microsoft.copilot'},
        {'name': 'Perplexity', 'package': 'ai.perplexity.app.android'},
        {'name': 'Character.AI', 'package': 'ai.character.app'},
        {'name': 'Replika', 'package': 'ai.replika.app'},
    ],
    'more': [
        # 办公
        {'name': 'Slack', 'package': 'com.Slack'},
        {'name': 'Zoom', 'package': 'us.zoom.videomeetings'},
        {'name': 'Microsoft Teams', 'package': 'com.microsoft.teams'},
        # 效率
        {'name': 'Notion', 'package': 'notion.id'},
        {'name': 'Todoist', 'package': 'com.todoist'},
        {'name': 'Evernote', 'package': 'com.evernote'},
    ],
}


def ensure_scraper_installed():
    """确保 google-play-scraper 已安装"""
    try:
        import google_play_scraper
        return True
    except ImportError:
        print("正在安装 google-play-scraper...")
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'google-play-scraper', '-q'])
        return True


def fetch_reviews(package: str, app_name: str, count: int = 200) -> List[Dict]:
    """
    使用 google-play-scraper 获取评论
    """
    try:
        from google_play_scraper import reviews, Sort
        
        result, continuation_token = reviews(
            package,
            lang='en',  # 英文评论
            country='us',  # 美国区
            sort=Sort.NEWEST,  # 最新评论
            count=count,
        )
        
        parsed_reviews = []
        for r in result:
            parsed_reviews.append({
                'id': r.get('reviewId', ''),
                'app_name': app_name,
                'package': package,
                'author': r.get('userName', 'anonymous'),
                'rating': r.get('score', 0),
                'content': r.get('content', ''),
                'date': r.get('at').isoformat() if r.get('at') else '',
                'thumbs_up': r.get('thumbsUpCount', 0),
                'reply_content': r.get('replyContent', ''),
                'source': 'Google Play',
                'source_url': f'https://play.google.com/store/apps/details?id={package}',
            })
        
        return parsed_reviews
        
    except Exception as e:
        print(f"  Error fetching {app_name}: {e}")
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
        
        reviews = fetch_reviews(package, app_name, CONFIG['reviews_per_app'])
        
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
        'source': 'Google Play (google-play-scraper)',
        'note': '直接抓取，无需 API key',
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
    
    # 确保依赖已安装
    ensure_scraper_installed()
    
    target_categories = categories or list(CATEGORY_APPS.keys())
    
    print("=" * 60)
    print("Google Play 评论采集器")
    print("数据源: google-play-scraper (无需 API key)")
    print(f"目标类目: {', '.join(target_categories)}")
    print("=" * 60)
    
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
    total = 0
    for cat_id, info in results.items():
        print(f"  {cat_id}: {info['total']} 条评论")
        total += info['total']
    print(f"  总计: {total} 条评论")
    print("=" * 60)
    
    return results


if __name__ == '__main__':
    import sys
    categories = sys.argv[1:] if len(sys.argv) > 1 else None
    main(categories)
