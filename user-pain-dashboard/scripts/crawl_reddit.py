#!/usr/bin/env python3
"""
Reddit 评论采集器
数据源：Reddit 公开 JSON API（无需登录/API key）
"""

import json
import time
import os
import urllib.request
import urllib.error
from datetime import datetime
from typing import List, Dict, Any, Optional

# 采集配置
CONFIG = {
    'output_dir': '../data/raw/reddit',
    'delay_seconds': 2,  # Reddit 有 rate limit
    'posts_per_subreddit': 50,
}

# Subreddit 配置（按类目）
CATEGORY_SUBREDDITS = {
    'wechat': [
        {'subreddit': 'China', 'search': 'WeChat'},
        {'subreddit': 'ChineseLanguage', 'search': 'WeChat'},
        {'subreddit': 'apps', 'search': 'WeChat'},
    ],
    'social': [
        # 约会/社交
        {'subreddit': 'Tinder', 'search': ''},
        {'subreddit': 'Bumble', 'search': ''},
        {'subreddit': 'hingeapp', 'search': ''},
        {'subreddit': 'OnlineDating', 'search': ''},
        # 通讯
        {'subreddit': 'Telegram', 'search': ''},
        {'subreddit': 'discordapp', 'search': 'problem OR bug OR feature'},
        {'subreddit': 'signal', 'search': ''},
        # 社交媒体
        {'subreddit': 'Twitter', 'search': 'problem OR bug OR feature'},
    ],
    'ai': [
        {'subreddit': 'ChatGPT', 'search': ''},
        {'subreddit': 'OpenAI', 'search': ''},
        {'subreddit': 'ClaudeAI', 'search': ''},
        {'subreddit': 'LocalLLaMA', 'search': 'problem OR limitation'},
        {'subreddit': 'artificial', 'search': 'chatgpt OR claude OR copilot'},
        {'subreddit': 'singularity', 'search': 'chatgpt problem'},
        {'subreddit': 'bing', 'search': 'copilot'},
    ],
    'more': [
        # 办公
        {'subreddit': 'Slack', 'search': ''},
        {'subreddit': 'Zoom', 'search': ''},
        {'subreddit': 'MicrosoftTeams', 'search': ''},
        # 效率
        {'subreddit': 'Notion', 'search': ''},
        {'subreddit': 'todoist', 'search': ''},
        {'subreddit': 'Evernote', 'search': ''},
        {'subreddit': 'ObsidianMD', 'search': ''},
        {'subreddit': 'productivity', 'search': 'app problem OR app feature'},
    ],
}


def fetch_subreddit_posts(subreddit: str, search: str = '', limit: int = 50) -> List[Dict]:
    """
    从 Reddit 获取帖子和评论
    使用公开 JSON API，无需认证
    """
    posts = []
    
    # 构建 URL
    if search:
        url = f'https://www.reddit.com/r/{subreddit}/search.json?q={urllib.parse.quote(search)}&restrict_sr=1&sort=relevance&limit={limit}'
    else:
        url = f'https://www.reddit.com/r/{subreddit}/hot.json?limit={limit}'
    
    try:
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (research bot for academic purposes)',
        })
        with urllib.request.urlopen(req, timeout=30) as response:
            data = json.loads(response.read().decode('utf-8'))
        
        for post in data.get('data', {}).get('children', []):
            post_data = post.get('data', {})
            
            # 帖子本身
            posts.append({
                'id': post_data.get('id', ''),
                'type': 'post',
                'subreddit': subreddit,
                'author': post_data.get('author', '[deleted]'),
                'title': post_data.get('title', ''),
                'content': post_data.get('selftext', ''),
                'score': post_data.get('score', 0),
                'num_comments': post_data.get('num_comments', 0),
                'created_utc': post_data.get('created_utc', 0),
                'date': datetime.fromtimestamp(post_data.get('created_utc', 0)).isoformat() if post_data.get('created_utc') else '',
                'source': 'Reddit',
                'source_url': f"https://reddit.com{post_data.get('permalink', '')}",
            })
        
        return posts
        
    except Exception as e:
        print(f"  Error fetching r/{subreddit}: {e}")
        return []


