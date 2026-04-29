#!/usr/bin/env python3
"""
知乎话题讨论采集器
数据源：知乎公开 API 和页面

特点：
- 知乎讨论质量高，用户反馈详细
- 适合采集深度使用体验和功能建议
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
    'output_dir': '../data/raw/zhihu',
    'delay_seconds': 2,
    'max_answers_per_question': 20,
    'max_questions_per_topic': 10,
}

# 话题/问题配置（按类目）
CATEGORY_TOPICS = {
    'wechat': {
        'questions': [
            # 微信相关高热度问题
            {'id': '19857563', 'title': '你觉得微信最反人类的设计是什么'},
            {'id': '21172836', 'title': '微信有哪些令人不爽的地方'},
            {'id': '265347014', 'title': '微信有哪些你觉得很鸡肋的功能'},
            {'id': '23927497', 'title': '你希望微信增加什么功能'},
            {'id': '303591717', 'title': '微信占用内存太大怎么办'},
            {'id': '268932330', 'title': '你最受不了微信的什么设计'},
        ],
        'keywords': ['微信 bug', '微信 难用', '微信 建议'],
    },
    'social': {
        'questions': [
            {'id': '337989138', 'title': '小红书有哪些让你不舒服的设计'},
            {'id': '270461919', 'title': '微博有哪些反人类的设计'},
            {'id': '30325513', 'title': '你觉得哪些社交软件最难用'},
        ],
        'keywords': ['社交软件 吐槽', '交友app 体验'],
    },
    'ai': {
        'questions': [
            {'id': '597254344', 'title': 'ChatGPT有哪些局限性'},
            {'id': '611877945', 'title': '国产AI助手哪个最好用'},
            {'id': '603249789', 'title': '使用Kimi是什么体验'},
            {'id': '618745632', 'title': '豆包AI用起来怎么样'},
        ],
        'keywords': ['AI助手 对比', 'ChatGPT 缺点', 'AI工具 推荐'],
    },
    'more': {
        'questions': [
            {'id': '28463946', 'title': '钉钉有哪些反人类的设计'},
            {'id': '349816447', 'title': '飞书用起来怎么样'},
            {'id': '30645811', 'title': '有哪些好用的效率工具'},
            {'id': '437892713', 'title': '腾讯会议有什么让你不满的地方'},
        ],
        'keywords': ['办公软件 吐槽', '效率工具 推荐'],
    },
}


def fetch_zhihu_question_answers(question_id: str, question_title: str) -> List[Dict]:
    """
    获取知乎问题的回答
    使用知乎公开 API
    """
    url = f'https://www.zhihu.com/api/v4/questions/{question_id}/answers'
    params = {
        'include': 'content,excerpt,voteup_count,comment_count,created_time',
        'limit': CONFIG['max_answers_per_question'],
        'offset': 0,
        'sort_by': 'default',
    }
    full_url = f"{url}?{urllib.parse.urlencode(params)}"
    
    try:
        req = urllib.request.Request(full_url, headers={
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Accept': 'application/json',
            'Referer': f'https://www.zhihu.com/question/{question_id}',
        })
        
        with urllib.request.urlopen(req, timeout=30) as response:
            data = json.loads(response.read().decode('utf-8'))
        
        answers = []
        for item in data.get('data', []):
            # 清理 HTML 标签
            content = item.get('content', '')
            content = re.sub(r'<[^>]+>', '', content)
            content = content.strip()
            
            if len(content) < 20:  # 过滤太短的回答
                continue
            
            answers.append({
                'id': item.get('id', ''),
                'question_id': question_id,
                'question_title': question_title,
                'content': content[:2000],  # 限制长度
                'excerpt': item.get('excerpt', ''),
                'author': item.get('author', {}).get('name', '匿名用户'),
                'voteup_count': item.get('voteup_count', 0),
                'comment_count': item.get('comment_count', 0),
                'created_time': item.get('created_time', 0),
                'date': datetime.fromtimestamp(item.get('created_time', 0)).isoformat() if item.get('created_time') else '',
                'source': '知乎',
                'source_url': f"https://www.zhihu.com/question/{question_id}/answer/{item.get('id', '')}",
            })
        
        return answers
        
    except urllib.error.HTTPError as e:
        if e.code == 403:
            print(f"  ⚠️ 需要登录: {question_title}")
        else:
            print(f"  HTTP Error {e.code}: {question_title}")
        return []
    except Exception as e:
        print(f"  Error: {e}")
        return []


def fetch_zhihu_search(keyword: str) -> List[Dict]:
    """
    知乎搜索
    """
    encoded_keyword = urllib.parse.quote(keyword)
    url = f'https://www.zhihu.com/api/v4/search_v3?t=general&q={encoded_keyword}&correction=1&offset=0&limit=10'
    
    try:
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Accept': 'application/json',
        })
        
        with urllib.request.urlopen(req, timeout=30) as response:
            data = json.loads(response.read().decode('utf-8'))
        
        results = []
        for item in data.get('data', []):
            obj = item.get('object', {})
            if obj.get('type') == 'answer':
                content = obj.get('content', '')
                content = re.sub(r'<[^>]+>', '', content)
                
                results.append({
                    'id': obj.get('id', ''),
                    'type': 'answer',
                    'content': content[:1000],
                    'author': obj.get('author', {}).get('name', ''),
                    'voteup_count': obj.get('voteup_count', 0),
                    'keyword': keyword,
                    'source': '知乎搜索',
                    'crawl_date': datetime.now().isoformat(),
                })
        
        return results
        
    except Exception as e:
        print(f"  搜索失败 '{keyword}': {e}")
        return []


def crawl_category(category_id: str) -> Dict[str, Any]:
    """采集单个类目"""
    
    print(f"\n{'='*50}")
    print(f"知乎采集: {category_id}")
    print(f"{'='*50}")
    
    if category_id not in CATEGORY_TOPICS:
        return {'category': category_id, 'items': [], 'error': 'Unknown category'}
    
    config = CATEGORY_TOPICS[category_id]
    all_items = []
    questions_crawled = []
    
    # 1. 采集指定问题的回答
    for q in config.get('questions', []):
        qid = q['id']
        qtitle = q['title']
        
        print(f"\n📝 问题: {qtitle[:30]}...")
        
        answers = fetch_zhihu_question_answers(qid, qtitle)
        all_items.extend(answers)
        
        questions_crawled.append({
            'question_id': qid,
            'question_title': qtitle,
            'answer_count': len(answers),
        })
        
        print(f"  ✓ 获取 {len(answers)} 条回答")
        time.sleep(CONFIG['delay_seconds'])
    
    # 2. 关键词搜索补充
    search_results = []
    for keyword in config.get('keywords', []):
        print(f"\n🔍 搜索: '{keyword}'")
        results = fetch_zhihu_search(keyword)
        search_results.extend(results)
        print(f"  ✓ 获取 {len(results)} 条结果")
        time.sleep(CONFIG['delay_seconds'])
    
    all_items.extend(search_results)
    
    return {
        'category': category_id,
        'crawl_date': datetime.now().isoformat(),
        'questions_crawled': questions_crawled,
        'search_keywords': config.get('keywords', []),
        'total_items': len(all_items),
        'items': all_items,
        'source': '知乎',
        'note': '问题回答 + 关键词搜索',
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
    target_categories = categories or list(CATEGORY_TOPICS.keys())
    
    print("=" * 60)
    print("知乎话题讨论采集器")
    print("数据源: 知乎问答 + 搜索")
    print(f"目标类目: {', '.join(target_categories)}")
    print("=" * 60)
    print("\n💡 提示: 知乎 API 对频率有限制，采集速度较慢")
    
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
