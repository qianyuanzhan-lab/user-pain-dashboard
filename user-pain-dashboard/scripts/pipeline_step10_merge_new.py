#!/usr/bin/env python3
"""
Step 10: 增量合并本周新需求到主数据中
================================================================
流程：
  1. 读取 data/processed/{cat}_ai_opportunities_consolidated.json（旧主数据）
  2. 读取 data/processed/incremental/{cat}_new_demands_{date}.json（本周新跑的）
  3. 对新需求 vs 旧需求做 embedding 相似度对比：
     - 如果有高相似的旧需求（>0.85）→ 并入旧，只更新计数和证据样本
     - 如果没有 → 作为新需求插入，打上 is_new=true, discovered_at=today
  4. 老需求的 is_new 状态：超过 7 天自动清除
  5. 写回主数据

用法:
  python3 pipeline_step10_merge_new.py --category ai
  python3 pipeline_step10_merge_new.py --category all
"""

import argparse
import json
import numpy as np
import shutil
from datetime import datetime, timezone, timedelta
from pathlib import Path

ROOT = Path(__file__).parent.parent
PROC_DIR = ROOT / "data/processed"
INC_DIR = PROC_DIR / "incremental"
INC_DIR.mkdir(exist_ok=True)


def compute_embeddings(texts, model_name="BAAI/bge-small-zh-v1.5"):
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer(model_name)
    return model.encode(texts, batch_size=64, normalize_embeddings=True, show_progress_bar=False)


def merge_incremental(category, new_expire_days=7):
    """合并新需求到主数据"""
    main_path = PROC_DIR / f"{category}_ai_opportunities_consolidated.json"
    new_path = INC_DIR / f"{category}_new_merged_demands.json"
    if not main_path.exists():
        print(f"❌ 主数据不存在: {main_path}")
        return
    if not new_path.exists():
        print(f"⚠️ 无新数据: {new_path}，跳过")
        return

    with open(main_path, encoding="utf-8") as f:
        main = json.load(f)
    with open(new_path, encoding="utf-8") as f:
        new_raw = json.load(f)

    today_iso = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    expire_cutoff = datetime.now(timezone.utc) - timedelta(days=new_expire_days)

    # 1. 清理主数据里"过期的 is_new"
    for op in main["ai_opportunities"]:
        disc_at = op.get("discovered_at")
        if op.get("is_new") and disc_at:
            try:
                d = datetime.fromisoformat(disc_at).replace(tzinfo=timezone.utc)
                if d < expire_cutoff:
                    op["is_new"] = False  # 超 7 天，清除 new 标记
            except Exception:
                op["is_new"] = False

    # 2. 对新需求做相似度匹配
    new_demands = new_raw.get("demands", [])
    main_ops = main["ai_opportunities"]

    if not new_demands:
        print(f"新需求为空，跳过")
        return

    # Embedding
    print(f"[增量合并] 新 {len(new_demands)} 需求 vs 主 {len(main_ops)} 需求")
    new_texts = [f"{d.get('title','')} | {d.get('description','')}" for d in new_demands]
    main_texts = [f"{o.get('title','')} | {o.get('description','')}" for o in main_ops]
    new_emb = compute_embeddings(new_texts)
    main_emb = compute_embeddings(main_texts)

    sim = new_emb @ main_emb.T   # (n_new, n_main)
    SIM_THRESHOLD = 0.85

    added = 0
    merged_to_existing = 0

    for i, nd in enumerate(new_demands):
        best_j = int(np.argmax(sim[i]))
        best_sim = float(sim[i][best_j])

        if best_sim >= SIM_THRESHOLD:
            # 并入旧需求 - 只增加 mention_count 和 evidence_samples
            existing = main_ops[best_j]
            existing["mention_count"] = (existing.get("mention_count", 0)
                                         + nd.get("size", 0))
            # 简化：不动 evidence_samples 避免重复（如果要精细合并得去重）
            existing["last_updated_at"] = today_iso
            merged_to_existing += 1
        else:
            # 新增一个需求点
            new_opp = {
                "id": f"{category}_demand_new_{today_iso}_{i}",
                "title": nd.get("title", ""),
                "description": nd.get("description", ""),
                "user_pain_summary": nd.get("description", ""),
                "ai_intervention_type": nd.get("ai_intervention_type", ""),
                "ai_description": nd.get("ai_description", ""),
                "ai_keywords": nd.get("ai_keywords", []),
                "ai_score": nd.get("ai_score", 5),
                "demand_type": nd.get("demand_type", ""),
                "demand_tier": nd.get("demand_tier", 2),
                "priority": "P1",   # 新增默认 P1
                "mention_count": nd.get("size", 0),
                "product_breakdown": nd.get("product_distribution", {}),
                "source_stats": {
                    "products_mentioned": list(nd.get("product_distribution", {}).keys())[:10],
                    "sources": list(nd.get("source_distribution", {}).keys()),
                    "exact_match_count": nd.get("size", 0),
                    "source_breakdown": nd.get("source_distribution", {}),
                },
                "evidence_samples": [],  # 简化：实际要从 atoms/candidates 里填
                "is_new": True,
                "discovered_at": today_iso,
            }
            main_ops.append(new_opp)
            added += 1

    main["ai_opportunities"] = main_ops
    main["last_incremental_at"] = today_iso

    # 备份旧数据
    backup = main_path.with_suffix(f".backup_{today_iso}.json")
    shutil.copy(main_path, backup)

    with open(main_path, "w", encoding="utf-8") as f:
        json.dump(main, f, ensure_ascii=False, indent=2)

    print(f"✅ {category} 合并完成")
    print(f"   新增需求: {added}")
    print(f"   并入旧需求: {merged_to_existing}")
    print(f"   主数据现共: {len(main_ops)} 个需求")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--category", default="all",
                    choices=["all", "wechat", "social", "ai", "more"])
    ap.add_argument("--new-expire-days", type=int, default=7)
    args = ap.parse_args()
    cats = ["wechat", "social", "ai", "more"] if args.category == "all" else [args.category]
    for c in cats:
        merge_incremental(c, args.new_expire_days)


if __name__ == "__main__":
    main()