def fetch_post_comments(permalink: str) -> List[Dict]:
    """获取帖子的评论"""
    url = f'https://www.reddit.com{permalink}.json?limit=100'
    
    try:
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (research bot)',
        })
        with urllib.request.urlopen(req, timeout=30) as response:
            data = json.loads(response.read().decode('utf-8'))
        
        comments = []
        
        # 评论在第二个元素
        if len(data) > 1:
            comment_data = data[1].get('data', {}).get('children', [])
            for comment in comment_data:
                if comment.get('kind') == 't1':
                    c = comment.get('data', {})
                    if c.get('body') and c.get('body') != '[deleted]':
                        comments.append({
                            'id': c.get('id', ''),
                            'type': 'comment',
                            'author': c.get('author', '[deleted]'),
                            'content': c.get('body', ''),
                            'score': c.get('score', 0),
                            'created_utc': c.get('created_utc', 0),
                            'date': datetime.fromtimestamp(c.get('created_utc', 0)).isoformat() if c.get('created_utc') else '',
                            'source': 'Reddit',
                            'source_url': f"https://reddit.com{permalink}",
                        })
        
        return comments
        
    except Exception as e:
        return []


def crawl_category(category_id: str) -> Dict[str, Any]:
    """采集单个类目"""
    
    print(f"\n{'='*50}")
    print(f"Reddit 采集: {category_id}")
    print(f"{'='*50}")
    
    if category_id not in CATEGORY_SUBREDDITS:
        return {'category': category_id, 'items': [], 'error': 'Unknown category'}
    
    all_items = []
    subreddits_crawled = []
    
    for config in CATEGORY_SUBREDDITS[category_id]:
        subreddit = config['subreddit']
        search = config.get('search', '')
        
        print(f"\n📱 采集 r/{subreddit}" + (f" (搜索: {search})" if search else ""))
        
        # 获取帖子
        posts = fetch_subreddit_posts(subreddit, search, CONFIG['posts_per_subreddit'])
        
        # 获取前 10 个帖子的评论
        comment_count = 0
        for post in posts[:10]:
            if post.get('source_url'):
                permalink = post['source_url'].replace('https://reddit.com', '')
                comments = fetch_post_comments(permalink)
                all_items.extend(comments)
                comment_count += len(comments)
                time.sleep(0.5)  # 避免 rate limit
        
        all_items.extend(posts)
        
        subreddits_crawled.append({
            'subreddit': subreddit,
            'search': search,
            'post_count': len(posts),
            'comment_count': comment_count,
        })
        
        print(f"  ✓ r/{subreddit}: {len(posts)} 帖子, {comment_count} 评论")
        time.sleep(CONFIG['delay_seconds'])
    
    return {
        'category': category_id,
        'crawl_date': datetime.now().isoformat(),
        'subreddits_crawled': subreddits_crawled,
        'total_items': len(all_items),
        'items': all_items,
        'source': 'Reddit (public JSON API)',
        'note': '无需 API key',
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
    import urllib.parse
    
    target_categories = categories or list(CATEGORY_SUBREDDITS.keys())
    
    print("=" * 60)
    print("Reddit 评论采集器")
    print("数据源: Reddit JSON API (无需 API key)")
    print(f"目标类目: {', '.join(target_categories)}")
    print("=" * 60)
    
    results = {}
    
    for cat_id in target_categories:
        data = crawl_category(cat_id)
        filepath = save_results(cat_id, data)
        results[cat_id] = {
            'file': filepath,
            'total': data['total_items'],
        }
    
    print("\n" + "=" * 60)
    print("采集完成汇总:")
    total = 0
    for cat_id, info in results.items():
        print(f"  {cat_id}: {info['total']} 条")
        total += info['total']
    print(f"  总计: {total} 条")
    print("=" * 60)
    
    return results


if __name__ == '__main__':
    import sys
    import urllib.parse
    categories = sys.argv[1:] if len(sys.argv) > 1 else None
    main(categories)
