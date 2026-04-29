#!/usr/bin/env python3
"""
Step 6: 本地 embedding + 层次聚类
================================================================
输入: data/processed/{category}_atoms.json  (Step 5 产出的需求原子)
输出: data/processed/{category}_clusters.json

流程:
  1. 加载所有 atoms
  2. 用 BGE-small-zh-v1.5 对 need_statement 做 embedding
  3. AgglomerativeClustering (余弦距离，阈值可调) 聚类
  4. 每个簇输出: cluster_id, size, member_atom_ids, centroid 附近的代表性原子

为了后续 Step 7（LLM 起簇标题）用，这里只做原子级别聚类。
"""

import os
import sys
import json
import time
import argparse
import numpy as np
from pathlib import Path
from datetime import datetime, timezone
from collections import Counter, defaultdict

ROOT = Path(__file__).parent.parent
PROC_DIR = ROOT / "data/processed"


def embed_atoms(atoms, model_name="BAAI/bge-small-zh-v1.5"):
    """对每个 atom 的 need_statement 做 embedding。"""
    from sentence_transformers import SentenceTransformer
    print(f"[Step 6] 加载 embedding 模型: {model_name}")
    t0 = time.time()
    model = SentenceTransformer(model_name)
    print(f"  模型加载用时 {time.time()-t0:.1f}s")

    texts = []
    for a in atoms:
        # 把 product + feature + need_statement 拼起来，向量包含语境
        t = f"[{a.get('product','')}] {a.get('feature','')}: {a.get('need_statement','')}"
        texts.append(t)

    print(f"  对 {len(texts)} 条原子做 embedding...")
    t0 = time.time()
    emb = model.encode(texts, batch_size=64, normalize_embeddings=True, show_progress_bar=False)
    print(f"  embedding 完成 用时 {time.time()-t0:.1f}s  维度 {emb.shape}")
    return emb


def cluster_atoms(embeddings, distance_threshold=0.35, min_cluster_size=2):
    """层次聚类，返回 labels 数组。distance=1-cosine_sim。"""
    from sklearn.cluster import AgglomerativeClustering
    print(f"[Step 6] 层次聚类 (distance_threshold={distance_threshold})")
    # normalize 后的向量，欧式距离 ≈ sqrt(2*(1-cos))
    # 直接用 cosine metric + average linkage 更直观
    clustering = AgglomerativeClustering(
        n_clusters=None,
        distance_threshold=distance_threshold,
        metric="cosine",
        linkage="average",
    )
    t0 = time.time()
    labels = clustering.fit_predict(embeddings)
    print(f"  聚类完成 用时 {time.time()-t0:.1f}s  共 {len(set(labels))} 个簇")
    return labels


def select_representatives(atoms, indices, embeddings, n=5):
    """从簇中选出与簇中心最接近的 n 个原子作为代表。"""
    if len(indices) <= n:
        return indices
    cluster_emb = embeddings[indices]
    centroid = cluster_emb.mean(axis=0)
    # normalize
    centroid = centroid / (np.linalg.norm(centroid) + 1e-9)
    sims = cluster_emb @ centroid
    order = np.argsort(-sims)
    return [indices[i] for i in order[:n]]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--category", required=True, choices=["wechat", "social", "ai", "more"])
    ap.add_argument("--distance-threshold", type=float, default=0.35,
                    help="距离阈值，越小簇越细。默认 0.35（对应 cos sim >= 0.65）")
    ap.add_argument("--min-size", type=int, default=2,
                    help="保留的最小簇规模（小于这个数的簇标记为 noise）")
    ap.add_argument("--model", default="BAAI/bge-small-zh-v1.5",
                    help="sentence-transformers 模型名")
    ap.add_argument("--use-sample", action="store_true",
                    help="使用 sample20 文件（试点用）")
    args = ap.parse_args()

    # 输入文件
    suffix = "_sample20" if args.use_sample else ""
    in_path = PROC_DIR / f"{args.category}_atoms{suffix}.json"
    if not in_path.exists():
        print(f"❌ 输入文件不存在: {in_path}")
        sys.exit(1)
    with open(in_path, encoding="utf-8") as f:
        data = json.load(f)
    atoms = data.get("atoms", [])
    print(f"[Step 6] 加载 {len(atoms)} 条原子 from {in_path.name}")
    if len(atoms) < 2:
        print("❌ 原子数不足，无法聚类")
        sys.exit(1)

    # Embedding
    emb = embed_atoms(atoms, args.model)

    # 聚类
    labels = cluster_atoms(emb, args.distance_threshold, args.min_size)

    # 组装簇
    clusters_map = defaultdict(list)
    for i, lb in enumerate(labels):
        clusters_map[int(lb)].append(i)

    # 过滤小簇（标记为 noise 单独一组）
    valid_clusters = []
    noise_atoms = []
    for lb, idxs in clusters_map.items():
        if len(idxs) >= args.min_size:
            valid_clusters.append((lb, idxs))
        else:
            noise_atoms.extend(idxs)

    # 按簇大小排序
    valid_clusters.sort(key=lambda x: -len(x[1]))

    # 输出
    clusters_out = []
    for rank, (orig_label, idxs) in enumerate(valid_clusters, 1):
        reps_idx = select_representatives(atoms, idxs, emb, n=5)
        members = [atoms[i] for i in idxs]
        reps = [atoms[i] for i in reps_idx]

        # 统计簇的多维元数据
        src_dist = Counter(m['source'] for m in members)
        product_dist = Counter(m.get('product') or m.get('source_product','') for m in members)
        sent_dist = Counter(m['sentiment'] for m in members)
        type_dist = Counter(m['type'] for m in members)
        pers_dist = Counter(m['perspective'] for m in members)
        avg_weight = sum(m.get('weight_signal', 0) for m in members) / len(members)

        clusters_out.append({
            "cluster_id": f"{args.category}_c{rank:03d}",
            "size": len(idxs),
            "representative_statements": [r['need_statement'] for r in reps],
            "representative_atoms": [r['atom_id'] for r in reps],
            "member_atom_ids": [atoms[i]['atom_id'] for i in idxs],
            "source_distribution": dict(src_dist),
            "product_distribution": dict(product_dist.most_common(10)),
            "sentiment_distribution": dict(sent_dist),
            "type_distribution": dict(type_dist),
            "perspective_distribution": dict(pers_dist),
            "avg_weight_signal": round(avg_weight, 2),
        })

    # Noise 存档（不参与后续聚合，但保留用于调试）
    noise_out = [{
        "atom_id": atoms[i]['atom_id'],
        "need_statement": atoms[i]['need_statement'],
        "product": atoms[i].get('product', ''),
        "source": atoms[i]['source'],
    } for i in noise_atoms]

    # 写入
    out_path = PROC_DIR / f"{args.category}_clusters{suffix}.json"
    out_data = {
        "category": args.category,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "input_atoms": len(atoms),
        "distance_threshold": args.distance_threshold,
        "min_cluster_size": args.min_size,
        "cluster_count": len(clusters_out),
        "noise_count": len(noise_out),
        "clusters": clusters_out,
        "noise_atoms": noise_out,
    }
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out_data, f, ensure_ascii=False, indent=2)

    print(f"\n✅ 写入 {out_path}")
    print(f"   原子 {len(atoms)} → 有效簇 {len(clusters_out)}（噪声 {len(noise_out)}）")
    print(f"\n   Top 10 最大簇:")
    for c in clusters_out[:10]:
        preview = c['representative_statements'][0][:50]
        print(f"     [{c['cluster_id']}] size={c['size']}  {preview}...")


if __name__ == "__main__":
    main()
