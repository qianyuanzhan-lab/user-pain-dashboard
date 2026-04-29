#!/usr/bin/env python3
"""
Hacker News 评论采集器
数据源：Hacker News Algolia API（完全免费、无需 API key）
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
    'output_dir': '../data/raw/hackernews',
    'delay_seconds': 1,  # 请求间隔
    'hits_per_page': 100,  # 每页结果数
    'max_pages': 5,  # 每个关键词最多采集页数
    'max_age_days': 365,  # 只采集最近N天的数据（默认一年）
}

# 搜索关键词配置（按类目组织）
SEARCH_KEYWORDS = {
    'wechat': [
        'WeChat', 'wechat app', 'wechat feature', 'wechat problem',
        'wechat mini program', 'wechat pay',
    ],
    'social': [
        'messaging app', 'social app', 'dating app',
        'Tinder', 'Bumble', 'Discord', 'Telegram',
        'social media problems', 'Twitter alternative', 'Reddit app',
        'podcast app', 'Spotify podcast',
    ],
    'ai': [
        'ChatGPT', 'ChatGPT problem', 'ChatGPT feature',
        'Claude AI', 'AI assistant', 'AI chatbot',
        'Copilot', 'AI coding', 'LLM hallucination',
        'AI memory', 'context window', 'AI limitation',
    ],
    'more': [
        'Slack notification', 'Zoom problem', 'meeting app',
        'productivity app', 'todo app', 'note taking app',
        'Notion', 'Obsidian', 'calendar app',
    ],
}


def fetch_hn_comments(query: str, page: int = 0) -> Dict[str, Any]:
    """
    从 Hacker News Algolia API 获取评论
    API 文档: https://hn.algolia.com/api
    """
    # 计算时间过滤：只获取最近 N 天的数据
    cutoff_timestamp = int((datetime.now() - timedelta(days=CONFIG['max_age_days'])).timestamp())
    
    # tags=comment 只搜索评论（不包括帖子标题）
    # numericFilters 用于时间过滤
    encoded_query = urllib.parse.quote(query)
    url = (
        f'https://hn.algolia.com/api/v1/search?query={encoded_query}'
        f'&tags=comment&hitsPerPage={CONFIG["hits_per_page"]}&page={page}'
        f'&numericFilters=created_at_i>{cutoff_timestamp}'
    )
    
    try:
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (research bot)',
        })
        with urllib.request.urlopen(req, timeout=30) as response:
            data = json.loads(response.read().decode('utf-8'))
        
        return {
            'hits': data.get('hits', []),
            'nbHits': data.get('nbHits', 0),
            'nbPages': data.get('nbPages', 0),
            'page': data.get('page', 0),
        }
    except Exception as e:
        print(f"  Error fetching '{query}': {e}")
        return {'hits': [], 'nbHits': 0, 'nbPages': 0, 'page': 0}


def parse_hn_comment(hit: Dict) -> Dict[str, Any]:
    """解析单条 HN 评论"""
    # 清理 HTML 标签
    comment_text = hit.get('comment_text', '')
    if comment_text:
        import re
        comment_text = re.sub(r'<[^>]+>', ' ', comment_text)
        comment_text = re.sub(r'\s+', ' ', comment_text).strip()
    
    return {
        'id': hit.get('objectID', ''),
        'author': hit.get('author', 'anonymous'),
        'content': comment_text,
        'created_at': hit.get('created_at', ''),
        'points': hit.get('points', 0),
        'story_id': hit.get('story_id', ''),
        'story_title': hit.get('story_title', ''),
        'story_url': hit.get('story_url', ''),
        'source_url': f"https://news.ycombinator.com/item?id={hit.get('objectID', '')}",
        'source': 'Hacker News',
    }


def crawl_category(category_id: str) -> Dict[str, Any]:
    """采集单个类目"""
    
    print(f"\n{'='*50}")
    print(f"Hacker News 采集: {category_id}")
    print(f"{'='*50}")
    
    if category_id not in SEARCH_KEYWORDS:
        return {'category': category_id, 'comments': [], 'error': 'Unknown category'}
    
    all_comments = []
    keywords_crawled = []
    seen_ids = set()  # 去重
    
    for keyword in SEARCH_KEYWORDS[category_id]:
        print(f"\n🔍 搜索: '{keyword}'")
        
        keyword_comments = []
        for page in range(CONFIG['max_pages']):
            result = fetch_hn_comments(keyword, page)
            
            if not result['hits']:
                break
            
            for hit in result['hits']:
                if hit.get('objectID') not in seen_ids:
                    seen_ids.add(hit.get('objectID'))
                    comment = parse_hn_comment(hit)
                    if comment['content'] and len(comment['content']) > 20:  # 过滤太短的
                        keyword_comments.append(comment)
            
            print(f"  Page {page + 1}: {len(result['hits'])} hits, total unique: {len(keyword_comments)}")
            
            # 如果已经没有更多页了
            if page >= result['nbPages'] - 1:
                break
            
            time.sleep(CONFIG['delay_seconds'])
        
        all_comments.extend(keyword_comments)
        keywords_crawled.append({
            'keyword': keyword,
            'comment_count': len(keyword_comments),
        })
        
        print(f"  ✓ '{keyword}': {len(keyword_comments)} 条评论")
        time.sleep(CONFIG['delay_seconds'])
    
    return {
        'category': category_id,
        'crawl_date': datetime.now().isoformat(),
        'keywords_crawled': keywords_crawled,
        'total_comments': len(all_comments),
        'comments': all_comments,
        'source': 'Hacker News (Algolia API)',
        'note': '免费 API，无需 key',
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
    import urllib.parse  # 确保导入
    
    target_categories = categories or list(SEARCH_KEYWORDS.keys())
    
    print("=" * 60)
    print("Hacker News 评论采集器")
    print("数据源: Algolia API (免费、无需 key)")
    print(f"目标类目: {', '.join(target_categories)}")
    print("=" * 60)
    
    results = {}
    
    for cat_id in target_categories:
        data = crawl_category(cat_id)
        filepath = save_results(cat_id, data)
        results[cat_id] = {
            'file': filepath,
            'total': data['total_comments'],
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
    import urllib.parse
    categories = sys.argv[1:] if len(sys.argv) > 1 else None
    main(categories)
