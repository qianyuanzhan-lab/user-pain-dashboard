#!/usr/bin/env python3
"""
全赛道一键执行（Step 1 → Step 9）
================================================================
等待 Step 5 完成后自动走 Step 6-9。

用法:
  python3 run_pipeline.py --category ai
  python3 run_pipeline.py --category all --skip wechat
"""

import argparse
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).parent.parent


def run(cmd, desc):
    print(f"\n{'='*70}")
    print(f"▶ {desc}")
    print(f"  cmd: {' '.join(cmd)}")
    print(f"{'='*70}", flush=True)
    t0 = time.time()
    proc = subprocess.run(cmd, cwd=ROOT)
    elapsed = time.time() - t0
    if proc.returncode != 0:
        print(f"❌ {desc} 失败 (exit {proc.returncode})")
        sys.exit(proc.returncode)
    print(f"✅ {desc} 完成 用时 {elapsed:.1f}s")


def pipeline(category):
    scripts = ROOT / "scripts"
    run(["python3", str(scripts / "pipeline_step1_4.py"), "--category", category],
        f"[{category}] Step 1-4 清洗筛选")
    run(["python3", str(scripts / "pipeline_step5_atoms.py"), "--category", category],
        f"[{category}] Step 5 DeepSeek 抽需求原子")
    run(["python3", str(scripts / "pipeline_step6_cluster.py"), "--category", category,
         "--distance-threshold", "0.42"],
        f"[{category}] Step 6 本地 embedding 聚类")
    run(["python3", str(scripts / "pipeline_step7_label.py"), "--category", category],
        f"[{category}] Step 7 LLM 打标")
    run(["python3", str(scripts / "pipeline_step8_merge.py"), "--category", category,
         "--sim", "0.75"],
        f"[{category}] Step 8 二级合并")
    run(["python3", str(scripts / "pipeline_step8_5_dedup.py"), "--category", category],
        f"[{category}] Step 8.5 全局去重")
    run(["python3", str(scripts / "pipeline_step9_dashboard.py"), "--category", category],
        f"[{category}] Step 9 生成 Dashboard JSON")
    print(f"\n🎉 [{category}] 全部完成")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--category", required=True, choices=["wechat", "social", "ai", "more", "all"])
    ap.add_argument("--skip", nargs="*", default=[], help="跳过的赛道列表")
    args = ap.parse_args()
    cats = ["wechat", "social", "ai", "more"] if args.category == "all" else [args.category]
    cats = [c for c in cats if c not in args.skip]
    for c in cats:
        pipeline(c)


if __name__ == "__main__":
    main()
