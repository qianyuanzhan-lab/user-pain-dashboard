#!/usr/bin/env python3
"""
采集统计同步器
采集完成后运行此脚本，自动更新前端 CRAWL_STATS 数据

功能：
1. 扫描 data/raw 目录下的所有采集结果
2. 统计各渠道的评论数量
3. 计算时间范围（当天往前推 1 年）
4. 更新 src/data/dashboardData.ts 中的 CRAWL_STATS
"""

import os
import json
import glob
import re
from datetime import datetime, timedelta
from typing import Dict, List, Any


# 路径配置
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
RAW_DATA_DIR = os.path.join(PROJECT_ROOT, 'data', 'raw')
DASHBOARD_DATA_FILE = os.path.join(PROJECT_ROOT, 'src', 'data', 'dashboardData.ts')


# 数据源配置
DATA_SOURCES = {
    'appstore': {
        'name': 'App Store',
        'icon': '🍎',
        'dir': 'appstore',
        'pattern': '*.json',
    },
    'googleplay': {
        'name': 'Google Play',
        'icon': '🤖',
        'dir': 'googleplay',
        'pattern': '*.json',
    },
    'heimao': {
        'name': '黑猫投诉',
        'icon': '🐱',
        'dir': 'heimao',
        'pattern': '*.json',
    },
    'hackernews': {
        'name': 'Hacker News',
        'icon': '📰',
        'dir': 'hackernews',
        'pattern': '*.json',
    },
    'v2ex': {
        'name': 'V2EX',
        'icon': '💬',
        'dir': 'v2ex',
        'pattern': '*.json',
    },
    'reddit': {
        'name': 'Reddit',
        'icon': '🔴',
        'dir': 'reddit',
        'pattern': '*.json',
    },
    'weibo': {
        'name': '微博',
        'icon': '📱',
        'dir': 'weibo',
        'pattern': '*.json',
    },
}


