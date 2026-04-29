#!/usr/bin/env python3
"""
增量抓取：只抓近 N 天的新数据
================================================================
与 crawl_all_sources.py 区别：
- 支持 --days 参数（默认 14），只抓最近 N 天
- 对抓取结果和已有 raw 数据做时间过滤合并
- 保持文件命名一致：{category}_{today}.json

用法:
  python3 crawl_incremental.py --days 14
  python3 crawl_incremental.py --days 7 --category ai
"""

import argparse
import json
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).parent.parent
SCRIPTS = ROOT / "scripts"


def run_crawler(script_name, category, days):
    """调用现有的单一源抓取脚本"""
    script = SCRIPTS / script_name
    if not script.exists():
        print(f"⚠️ {script_name} 不存在，跳过")
        return None
    cmd = ["python3", str(script), "--category", category, "--days", str(days)]
    print(f"  运行: {' '.join(cmd)}")
    try:
        subprocess.run(cmd, check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"  ❌ {script_name} 失败: {e}")
        return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=14, help="抓取最近 N 天（默认 14）")
    ap.add_argument("--category", default="all",
                    choices=["all", "wechat", "social", "ai", "more"])
    args = ap.parse_args()

    cutoff = datetime.now(timezone.utc) - timedelta(days=args.days)
    print(f"=== 增量抓取 ===")
    print(f"  时间窗口: >= {cutoff.strftime('%Y-%m-%d')}")
    print(f"  赛道: {args.category}")

    cats = ["wechat", "social", "ai", "more"] if args.category == "all" else [args.category]
    for cat in cats:
        print(f"\n--- 赛道: {cat} ---")
        # 三个数据源依次跑
        run_crawler("crawl_appstore.py", cat, args.days)
        run_crawler("crawl_googleplay.py", cat, args.days)
        run_crawler("crawl_hackernews.py", cat, args.days)

    print("\n✅ 增量抓取完成")


if __name__ == "__main__":
    main()
