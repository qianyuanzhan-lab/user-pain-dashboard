#!/usr/bin/env python3
"""
用户痛点数据采集 - 主入口
整合所有数据源的完整采集流程

数据源清单：
1. App Store - Apple 官方评论 (RSS Feed)
2. Google Play - Android 应用评论
3. 酷安 - 国内安卓应用社区
4. 黑猫投诉 - 用户投诉平台
5. 知乎 - 深度讨论
6. 豆瓣 - 小组讨论
7. 小红书 - 用户分享笔记
8. V2EX - 技术社区
9. 微博 - 热点话题
10. Hacker News - 国际科技社区

使用方法：
  python crawl_all_sources.py           # 采集所有类目
  python crawl_all_sources.py wechat    # 只采集微信类目
  python crawl_all_sources.py --fast    # 快速模式（只用稳定数据源）
"""

import sys
import os
import json
from datetime import datetime
from typing import List, Dict, Optional, Any

# 添加脚本目录到路径
sys.path.insert(0, os.path.dirname(__file__))


def import_crawlers():
    """动态导入所有采集器"""
    crawlers = {}
    
    # 稳定数据源（官方 API 或成熟接口）
    stable_sources = [
        ('appstore', 'crawl_appstore', 'App Store'),
        ('v2ex', 'crawl_v2ex', 'V2EX'),
        ('hackernews', 'crawl_hackernews', 'Hacker News'),
    ]
    
    # 需要特殊处理的数据源（可能有反爬机制）
    advanced_sources = [
        ('googleplay', 'crawl_googleplay', 'Google Play'),
        ('heimao', 'crawl_heimao', '黑猫投诉'),
        ('coolapk', 'crawl_coolapk', '酷安'),
        ('zhihu', 'crawl_zhihu', '知乎'),
        ('douban', 'crawl_douban', '豆瓣'),
        ('xiaohongshu', 'crawl_xiaohongshu', '小红书'),
        ('weibo', 'crawl_weibo', '微博'),
    ]
    
    all_sources = stable_sources + advanced_sources
    
    for source_id, module_name, display_name in all_sources:
        try:
            module = __import__(module_name)
            crawlers[source_id] = {
                'module': module,
                'name': display_name,
                'stable': source_id in [s[0] for s in stable_sources],
            }
        except ImportError as e:
            print(f"⚠️ 无法导入 {display_name} 采集器: {e}")
    
    return crawlers


def run_crawler(crawler_info: Dict, categories: Optional[List[str]] = None) -> Dict:
    """运行单个采集器"""
    try:
        module = crawler_info['module']
        if hasattr(module, 'main'):
            return module.main(categories)
        else:
            print(f"  ⚠️ {crawler_info['name']} 缺少 main 函数")
            return {'error': 'No main function'}
    except Exception as e:
        print(f"  ❌ {crawler_info['name']} 采集失败: {e}")
        return {'error': str(e)}


