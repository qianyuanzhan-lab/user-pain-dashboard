#!/usr/bin/env python3
"""
酷安应用评论采集器
数据源：酷安应用市场

酷安是国内最大的安卓应用社区之一：
- 用户群体：科技爱好者、极客
- 评论特点：详细、专业、关注细节
- 非常适合采集深度使用反馈
"""

import json
import time
import os
import urllib.request
import urllib.error
import urllib.parse
import hashlib
from datetime import datetime
from typing import List, Dict, Any, Optional

# 采集配置
CONFIG = {
    'output_dir': '../data/raw/coolapk',
    'delay_seconds': 2,
    'max_comments_per_app': 50,
}

# 应用配置（按类目）
# 酷安使用包名(package name)来标识应用
CATEGORY_APPS = {
    'wechat': {
        'apps': [
            {'package': 'com.tencent.mm', 'name': '微信'},
            {'package': 'com.tencent.mobileqq', 'name': 'QQ'},
        ],
    },
    'social': {
        'apps': [
            {'package': 'com.xingin.xhs', 'name': '小红书'},
            {'package': 'com.sina.weibo', 'name': '微博'},
            {'package': 'cn.soulapp.android', 'name': 'Soul'},
            {'package': 'com.p1.mobile.putong', 'name': '探探'},
            {'package': 'com.immomo.momo', 'name': '陌陌'},
            {'package': 'me.jike.app', 'name': '即刻'},
        ],
    },
    'ai': {
        'apps': [
            {'package': 'com.moonshot.kimichat', 'name': 'Kimi智能助手'},
            {'package': 'com.larus.nova', 'name': '豆包'},
            {'package': 'com.alibaba.tongyi.ai', 'name': '通义千问'},
            {'package': 'com.baidu.newapp', 'name': '文心一言'},
            {'package': 'com.tencent.hunyuan', 'name': '腾讯混元'},
            {'package': 'com.deepseek.chat', 'name': 'DeepSeek'},
        ],
    },
    'more': {
        'apps': [
            {'package': 'com.ss.android.lark', 'name': '飞书'},
            {'package': 'com.alibaba.android.rimet', 'name': '钉钉'},
            {'package': 'com.tencent.wework', 'name': '企业微信'},
            {'package': 'com.tencent.wemeet.app', 'name': '腾讯会议'},
            {'package': 'com.ticktick.task', 'name': '滴答清单'},
            {'package': 'com.yinxiang', 'name': '印象笔记'},
        ],
    },
}


def generate_device_id() -> str:
    """生成设备 ID"""
    return hashlib.md5(str(time.time()).encode()).hexdigest()


def fetch_coolapk_comments(package: str, app_name: str) -> List[Dict]:
    """
    获取酷安应用评论
    
    酷安 API 需要特定的请求头和签名
    这里使用简化版本，实际可能需要更复杂的签名算法
    """
    # 酷安 v6 API
    url = f'https://api.coolapk.com/v6/apk/commentList'
    params = {
        'id': package,
        'page': 1,
        'listType': 'dateline',  # 按时间排序
        'firstItem': 0,
        'lastItem': 0,
    }
    full_url = f"{url}?{urllib.parse.urlencode(params)}"
    
    device_id = generate_device_id()
    
    try:
        req = urllib.request.Request(full_url, headers={
            'User-Agent': 'Dalvik/2.1.0 (Linux; U; Android 12; Pixel 6 Build/SD1A.210817.019) (#Build; google; Pixel 6; SD1A.210817.019; 12) +CoolMarket/12.4.2-2208241-universal',
            'X-App-Id': 'com.coolapk.market',
            'X-Requested-With': 'XMLHttpRequest',
            'X-App-Version': '12.4.2',
            'X-App-Code': '2208241',
            'X-Api-Version': '12',
            'X-App-Device': device_id,
            'X-Dark-Mode': '0',
            'X-App-Channel': 'coolapk',
            'X-App-Mode': 'universal',
            'Accept': 'application/json',
        })
        
        with urllib.request.urlopen(req, timeout=30) as response:
            data = json.loads(response.read().decode('utf-8'))
        
        comments = []
        
        for item in data.get('data', []):
            # 跳过非评论项
            if item.get('entityType') != 'feed':
                continue
            
            message = item.get('message', '')
            if not message or len(message) < 10:
                continue
            
            comments.append({
                'id': str(item.get('id', '')),
                'package': package,
                'app_name': app_name,
                'content': message,
                'author': item.get('username', ''),
                'user_avatar': item.get('userAvatar', ''),
                'like_count': item.get('likenum', 0),
                'reply_count': item.get('replynum', 0),
                'rating': item.get('score', 0),  # 评分
                'device': item.get('device_title', ''),  # 用户设备
                'date': item.get('dateline', ''),
                'source': '酷安',
                'source_url': f"https://www.coolapk.com/apk/{package}",
                'crawl_date': datetime.now().isoformat(),
            })
        
        return comments
        
    except urllib.error.HTTPError as e:
        print(f"  HTTP Error {e.code}: {app_name}")
        return []
    except Exception as e:
        print(f"  Error fetching {app_name}: {e}")
        return []


