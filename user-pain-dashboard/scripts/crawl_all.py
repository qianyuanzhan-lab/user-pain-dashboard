#!/usr/bin/env python3
"""
主采集入口
运行完整的数据采集 + 分析流程

流程：
1. App Store 采集
2. Google Play 采集
3. 黑猫投诉采集
4. 痛点分析与聚类
5. 同步统计数据到前端
"""

import sys
import os
from datetime import datetime

# 添加脚本目录到路径
sys.path.insert(0, os.path.dirname(__file__))

from crawl_appstore import main as crawl_appstore
from crawl_googleplay import main as crawl_googleplay
from crawl_heimao import main as crawl_heimao
from analyze_data import main as analyze_data
from sync_crawl_stats import main as sync_stats


def run_full_crawl(category: str = None):
    """
    运行完整采集流程
    
    Args:
        category: 指定类目（wechat/social/ai/more），None 表示全部
    """
    categories = [category] if category else None
    
    print("=" * 70)
    print(f"用户痛点数据采集 - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 70)
    
    results = {
        'start_time': datetime.now().isoformat(),
        'category': category or 'all',
        'stages': {},
    }
    
    # Stage 1: App Store
    print("\n" + "=" * 70)
    print("Stage 1/5: App Store 采集")
    print("=" * 70)
    try:
        appstore_results = crawl_appstore(categories)
        results['stages']['appstore'] = appstore_results
    except Exception as e:
        print(f"App Store 采集失败: {e}")
        results['stages']['appstore'] = {'error': str(e)}
    
    # Stage 2: Google Play
    print("\n" + "=" * 70)
    print("Stage 2/5: Google Play 采集")
    print("=" * 70)
    try:
        googleplay_results = crawl_googleplay(categories)
        results['stages']['googleplay'] = googleplay_results
    except Exception as e:
        print(f"Google Play 采集失败: {e}")
        results['stages']['googleplay'] = {'error': str(e)}
    
    # Stage 3: 黑猫投诉
    print("\n" + "=" * 70)
    print("Stage 3/5: 黑猫投诉采集")
    print("=" * 70)
    try:
        heimao_results = crawl_heimao(categories)
        results['stages']['heimao'] = heimao_results
    except Exception as e:
        print(f"黑猫投诉采集失败: {e}")
        results['stages']['heimao'] = {'error': str(e)}
    
    # Stage 4: 数据分析
    print("\n" + "=" * 70)
    print("Stage 4/5: 痛点分析与聚类")
    print("=" * 70)
    try:
        analysis_results = analyze_data(categories)
        results['stages']['analysis'] = analysis_results
    except Exception as e:
        print(f"数据分析失败: {e}")
        results['stages']['analysis'] = {'error': str(e)}
    
    results['end_time'] = datetime.now().isoformat()
    
    # Stage 5: 同步统计数据
    print("\n" + "=" * 70)
    print("Stage 5/5: 同步统计数据到前端")
    print("=" * 70)
    try:
        sync_results = sync_stats()
        results['stages']['sync'] = {
            'total_reviews': sync_results.get('totalReviews', 0),
            'channels': len(sync_results.get('channels', [])),
        }
    except Exception as e:
        print(f"统计同步失败: {e}")
        results['stages']['sync'] = {'error': str(e)}
    
    # 汇总
    print("\n" + "=" * 70)
    print("采集完成汇总")
    print("=" * 70)
    print(f"类目: {category or '全部'}")
    print(f"耗时: {results['end_time'][:19]} - {results['start_time'][:19]}")
    
    for stage, data in results['stages'].items():
        if 'error' in data:
            print(f"  {stage}: ❌ {data['error']}")
        else:
            total = sum(v.get('total', 0) for v in data.values() if isinstance(v, dict))
            print(f"  {stage}: ✓ {total} 条")
    
    return results


def run_single_category(category: str):
    """采集单个类目"""
    if category not in ['wechat', 'social', 'ai', 'more']:
        print(f"未知类目: {category}")
        print("可选类目: wechat, social, ai, more")
        return
    
    return run_full_crawl(category)


if __name__ == '__main__':
    if len(sys.argv) > 1:
        category = sys.argv[1]
        run_single_category(category)
    else:
        run_full_crawl()