def count_reviews_in_file(filepath: str) -> int:
    """统计单个 JSON 文件中的评论数量"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 尝试不同的数据结构
        if isinstance(data, list):
            return len(data)
        elif isinstance(data, dict):
            if 'reviews' in data:
                return len(data['reviews'])
            elif 'comments' in data:  # HackerNews 用 comments
                return len(data['comments'])
            elif 'complaints' in data:  # 黑猫投诉
                return len(data['complaints'])
            elif 'total_reviews' in data:
                return data['total_reviews']
            elif 'total_comments' in data:
                return data['total_comments']
            elif 'items' in data:
                return len(data['items'])
            elif 'data' in data and isinstance(data['data'], list):
                return len(data['data'])
        return 0
    except Exception as e:
        print(f"  ⚠️ 无法读取 {filepath}: {e}")
        return 0


def scan_data_source(source_id: str, source_config: Dict) -> Dict[str, Any]:
    """扫描单个数据源目录，统计评论数量"""
    source_dir = os.path.join(RAW_DATA_DIR, source_config['dir'])
    
    if not os.path.exists(source_dir):
        return {
            'source': source_config['name'],
            'icon': source_config['icon'],
            'count': 0,
            'files': 0,
            'latest_file': None,
        }
    
    pattern = os.path.join(source_dir, source_config['pattern'])
    files = glob.glob(pattern)
    
    total_count = 0
    latest_file = None
    latest_mtime = 0
    
    for filepath in files:
        count = count_reviews_in_file(filepath)
        total_count += count
        
        mtime = os.path.getmtime(filepath)
        if mtime > latest_mtime:
            latest_mtime = mtime
            latest_file = os.path.basename(filepath)
    
    return {
        'source': source_config['name'],
        'icon': source_config['icon'],
        'count': total_count,
        'files': len(files),
        'latest_file': latest_file,
        'latest_time': datetime.fromtimestamp(latest_mtime).isoformat() if latest_mtime else None,
    }


def generate_crawl_stats() -> Dict[str, Any]:
    """生成完整的采集统计数据"""
    print("📊 扫描数据目录...")
    
    channels = []
    total_count = 0
    
    for source_id, source_config in DATA_SOURCES.items():
        print(f"  扫描 {source_config['name']}...", end=' ')
        stats = scan_data_source(source_id, source_config)
        
        if stats['count'] > 0:
            # 获取地区标注
            region_map = {
                'App Store': '中国区',
                'Google Play': '全球',
                '黑猫投诉': '中国',
                'Hacker News': '全球',
                'V2EX': '中国',
                'Reddit': '全球',
                '微博': '中国',
            }
            channels.append({
                'id': source_id,
                'name': stats['source'],
                'region': region_map.get(stats['source'], '全球'),
                'count': stats['count'],
            })
            total_count += stats['count']
            print(f"✓ {stats['count']} 条 ({stats['files']} 文件)")
        else:
            print("无数据")
    
    # 时间范围：当天往前推 1 年
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)
    
    crawl_stats = {
        'totalReviews': total_count,
        'channels': channels,
        'timeRange': {
            'start': start_date.strftime('%Y-%m-%d'),
            'end': end_date.strftime('%Y-%m-%d'),
        },
        'lastUpdated': end_date.isoformat(),
    }
    
    print(f"\n📈 统计结果:")
    print(f"  总评论数: {total_count}")
    print(f"  数据渠道数: {len(channels)}")
    print(f"  时间范围: {crawl_stats['timeRange']['start']} ~ {crawl_stats['timeRange']['end']}")
    
    return crawl_stats


def format_crawl_stats_ts(stats: Dict) -> str:
    """将统计数据格式化为 TypeScript 代码"""
    channels_ts = []
    for ch in stats['channels']:
        channels_ts.append(f"    {{ id: '{ch['id']}', name: '{ch['name']}', region: '{ch['region']}', count: {ch['count']} }},")
    
    return f'''// ============================================
// 采集统计（按渠道） - 用于开屏动效
// 自动生成时间: {stats['lastUpdated']}
// ============================================
import {{ ChannelCrawlStats }} from '../types';

// 动态计算时间范围
const getChannelTimeRange = () => {{
  const endDate = new Date();
  const startDate = new Date();
  startDate.setFullYear(startDate.getFullYear() - 1);
  return {{
    start: startDate.toISOString().split('T')[0],
    end: endDate.toISOString().split('T')[0],
  }};
}};

export const CHANNEL_CRAWL_STATS: ChannelCrawlStats = {{
  totalReviews: {stats['totalReviews']},
  channels: [
{chr(10).join(channels_ts)}
  ],
  timeRange: getChannelTimeRange(),
  lastUpdated: '{stats['lastUpdated']}',
}};'''


def update_dashboard_data(stats: Dict):
    """更新 dashboardData.ts 中的 CHANNEL_CRAWL_STATS"""
    print(f"\n📝 更新 {DASHBOARD_DATA_FILE}...")
    
    if not os.path.exists(DASHBOARD_DATA_FILE):
        print(f"  ❌ 文件不存在: {DASHBOARD_DATA_FILE}")
        return False
    
    with open(DASHBOARD_DATA_FILE, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 匹配并替换 CHANNEL_CRAWL_STATS 及其前面的注释和 import
    pattern = r'// ============================================\n// 采集统计（按渠道）[\s\S]*?export const CHANNEL_CRAWL_STATS: ChannelCrawlStats = \{[\s\S]*?\};'
    new_stats_ts = format_crawl_stats_ts(stats)
    
    if re.search(pattern, content):
        new_content = re.sub(pattern, new_stats_ts, content)
        print("  ✓ 找到并替换 CHANNEL_CRAWL_STATS")
    else:
        # 如果没找到完整模式，尝试简单匹配
        simple_pattern = r'export const CHANNEL_CRAWL_STATS: ChannelCrawlStats = \{[\s\S]*?\};'
        if re.search(simple_pattern, content):
            new_content = re.sub(simple_pattern, new_stats_ts.split('export const')[1], content)
            new_content = 'export const' + new_content
            print("  ✓ 找到并替换 CHANNEL_CRAWL_STATS (简单匹配)")
        else:
            print("  ❌ 未找到 CHANNEL_CRAWL_STATS 定义")
            return False
    
    with open(DASHBOARD_DATA_FILE, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print("  ✓ 文件已更新")
    return True


def save_stats_json(stats: Dict):
    """保存统计数据为 JSON（备份）"""
    output_file = os.path.join(PROJECT_ROOT, 'data', 'crawl_stats.json')
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)
    
    print(f"  💾 备份保存到: {output_file}")


def main():
    """主函数"""
    print("=" * 60)
    print("采集统计同步器")
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # 生成统计
    stats = generate_crawl_stats()
    
    # 保存 JSON 备份
    save_stats_json(stats)
    
    # 更新 TypeScript 文件
    update_dashboard_data(stats)
    
    print("\n" + "=" * 60)
    print("✅ 同步完成")
    print("=" * 60)
    
    return stats


if __name__ == '__main__':
    main()
