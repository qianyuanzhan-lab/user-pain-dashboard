#!/usr/bin/env python3
"""
小红书用户评价采集器
数据源：小红书公开笔记页面
用于采集用户对各类 App 的使用体验分享

注意：
- 采集公开笔记内容
- 遵守请求频率限制
- 仅用于产品研究
"""

import json
import time
import os
import urllib.request
import urllib.error
import urllib.parse
import re
import hashlib
from datetime import datetime
from typing import List, Dict, Any, Optional

# 采集配置
CONFIG = {
    'output_dir': '../data/raw/xiaohongshu',
    'delay_seconds': 3,  # 请求间隔，避免被限流
    'max_notes_per_keyword': 30,
}

# 搜索关键词配置（按类目）
CATEGORY_KEYWORDS = {
    'wechat': [
        '微信bug', '微信更新吐槽', '微信占内存', '微信卡顿',
        '微信功能建议', '微信使用技巧', '为什么微信',
        '微信太难用', '微信存储空间', '微信清理',
    ],
    'social': [
        '小红书bug', '微博难用', 'Soul使用体验',
        '社交软件推荐', '交友app踩雷', '社交软件对比',
        '探探真实体验', '陌陌使用感受', '即刻app',
    ],
    'ai': [
        'ChatGPT使用体验', 'Kimi测评', '豆包AI测评',
        'AI助手对比', '文心一言体验', 'AI工具推荐',
        'AI写作工具', 'AI绘画app', 'AI翻译app',
        'DeepSeek体验', '通义千问测评',
    ],
    'more': [
        '办公软件推荐', '效率app推荐', '飞书使用体验',
        '钉钉吐槽', '腾讯会议bug', '笔记软件对比',
        '学习app推荐', '作业帮体验', '网课软件',
    ],
}

# 痛点关键词（用于筛选有价值的内容）
PAIN_KEYWORDS = [
    '难用', '卡顿', 'bug', '崩溃', '闪退', '吐槽',
    '太慢', '占内存', '耗电', '广告多', '收费',
    '找不到', '不好用', '垃圾', '差评', '失望',
    '建议', '希望', '为什么', '怎么', '求助',
    '踩雷', '避坑', '真实体验', '使用感受',
]


def generate_search_id() -> str:
    """生成搜索 ID"""
    return hashlib.md5(str(time.time()).encode()).hexdigest()[:16]


def fetch_xiaohongshu_search(keyword: str) -> List[Dict]:
    """
    从小红书搜索获取笔记
    
    注意：小红书有严格的反爬机制，这里使用移动端 API
    实际使用时可能需要配合代理或 cookie
    """
    # 小红书移动端搜索 API（需要签名，这里简化处理）
    # 实际生产环境建议使用官方开放平台或第三方服务
    
    encoded_keyword = urllib.parse.quote(keyword)
    
    # 备选方案：通过公开页面抓取
    # 这里使用模拟数据结构，实际需要根据真实 API 调整
    
    try:
        # 方案1: 尝试访问移动端搜索页面
        url = f'https://www.xiaohongshu.com/search_result?keyword={encoded_keyword}'
        
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148',
            'Accept': 'text/html,application/xhtml+xml',
            'Accept-Language': 'zh-CN,zh;q=0.9',
        })
        
        with urllib.request.urlopen(req, timeout=30) as response:
            html = response.read().decode('utf-8')
        
        notes = []
        
        # 解析页面中的笔记数据
        # 小红书页面中通常有 JSON 数据块
        json_pattern = r'window\.__INITIAL_STATE__\s*=\s*({.+?})</script>'
        match = re.search(json_pattern, html, re.DOTALL)
        
        if match:
            try:
                data = json.loads(match.group(1))
                # 从数据中提取笔记列表
                note_list = data.get('search', {}).get('notes', {}).get('items', [])
                
                for item in note_list[:CONFIG['max_notes_per_keyword']]:
                    note_info = item.get('note', {}) or item
                    notes.append({
                        'id': note_info.get('id', ''),
                        'title': note_info.get('title', ''),
                        'content': note_info.get('desc', ''),
                        'author': note_info.get('user', {}).get('nickname', ''),
                        'likes': note_info.get('liked_count', 0),
                        'comments': note_info.get('comments_count', 0),
                        'keyword': keyword,
                        'source': '小红书',
                        'source_url': f"https://www.xiaohongshu.com/explore/{note_info.get('id', '')}",
                        'crawl_date': datetime.now().isoformat(),
                    })
            except json.JSONDecodeError:
                pass
        
        return notes
        
    except urllib.error.HTTPError as e:
        if e.code == 403:
            print(f"  ⚠️ 请求被拒绝（需要登录或验证）: {keyword}")
        else:
            print(f"  HTTP Error {e.code} for '{keyword}'")
        return []
    except Exception as e:
        print(f"  Error fetching '{keyword}': {e}")
        return []


def is_pain_related(text: str) -> bool:
    """判断内容是否与痛点相关"""
    text_lower = text.lower()
    return any(kw in text_lower for kw in PAIN_KEYWORDS)


def crawl_category(category_id: str) -> Dict[str, Any]:
    """采集单个类目"""
    
    print(f"\n{'='*50}")
    print(f"小红书采集: {category_id}")
    print(f"{'='*50}")
    
    if category_id not in CATEGORY_KEYWORDS:
        return {'category': category_id, 'notes': [], 'error': 'Unknown category'}
    
    all_notes = []
    keywords_crawled = []
    seen_ids = set()
    
    for keyword in CATEGORY_KEYWORDS[category_id]:
        print(f"\n🔍 搜索: '{keyword}'")
        
        notes = fetch_xiaohongshu_search(keyword)
        
        # 去重 + 筛选痛点相关内容
        unique_notes = []
        for note in notes:
            note_id = note.get('id')
            if note_id and note_id not in seen_ids:
                seen_ids.add(note_id)
                # 检查是否包含痛点关键词
                full_text = f"{note.get('title', '')} {note.get('content', '')}"
                if is_pain_related(full_text):
                    note['pain_related'] = True
                    unique_notes.append(note)
        
        all_notes.extend(unique_notes)
        keywords_crawled.append({
            'keyword': keyword,
            'note_count': len(unique_notes),
        })
        
        print(f"  ✓ '{keyword}': {len(unique_notes)} 条相关笔记")
        time.sleep(CONFIG['delay_seconds'])
    
    return {
        'category': category_id,
        'crawl_date': datetime.now().isoformat(),
        'keywords_crawled': keywords_crawled,
        'total_notes': len(all_notes),
        'notes': all_notes,
        'source': '小红书',
        'note': '公开笔记采集，已筛选痛点相关内容',
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
    print("小红书用户评价采集器")
    print("数据源: 小红书公开笔记")
    print(f"目标类目: {', '.join(target_categories)}")
    print("=" * 60)
    print("\n⚠️ 注意: 小红书有反爬机制，部分请求可能失败")
    print("建议配合代理使用或降低采集频率")
    
    results = {}
    
    for cat_id in target_categories:
        data = crawl_category(cat_id)
        filepath = save_results(cat_id, data)
        results[cat_id] = {
            'file': filepath,
            'total': data['total_notes'],
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
