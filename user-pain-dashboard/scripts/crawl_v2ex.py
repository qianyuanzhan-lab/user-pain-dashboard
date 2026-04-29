#!/usr/bin/env python3
"""
V2EX 评论采集器
数据源：V2EX 公开 API（无需登录）
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
    'output_dir': '../data/raw/v2ex',
    'delay_seconds': 1,
    'topics_per_node': 50,
}

# 节点配置（按类目）
CATEGORY_NODES = {
    'wechat': [
        {'node': 'wechat', 'name': '微信'},
    ],
    'social': [
        {'node': 'twitter', 'name': 'Twitter'},
        {'node': 'telegram', 'name': 'Telegram'},
        {'node': 'sns', 'name': '社交网络'},
    ],
    'ai': [
        {'node': 'ai', 'name': 'AI'},
        {'node': 'openai', 'name': 'OpenAI'},
        {'node': 'chatgpt', 'name': 'ChatGPT'},
        {'node': 'llm', 'name': 'LLM'},
    ],
    'more': [
        {'node': 'apple', 'name': 'Apple'},
        {'node': 'programmer', 'name': '程序员'},
        {'node': 'macos', 'name': 'macOS'},
        {'node': 'android', 'name': 'Android'},
        {'node': 'iphone', 'name': 'iPhone'},
        {'node': 'career', 'name': '职场'},
        {'node': 'remote', 'name': '远程工作'},
    ],
}


def fetch_node_topics(node: str) -> List[Dict]:
    """
    从 V2EX 获取节点下的主题
    API 文档: https://www.v2ex.com/api/
    """
    url = f'https://www.v2ex.com/api/topics/show.json?node_name={node}'
    
    try:
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (research bot)',
        })
        with urllib.request.urlopen(req, timeout=30) as response:
            topics = json.loads(response.read().decode('utf-8'))
        
        parsed = []
        for t in topics:
            parsed.append({
                'id': t.get('id', ''),
                'title': t.get('title', ''),
                'content': t.get('content', ''),
                'author': t.get('member', {}).get('username', ''),
                'replies': t.get('replies', 0),
                'created': t.get('created', 0),
                'date': datetime.fromtimestamp(t.get('created', 0)).isoformat() if t.get('created') else '',
                'node': node,
                'source': 'V2EX',
                'source_url': t.get('url', ''),
            })
        
        return parsed
        
    except Exception as e:
        print(f"  Error fetching node {node}: {e}")
        return []


def fetch_topic_replies(topic_id: int) -> List[Dict]:
    """获取主题的回复"""
    url = f'https://www.v2ex.com/api/replies/show.json?topic_id={topic_id}'
    
    try:
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (research bot)',
        })
        with urllib.request.urlopen(req, timeout=30) as response:
            replies = json.loads(response.read().decode('utf-8'))
        
        parsed = []
        for r in replies:
            parsed.append({
                'id': r.get('id', ''),
                'topic_id': topic_id,
                'content': r.get('content', ''),
                'author': r.get('member', {}).get('username', ''),
                'created': r.get('created', 0),
                'date': datetime.fromtimestamp(r.get('created', 0)).isoformat() if r.get('created') else '',
                'source': 'V2EX',
                'source_url': f'https://www.v2ex.com/t/{topic_id}',
            })
        
        return parsed
        
    except Exception as e:
        return []


def crawl_category(category_id: str) -> Dict[str, Any]:
    """采集单个类目"""
    
    print(f"\n{'='*50}")
    print(f"V2EX 采集: {category_id}")
    print(f"{'='*50}")
    
    if category_id not in CATEGORY_NODES:
        return {'category': category_id, 'items': [], 'error': 'Unknown category'}
    
    all_items = []
    nodes_crawled = []
    
    for config in CATEGORY_NODES[category_id]:
        node = config['node']
        name = config['name']
        
        print(f"\n📱 采集节点: {name} ({node})")
        
        # 获取主题
        topics = fetch_node_topics(node)
        
        # 获取前 5 个主题的回复
        reply_count = 0
        for topic in topics[:5]:
            if topic.get('id'):
                replies = fetch_topic_replies(topic['id'])
                all_items.extend(replies)
                reply_count += len(replies)
                time.sleep(0.5)
        
        all_items.extend(topics)
        
        nodes_crawled.append({
            'node': node,
            'name': name,
            'topic_count': len(topics),
            'reply_count': reply_count,
        })
        
        print(f"  ✓ {name}: {len(topics)} 主题, {reply_count} 回复")
        time.sleep(CONFIG['delay_seconds'])
    
    return {
        'category': category_id,
        'crawl_date': datetime.now().isoformat(),
        'nodes_crawled': nodes_crawled,
        'total_items': len(all_items),
        'items': all_items,
        'source': 'V2EX (public API)',
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
    target_categories = categories or list(CATEGORY_NODES.keys())
    
    print("=" * 60)
    print("V2EX 评论采集器")
    print("数据源: V2EX API (无需 API key)")
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
    categories = sys.argv[1:] if len(sys.argv) > 1 else None
    main(categories)
