#!/usr/bin/env python3
"""
黑猫投诉采集器 V2
使用黑猫投诉的 JSON API 接口
"""

import json
import time
import os
import urllib.request
import urllib.error
import urllib.parse
from datetime import datetime
from typing import List, Dict, Any, Optional

# 配置
CONFIG = {
    'output_dir': '../data/raw/heimao',
    'delay_seconds': 2,
    'max_pages': 10,
}

# 采集目标
CATEGORY_KEYWORDS = {
    'wechat': ['微信', '微信支付', '微信转账', '微信红包'],
    'social': ['Soul APP', '探探', '陌陌', '即刻'],
    'ai': ['ChatGPT', 'Kimi', '豆包 AI', 'Claude', '文心一言', '通义千问'],
    'more': ['飞书', '钉钉', '企业微信', '腾讯会议'],
}


def search_heimao_api(keyword: str, page: int = 1) -> List[Dict]:
    """使用黑猫投诉搜索 API"""
    encoded = urllib.parse.quote(keyword)
    # 黑猫投诉的搜索 API
    url = f'https://tousu.sina.com.cn/api/index/s?keywords={encoded}&page_size=20&page={page}'
    
    try:
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json',
            'Referer': 'https://tousu.sina.com.cn/',
        })
        with urllib.request.urlopen(req, timeout=30) as response:
            data = json.loads(response.read().decode('utf-8'))
        
        complaints = []
        items = data.get('result', {}).get('data', {}).get('lists', [])
        
        for item in items:
            complaints.append({
                'keyword': keyword,
                'title': item.get('main', {}).get('title', ''),
                'summary': item.get('main', {}).get('summary', ''),
                'company': item.get('main', {}).get('cotitle', ''),
                'status': item.get('main', {}).get('status_desc', ''),
                'timestamp': item.get('main', {}).get('timestamp', ''),
                'appeal': item.get('main', {}).get('appeal', ''),
                'url': f"https://tousu.sina.com.cn/complaint/view/{item.get('main', {}).get('sn', '')}/",
                'source': '黑猫投诉',
                'source_id': 'heimao',
                'crawl_date': datetime.now().isoformat(),
            })
        
        return complaints
        
    except urllib.error.HTTPError as e:
        print(f"  HTTP Error {e.code}: {e.reason}")
        return []
    except Exception as e:
        print(f"  Error: {e}")
        return []


def fetch_complaint_detail(url: str) -> Dict:
    """获取投诉详情（可选）"""
    try:
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        })
        with urllib.request.urlopen(req, timeout=15) as response:
            html = response.read().decode('utf-8')
        
        # 简单提取投诉内容
        import re
        content_match = re.search(r'class="complaint-cont"[^>]*>(.*?)</div>', html, re.DOTALL)
        if content_match:
            content = re.sub(r'<[^>]+>', '', content_match.group(1)).strip()
            return {'detail': content[:500]}
        
        return {}
    except:
        return {}


def crawl_category(category_id: str) -> Dict[str, Any]:
    """采集单个类目"""
    print(f"\n{'='*50}")
    print(f"黑猫投诉采集: {category_id}")
    print(f"{'='*50}")
    
    if category_id not in CATEGORY_KEYWORDS:
        return {'category': category_id, 'complaints': [], 'error': 'Unknown category'}
    
    all_complaints = []
    keywords_crawled = []
    
    for keyword in CATEGORY_KEYWORDS[category_id]:
        print(f"\n🔍 搜索关键词: {keyword}")
        keyword_complaints = []
        
        for page in range(1, CONFIG['max_pages'] + 1):
            print(f"  第 {page} 页...", end=' ')
            
            complaints = search_heimao_api(keyword, page)
            
            if not complaints:
                print("无更多数据")
                break
            
            keyword_complaints.extend(complaints)
            print(f"获取 {len(complaints)} 条")
            
            time.sleep(CONFIG['delay_seconds'])
            
            # 如果这页不满，说明没有更多了
            if len(complaints) < 15:
                break
        
        all_complaints.extend(keyword_complaints)
        keywords_crawled.append({
            'keyword': keyword,
            'count': len(keyword_complaints),
        })
        print(f"  ✓ {keyword}: {len(keyword_complaints)} 条投诉")
    
    # 去重（同一条投诉可能被多个关键词搜到）
    seen_urls = set()
    unique_complaints = []
    for c in all_complaints:
        if c['url'] not in seen_urls:
            seen_urls.add(c['url'])
            unique_complaints.append(c)
    
    print(f"\n去重后: {len(unique_complaints)} 条")
    
    return {
        'category': category_id,
        'crawl_date': datetime.now().isoformat(),
        'source': '黑猫投诉',
        'source_id': 'heimao',
        'keywords_crawled': keywords_crawled,
        'total_complaints': len(unique_complaints),
        'complaints': unique_complaints,
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
    target_categories = categories or list(CATEGORY_KEYWORDS.keys())
    
    print("=" * 60)
    print("黑猫投诉采集器 V2")
    print(f"目标类目: {', '.join(target_categories)}")
    print("=" * 60)
    
    results = {}
    total_all = 0
    
    for cat_id in target_categories:
        data = crawl_category(cat_id)
        filepath = save_results(cat_id, data)
        results[cat_id] = {
            'file': filepath,
            'total': data['total_complaints'],
        }
        total_all += data['total_complaints']
    
    print("\n" + "=" * 60)
    print("采集完成汇总:")
    for cat_id, info in results.items():
        print(f"  {cat_id}: {info['total']} 条投诉")
    print(f"\n总计: {total_all} 条")
    print("=" * 60)
    
    return results


if __name__ == '__main__':
    import sys
    categories = sys.argv[1:] if len(sys.argv) > 1 else None
    main(categories)
