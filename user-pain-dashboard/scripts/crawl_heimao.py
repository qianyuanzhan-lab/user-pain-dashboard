#!/usr/bin/env python3
"""
黑猫投诉采集器
数据源：新浪黑猫投诉平台（公开投诉数据）
"""

import json
import time
import os
import urllib.request
import urllib.error
import urllib.parse
import re
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

# 采集配置
CONFIG = {
    'output_dir': '../data/raw/heimao',
    'delay_seconds': 3,
    'max_pages': 5,
    'time_range_days': 365,
}

# 企业投诉页配置
CATEGORY_COMPANIES = {
    'wechat': [
        {'name': '微信', 'couid': '5272087655', 'keywords': ['微信', '微信支付']},
    ],
    'social': [
        {'name': 'Soul', 'couid': '5772598187', 'keywords': ['Soul', '匿名', '骚扰']},
        {'name': '探探', 'couid': '5262441113', 'keywords': ['探探', '真人', '机器人']},
        {'name': '陌陌', 'couid': '5292887173', 'keywords': ['陌陌', '诈骗', '封号']},
    ],
    'ai': [
        {'name': 'ChatGPT', 'couid': None, 'keywords': ['ChatGPT', 'OpenAI']},
        {'name': 'Kimi', 'couid': None, 'keywords': ['Kimi', '月之暗面']},
        {'name': '豆包', 'couid': None, 'keywords': ['豆包', '字节', 'AI']},
    ],
    'more': [
        {'name': '作业帮', 'couid': '5163050095', 'keywords': ['作业帮', '退款']},
        {'name': '飞书', 'couid': None, 'keywords': ['飞书']},
        {'name': '钉钉', 'couid': '5193149127', 'keywords': ['钉钉']},
    ],
}


def fetch_heimao_company(couid: str, company_name: str, page: int = 1) -> List[Dict]:
    """获取企业投诉列表"""
    url = f'https://tousu.sina.com.cn/company/view/?couid={couid}&page={page}'
    
    try:
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Referer': 'https://tousu.sina.com.cn/',
        })
        with urllib.request.urlopen(req, timeout=30) as response:
            html = response.read().decode('utf-8')
        
        complaints = []
        
        # 提取投诉条目
        pattern = r'<a[^>]*href="(/complaint/view/\d+/)"[^>]*>([^<]+)</a>'
        matches = re.findall(pattern, html)
        
        for link, title in matches[:20]:
            complaints.append({
                'company': company_name,
                'title': title.strip(),
                'url': f'https://tousu.sina.com.cn{link}',
                'source': '黑猫投诉',
                'crawl_date': datetime.now().isoformat(),
            })
        
        return complaints
        
    except Exception as e:
        print(f"  Error: {e}")
        return []


def search_heimao(keyword: str, page: int = 1) -> List[Dict]:
    """搜索黑猫投诉（用于没有企业主页的品牌）"""
    encoded = urllib.parse.quote(keyword)
    url = f'https://tousu.sina.com.cn/index/search?keywords={encoded}&page={page}'
    
    try:
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        })
        with urllib.request.urlopen(req, timeout=30) as response:
            html = response.read().decode('utf-8')
        
        results = []
        pattern = r'<a[^>]*href="(/complaint/view/\d+/)"[^>]*>([^<]+)</a>'
        matches = re.findall(pattern, html)
        
        for link, title in matches[:10]:
            results.append({
                'keyword': keyword,
                'title': title.strip(),
                'url': f'https://tousu.sina.com.cn{link}',
                'source': '黑猫投诉',
                'crawl_date': datetime.now().isoformat(),
            })
        
        return results
        
    except Exception as e:
        print(f"  Search error: {e}")
        return []


def crawl_category(category_id: str) -> Dict[str, Any]:
    """采集单个类目"""
    
    print(f"\n{'='*50}")
    print(f"黑猫投诉采集: {category_id}")
    print(f"{'='*50}")
    
    if category_id not in CATEGORY_COMPANIES:
        return {'category': category_id, 'complaints': [], 'error': 'Unknown category'}
    
    all_complaints = []
    companies_crawled = []
    
    for company in CATEGORY_COMPANIES[category_id]:
        name = company['name']
        couid = company.get('couid')
        keywords = company.get('keywords', [])
        
        print(f"\n📋 采集 {name}")
        company_complaints = []
        
        if couid:
            # 有企业主页，直接采集
            for page in range(1, CONFIG['max_pages'] + 1):
                print(f"  页码 {page}...", end=' ')
                complaints = fetch_heimao_company(couid, name, page)
                if not complaints:
                    print("无数据")
                    break
                company_complaints.extend(complaints)
                print(f"获取 {len(complaints)} 条")
                time.sleep(CONFIG['delay_seconds'])
        else:
            # 没有企业主页，用关键词搜索
            for kw in keywords[:2]:  # 最多 2 个关键词
                print(f"  搜索关键词: {kw}...", end=' ')
                results = search_heimao(kw)
                company_complaints.extend(results)
                print(f"获取 {len(results)} 条")
                time.sleep(CONFIG['delay_seconds'])
        
        all_complaints.extend(company_complaints)
        companies_crawled.append({
            'name': name,
            'couid': couid,
            'count': len(company_complaints),
        })
        print(f"  ✓ {name}: {len(company_complaints)} 条投诉")
    
    return {
        'category': category_id,
        'crawl_date': datetime.now().isoformat(),
        'companies_crawled': companies_crawled,
        'total_complaints': len(all_complaints),
        'complaints': all_complaints,
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
    target_categories = categories or list(CATEGORY_COMPANIES.keys())
    
    print("=" * 60)
    print("黑猫投诉采集器")
    print(f"目标类目: {', '.join(target_categories)}")
    print("=" * 60)
    
    results = {}
    
    for cat_id in target_categories:
        data = crawl_category(cat_id)
        filepath = save_results(cat_id, data)
        results[cat_id] = {
            'file': filepath,
            'total': data['total_complaints'],
        }
    
    print("\n" + "=" * 60)
    print("采集完成汇总:")
    for cat_id, info in results.items():
        print(f"  {cat_id}: {info['total']} 条投诉")
    print("=" * 60)
    
    return results


if __name__ == '__main__':
    import sys
    categories = sys.argv[1:] if len(sys.argv) > 1 else None
    main(categories)