def fetch_coolapk_app_info(package: str) -> Optional[Dict]:
    """
    获取应用详情
    """
    url = f'https://api.coolapk.com/v6/apk/detail?id={package}'
    
    try:
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Dalvik/2.1.0 (Linux; U; Android 12)',
            'Accept': 'application/json',
        })
        
        with urllib.request.urlopen(req, timeout=30) as response:
            data = json.loads(response.read().decode('utf-8'))
        
        app_data = data.get('data', {})
        return {
            'title': app_data.get('title', ''),
            'version': app_data.get('apkversionname', ''),
            'score': app_data.get('score', 0),
            'comment_count': app_data.get('commentnum', 0),
            'download_count': app_data.get('downnum', 0),
        }
        
    except Exception as e:
        return None


def crawl_category(category_id: str) -> Dict[str, Any]:
    """采集单个类目"""
    
    print(f"\n{'='*50}")
    print(f"酷安采集: {category_id}")
    print(f"{'='*50}")
    
    if category_id not in CATEGORY_APPS:
        return {'category': category_id, 'comments': [], 'error': 'Unknown category'}
    
    config = CATEGORY_APPS[category_id]
    all_comments = []
    apps_crawled = []
    
    for app in config.get('apps', []):
        package = app['package']
        name = app['name']
        
        print(f"\n📱 应用: {name} ({package})")
        
        # 获取应用信息
        app_info = fetch_coolapk_app_info(package)
        if app_info:
            print(f"  📊 评分: {app_info.get('score', 'N/A')} | 评论: {app_info.get('comment_count', 'N/A')}")
        
        # 获取评论
        comments = fetch_coolapk_comments(package, name)
        all_comments.extend(comments)
        
        apps_crawled.append({
            'package': package,
            'name': name,
            'comment_count': len(comments),
            'app_info': app_info,
        })
        
        print(f"  ✓ 获取 {len(comments)} 条评论")
        time.sleep(CONFIG['delay_seconds'])
    
    return {
        'category': category_id,
        'crawl_date': datetime.now().isoformat(),
        'apps_crawled': apps_crawled,
        'total_comments': len(all_comments),
        'comments': all_comments,
        'source': '酷安',
        'note': '安卓应用市场，用户群体偏极客',
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
    target_categories = categories or list(CATEGORY_APPS.keys())
    
    print("=" * 60)
    print("酷安应用评论采集器")
    print("数据源: 酷安应用市场")
    print(f"目标类目: {', '.join(target_categories)}")
    print("=" * 60)
    print("\n💡 酷安特点: 用户群体偏极客，评论质量高")
    
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
        print(f"  {cat_id}: {info['total']} 条")
        total += info['total']
    print(f"  总计: {total} 条")
    print("=" * 60)
    
    return results


if __name__ == '__main__':
    import sys
    categories = sys.argv[1:] if len(sys.argv) > 1 else None
    main(categories)
