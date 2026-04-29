#!/usr/bin/env python3
"""
豆瓣应用/话题评论采集器
数据源：豆瓣小组、话题讨论

豆瓣用户群体相对专业，评论质量较高
适合采集深度使用体验和产品分析
"""

import json
import time
import os
import urllib.request
import urllib.error
import urllib.parse
import re
from datetime import datetime
from typing import List, Dict, Any, Optional

# 采集配置
CONFIG = {
    'output_dir': '../data/raw/douban',
    'delay_seconds': 3,  # 豆瓣对频率敏感
    'max_posts_per_group': 30,
}

# 豆瓣小组配置（按类目）
CATEGORY_GROUPS = {
    'wechat': {
        'groups': [
            {'id': '692534', 'name': '互联网吐槽'},
            {'id': '579173', 'name': 'App Store推荐'},
        ],
        'search_keywords': ['微信', '微信功能', '微信bug'],
    },
    'social': {
        'groups': [
            {'id': '692534', 'name': '互联网吐槽'},
            {'id': '689453', 'name': '数字生活'},
        ],
        'search_keywords': ['社交软件', '小红书', '微博'],
    },
    'ai': {
        'groups': [
            {'id': '724481', 'name': 'AI前沿'},
            {'id': '715421', 'name': 'ChatGPT研究'},
        ],
        'search_keywords': ['AI助手', 'ChatGPT', 'AI工具'],
    },
    'more': {
        'groups': [
            {'id': '626697', 'name': '效率工具'},
            {'id': '579173', 'name': 'App Store推荐'},
        ],
        'search_keywords': ['办公软件', '效率app', '工具推荐'],
    },
}


def fetch_douban_group_topics(group_id: str, group_name: str) -> List[Dict]:
    """
    获取豆瓣小组的讨论帖子
    """
    url = f'https://www.douban.com/group/{group_id}/discussion'
    
    try:
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml',
            'Accept-Language': 'zh-CN,zh;q=0.9',
        })
        
        with urllib.request.urlopen(req, timeout=30) as response:
            html = response.read().decode('utf-8')
        
        posts = []
        
        # 解析帖子列表
        # 豆瓣小组讨论列表的 HTML 结构
        pattern = r'<a[^>]*href="(https://www\.douban\.com/group/topic/(\d+)/)"[^>]*title="([^"]*)"'
        matches = re.findall(pattern, html)
        
        for url, topic_id, title in matches[:CONFIG['max_posts_per_group']]:
            if not title.strip():
                continue
            
            posts.append({
                'id': topic_id,
                'title': title.strip(),
                'url': url,
                'group_id': group_id,
                'group_name': group_name,
                'source': '豆瓣小组',
                'crawl_date': datetime.now().isoformat(),
            })
        
        return posts
        
    except urllib.error.HTTPError as e:
        print(f"  HTTP Error {e.code}: {group_name}")
        return []
    except Exception as e:
        print(f"  Error: {e}")
        return []


def fetch_topic_content(topic_url: str) -> Optional[Dict]:
    """
    获取帖子详情
    """
    try:
        req = urllib.request.Request(topic_url, headers={
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml',
        })
        
        with urllib.request.urlopen(req, timeout=30) as response:
            html = response.read().decode('utf-8')
        
        # 提取正文内容
        content_pattern = r'<div class="topic-content"[^>]*>(.*?)</div>'
        match = re.search(content_pattern, html, re.DOTALL)
        
        content = ''
        if match:
            content = re.sub(r'<[^>]+>', '', match.group(1))
            content = content.strip()
        
        # 提取回复
        replies = []
        reply_pattern = r'<div class="reply-content"[^>]*>(.*?)</div>'
        reply_matches = re.findall(reply_pattern, html, re.DOTALL)
        
        for reply_html in reply_matches[:10]:
            reply_text = re.sub(r'<[^>]+>', '', reply_html).strip()
            if reply_text and len(reply_text) > 10:
                replies.append({
                    'content': reply_text[:500],
                })
        
        return {
            'content': content[:2000],
            'replies': replies,
            'reply_count': len(replies),
        }
        
    except Exception as e:
        return None


def fetch_douban_search(keyword: str) -> List[Dict]:
    """
    豆瓣搜索
    """
    encoded_keyword = urllib.parse.quote(keyword)
    url = f'https://www.douban.com/search?cat=1019&q={encoded_keyword}'  # cat=1019 是小组讨论
    
    try:
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Accept': 'text/html',
        })
        
        with urllib.request.urlopen(req, timeout=30) as response:
            html = response.read().decode('utf-8')
        
        results = []
        
        # 解析搜索结果
        pattern = r'<a[^>]*href="(https://www\.douban\.com/group/topic/\d+/)"[^>]*>([^<]+)</a>'
        matches = re.findall(pattern, html)
        
        for url, title in matches[:20]:
            results.append({
                'title': title.strip(),
                'url': url,
                'keyword': keyword,
                'source': '豆瓣搜索',
                'crawl_date': datetime.now().isoformat(),
            })
        
        return results
        
    except Exception as e:
        print(f"  搜索失败 '{keyword}': {e}")
        return []


def crawl_category(category_id: str) -> Dict[str, Any]:
    """采集单个类目"""
    
    print(f"\n{'='*50}")
    print(f"豆瓣采集: {category_id}")
    print(f"{'='*50}")
    
    if category_id not in CATEGORY_GROUPS:
        return {'category': category_id, 'items': [], 'error': 'Unknown category'}
    
    config = CATEGORY_GROUPS[category_id]
    all_items = []
    groups_crawled = []
    
    # 1. 采集小组帖子
    for group in config.get('groups', []):
        gid = group['id']
        gname = group['name']
        
        print(f"\n📚 小组: {gname}")
        
        posts = fetch_douban_group_topics(gid, gname)
        
        # 获取部分帖子的详细内容
        for post in posts[:5]:
            time.sleep(1)
            detail = fetch_topic_content(post['url'])
            if detail:
                post.update(detail)
        
        all_items.extend(posts)
        
        groups_crawled.append({
            'group_id': gid,
            'group_name': gname,
            'post_count': len(posts),
        })
        
        print(f"  ✓ 获取 {len(posts)} 条帖子")
        time.sleep(CONFIG['delay_seconds'])
    
    # 2. 关键词搜索补充
    search_results = []
    for keyword in config.get('search_keywords', []):
        print(f"\n🔍 搜索: '{keyword}'")
        results = fetch_douban_search(keyword)
        search_results.extend(results)
        print(f"  ✓ 获取 {len(results)} 条结果")
        time.sleep(CONFIG['delay_seconds'])
    
    all_items.extend(search_results)
    
    return {
        'category': category_id,
        'crawl_date': datetime.now().isoformat(),
        'groups_crawled': groups_crawled,
        'search_keywords': config.get('search_keywords', []),
        'total_items': len(all_items),
        'items': all_items,
        'source': '豆瓣',
        'note': '小组讨论 + 关键词搜索',
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
    target_categories = categories or list(CATEGORY_GROUPS.keys())
    
    print("=" * 60)
    print("豆瓣评论采集器")
    print("数据源: 豆瓣小组讨论")
    print(f"目标类目: {', '.join(target_categories)}")
    print("=" * 60)
    print("\n💡 提示: 豆瓣对爬虫敏感，采集速度较慢")
    
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
    categories = sys.argv[1:] if len(sys.argv) > 1 else None
    main(categories)