def run_full_crawl(
    categories: Optional[List[str]] = None,
    fast_mode: bool = False,
    sources: Optional[List[str]] = None,
):
    """
    运行完整采集流程
    
    Args:
        categories: 指定类目（wechat/social/ai/more），None 表示全部
        fast_mode: 快速模式，只使用稳定数据源
        sources: 指定数据源列表，None 表示全部
    """
    crawlers = import_crawlers()
    
    if not crawlers:
        print("❌ 没有可用的采集器")
        return {}
    
    print("=" * 70)
    print(f"用户痛点数据采集 - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 70)
    
    if categories:
        print(f"目标类目: {', '.join(categories)}")
    else:
        print("目标类目: 全部 (wechat, social, ai, more)")
    
    if fast_mode:
        print("模式: 快速模式（仅稳定数据源）")
        crawlers = {k: v for k, v in crawlers.items() if v['stable']}
    
    if sources:
        print(f"数据源: {', '.join(sources)}")
        crawlers = {k: v for k, v in crawlers.items() if k in sources}
    
    print(f"可用数据源: {', '.join(c['name'] for c in crawlers.values())}")
    print("=" * 70)
    
    results = {
        'start_time': datetime.now().isoformat(),
        'categories': categories or ['wechat', 'social', 'ai', 'more'],
        'fast_mode': fast_mode,
        'sources': {},
    }
    
    total_items = 0
    
    for idx, (source_id, crawler_info) in enumerate(crawlers.items(), 1):
        print(f"\n{'='*70}")
        print(f"[{idx}/{len(crawlers)}] {crawler_info['name']}")
        print("=" * 70)
        
        source_result = run_crawler(crawler_info, categories)
        
        # 统计
        source_total = 0
        if isinstance(source_result, dict):
            for cat_id, cat_data in source_result.items():
                if isinstance(cat_data, dict) and 'total' in cat_data:
                    source_total += cat_data['total']
        
        results['sources'][source_id] = {
            'name': crawler_info['name'],
            'result': source_result,
            'total_items': source_total,
        }
        
        total_items += source_total
        print(f"\n✓ {crawler_info['name']} 完成: {source_total} 条数据")
    
    results['end_time'] = datetime.now().isoformat()
    results['total_items'] = total_items
    
    # 保存汇总结果
    output_dir = os.path.join(os.path.dirname(__file__), '../data/raw')
    os.makedirs(output_dir, exist_ok=True)
    
    summary_file = os.path.join(output_dir, f"crawl_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2, default=str)
    
    # 打印汇总
    print("\n" + "=" * 70)
    print("采集完成汇总")
    print("=" * 70)
    print(f"总耗时: {results['start_time'][:19]} → {results['end_time'][:19]}")
    print(f"总数据量: {total_items} 条")
    print("\n各数据源:")
    
    for source_id, source_data in results['sources'].items():
        status = "✓" if 'error' not in source_data.get('result', {}) else "❌"
        print(f"  {status} {source_data['name']}: {source_data['total_items']} 条")
    
    print(f"\n汇总文件: {summary_file}")
    print("=" * 70)
    
    return results


def print_help():
    """打印帮助信息"""
    print("""
用户痛点数据采集器
==================

用法:
  python crawl_all_sources.py [选项] [类目...]

类目:
  wechat    微信相关应用
  social    社交/社区应用
  ai        AI/智能助手应用
  more      办公/效率/其他应用

选项:
  --fast           快速模式，只使用稳定数据源（App Store, V2EX, Hacker News）
  --source=xxx     指定单个数据源（appstore, coolapk, zhihu, douban, xiaohongshu, weibo, v2ex, heimao, hackernews）
  --help, -h       显示帮助

示例:
  python crawl_all_sources.py                    # 采集所有类目、所有数据源
  python crawl_all_sources.py wechat             # 只采集微信类目
  python crawl_all_sources.py --fast wechat      # 快速模式采集微信
  python crawl_all_sources.py --source=zhihu     # 只使用知乎数据源
  python crawl_all_sources.py social ai          # 采集社交和AI类目

数据源清单:
  稳定数据源（推荐）:
    - App Store    Apple 官方 RSS Feed，完全稳定
    - V2EX         公开 API，无需认证
    - Hacker News  公开 API，无需认证

  高级数据源（可能需要代理或有频率限制）:
    - Google Play  需要代理访问
    - 酷安         国内安卓社区，评论质量高
    - 知乎         深度讨论，有反爬限制
    - 豆瓣         小组讨论，有反爬限制
    - 小红书       用户分享，有较强反爬
    - 微博         热点话题，有反爬限制
    - 黑猫投诉     投诉平台，需解析HTML

输出:
  数据保存到 data/raw/<source>/<category>_YYYYMMDD.json
  汇总报告保存到 data/raw/crawl_summary_YYYYMMDD_HHMMSS.json
""")


def main():
    """主函数"""
    args = sys.argv[1:]
    
    # 解析参数
    if '--help' in args or '-h' in args:
        print_help()
        return
    
    fast_mode = '--fast' in args
    if fast_mode:
        args.remove('--fast')
    
    sources = None
    for arg in args[:]:
        if arg.startswith('--source='):
            source = arg.split('=')[1]
            sources = [source]
            args.remove(arg)
    
    # 剩余参数作为类目
    categories = args if args else None
    
    # 运行采集
    run_full_crawl(
        categories=categories,
        fast_mode=fast_mode,
        sources=sources,
    )


if __name__ == '__main__':
    main()
