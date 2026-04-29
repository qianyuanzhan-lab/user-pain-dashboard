#!/usr/bin/env python3
"""
Step 8: 二级合并相似簇
================================================================
输入: data/processed/{category}_labeled_clusters.json
输出: data/processed/{category}_merged_demands.json

流程:
  1. 用 BGE 对 (title + semantic_fingerprint + description) 做 embedding
  2. 找相似度 >= sim_threshold 的簇对（候选合并对）
  3. 用 union-find 把候选对组成连通分量
  4. 对每个候选合并组，让 LLM 判断「是/否合并」+ 给合并后的 title
  5. 输出最终需求点列表

用法:
  python3 pipeline_step8_merge.py --category social
  python3 pipeline_step8_merge.py --category social --sim 0.75
"""

import os
import sys
import json
import time
import argparse
import urllib.request
import numpy as np
from pathlib import Path
from datetime import datetime, timezone
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed

ROOT = Path(__file__).parent.parent
PROC_DIR = ROOT / "data/processed"

API_URL = "https://api.deepseek.com/v1/chat/completions"
MODEL = "deepseek-chat"
MAX_WORKERS = 10
TIMEOUT = 60
MAX_RETRY = 3

env_path = ROOT.parent / ".env"
if env_path.exists():
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")


# ============================================
# Step 8.1: 找候选合并对
# ============================================
def find_candidate_pairs(clusters, sim_threshold=0.75):
    """用 embedding 找相似度高于阈值的簇对，返回 pairs 和 embedding"""
    from sentence_transformers import SentenceTransformer
    print(f"[Step 8.1] 加载 embedding 模型...")
    model = SentenceTransformer("BAAI/bge-small-zh-v1.5")
    texts = []
    for c in clusters:
        t = f"{c.get('title','')} | {c.get('semantic_fingerprint','')} | {c.get('description','')[:120]}"
        texts.append(t)
    print(f"  对 {len(texts)} 个簇标题做 embedding...")
    emb = model.encode(texts, batch_size=64, normalize_embeddings=True, show_progress_bar=False)

    sim = emb @ emb.T
    n = len(clusters)
    pairs = []
    for i in range(n):
        for j in range(i+1, n):
            if sim[i, j] >= sim_threshold:
                pairs.append((i, j, float(sim[i, j])))
    pairs.sort(key=lambda x: -x[2])
    print(f"  找到 {len(pairs)} 个候选合并对（sim ≥ {sim_threshold}）")
    return pairs, emb


# ============================================
# Step 8.2: Union-Find 把候选对组成连通分量
# ============================================
class UnionFind:
    def __init__(self, n):
        self.parent = list(range(n))
    def find(self, x):
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]
            x = self.parent[x]
        return x
    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.parent[ra] = rb


# ============================================
# Step 8.3: LLM 确认合并
# ============================================
PROMPT_MERGE = """下面是 {n} 个看起来相似的「需求簇」，每个都已经独立打过标签。请判断它们是否真的描述同一个底层需求。

【输入】
{cluster_text}

【任务】
1. 判断这些簇是否应该合并为一个需求点
2. 如果应该合并，给出合并后的统一标题、描述
3. 如果其中有不应该合并的（语义不同），从合并组中剔除

【输出格式】仅输出如下 JSON:
{{
  "should_merge": true/false,
  "merge_groups": [
    {{
      "merged_title": "合并后的标题",
      "merged_description": "1-2 句话描述",
      "merged_demand_type": "功能缺失|体验问题|平台策略",
      "merged_demand_tier": 1/2/3,
      "merged_ai_score": 5,
      "merged_ai_intervention_type": "重量介入|轻量介入|无关",
      "merged_ai_description": "AI 怎么介入",
      "merged_ai_keywords": ["..."],
      "cluster_indices": [0, 1, 2]   // 上面输入中要合并的簇序号（0-based）
    }}
  ],
  "exclude_indices": []   // 不应该合并、要单独保留的簇序号
}}

如果 should_merge=false，所有簇都要进 exclude_indices。
如果只有一组合并，merge_groups 只放一项。
如果是多个互相独立的合并组（少见），可以放多项。
"""


def call_deepseek(prompt, retry=0):
    body = {
        "model": MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.1,
        "max_tokens": 1500,
        "response_format": {"type": "json_object"},
    }
    req = urllib.request.Request(
        API_URL,
        data=json.dumps(body).encode("utf-8"),
        headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            result = json.loads(resp.read())
        return result["choices"][0]["message"]["content"].strip(), result.get("usage", {})
    except Exception as e:
        if retry < MAX_RETRY:
            time.sleep(2 * (retry + 1))
            return call_deepseek(prompt, retry + 1)
        return None, {"error": str(e)[:200]}


def confirm_group(group_indices, clusters):
    """对一组候选合并簇调用 LLM 确认"""
    sub_clusters = [clusters[i] for i in group_indices]
    cluster_text = ""
    for i, c in enumerate(sub_clusters):
        products = list(c.get("product_distribution", {}).keys())[:3]
        cluster_text += (
            f"[簇 {i}] (规模 {c['size']}, T{c.get('demand_tier','?')}, AI{c.get('ai_score','?')}, 主要产品 {products})\n"
            f"  标题: {c.get('title','')}\n"
            f"  描述: {c.get('description','')[:150]}\n"
            f"  指纹: {c.get('semantic_fingerprint','')}\n\n"
        )
    prompt = PROMPT_MERGE.format(n=len(sub_clusters), cluster_text=cluster_text)
    text, usage = call_deepseek(prompt)
    if not text:
        return None, usage
    try:
        return json.loads(text), usage
    except json.JSONDecodeError:
        return None, usage


# ============================================
# 主流程
# ============================================
def merge_clusters(clusters, group_decisions):
    """根据 LLM 决策真正合并簇。返回最终需求点列表"""
    final = []
    used_indices = set()

    for group_indices, decision in group_decisions:
        if not decision:
            continue
        # 处理 LLM 返回的合并组
        if decision.get("should_merge"):
            for mg in decision.get("merge_groups", []):
                local_idxs = mg.get("cluster_indices", [])
                # local_idxs 是相对于 group_indices 的下标
                global_idxs = [group_indices[i] for i in local_idxs if 0 <= i < len(group_indices)]
                if not global_idxs:
                    continue
                # 合并
                merged = build_merged_demand(global_idxs, clusters, mg)
                final.append(merged)
                used_indices.update(global_idxs)
            # exclude 的单独保留
            for ex in decision.get("exclude_indices", []):
                if 0 <= ex < len(group_indices):
                    gi = group_indices[ex]
                    if gi not in used_indices:
                        # 单独成一个需求点
                        final.append(build_single_demand(clusters[gi]))
                        used_indices.add(gi)
        else:
            # LLM 判定不合并，全部单独保留
            for gi in group_indices:
                if gi not in used_indices:
                    final.append(build_single_demand(clusters[gi]))
                    used_indices.add(gi)

    # 没参与合并组的簇也要保留
    for i, c in enumerate(clusters):
        if i not in used_indices:
            final.append(build_single_demand(c))
            used_indices.add(i)

    return final


def build_single_demand(cluster):
    """单个簇 → 需求点"""
    return {
        "demand_id": None,  # 后面统一编号
        "title": cluster.get("title", ""),
        "description": cluster.get("description", ""),
        "demand_type": cluster.get("demand_type", ""),
        "demand_tier": cluster.get("demand_tier", 2),
        "ai_score": cluster.get("ai_score", 0),
        "ai_intervention_type": cluster.get("ai_intervention_type", ""),
        "ai_description": cluster.get("ai_description", ""),
        "ai_keywords": cluster.get("ai_keywords", []),
        "size": cluster["size"],
        "source_distribution": cluster.get("source_distribution", {}),
        "product_distribution": cluster.get("product_distribution", {}),
        "perspective_distribution": cluster.get("perspective_distribution", {}),
        "sentiment_distribution": cluster.get("sentiment_distribution", {}),
        "avg_weight_signal": cluster.get("avg_weight_signal", 0),
        "merged_from_clusters": [cluster["cluster_id"]],
        "member_atom_ids": list(cluster.get("member_atom_ids", [])),
        "representative_statements": cluster.get("representative_statements", []),
    }


def build_merged_demand(global_idxs, clusters, mg):
    """多个簇合并 → 需求点"""
    members = [clusters[i] for i in global_idxs]
    # 合并各种分布
    src = Counter()
    prod = Counter()
    pers = Counter()
    sent = Counter()
    all_atoms = []
    all_reps = []
    for m in members:
        for k, v in m.get("source_distribution", {}).items(): src[k] += v
        for k, v in m.get("product_distribution", {}).items(): prod[k] += v
        for k, v in m.get("perspective_distribution", {}).items(): pers[k] += v
        for k, v in m.get("sentiment_distribution", {}).items(): sent[k] += v
        all_atoms.extend(m.get("member_atom_ids", []))
        all_reps.extend(m.get("representative_statements", []))

    total_size = sum(m["size"] for m in members)
    avg_w = sum(m.get("avg_weight_signal", 0) * m["size"] for m in members) / max(total_size, 1)

    return {
        "demand_id": None,
        "title": mg.get("merged_title", members[0].get("title", "")),
        "description": mg.get("merged_description", members[0].get("description", "")),
        "demand_type": mg.get("merged_demand_type", members[0].get("demand_type", "")),
        "demand_tier": mg.get("merged_demand_tier", members[0].get("demand_tier", 2)),
        "ai_score": mg.get("merged_ai_score", round(sum(m.get("ai_score", 0) for m in members) / len(members))),
        "ai_intervention_type": mg.get("merged_ai_intervention_type", members[0].get("ai_intervention_type", "")),
        "ai_description": mg.get("merged_ai_description", members[0].get("ai_description", "")),
        "ai_keywords": mg.get("merged_ai_keywords", members[0].get("ai_keywords", [])),
        "size": total_size,
        "source_distribution": dict(src),
        "product_distribution": dict(prod.most_common(20)),
        "perspective_distribution": dict(pers),
        "sentiment_distribution": dict(sent),
        "avg_weight_signal": round(avg_w, 2),
        "merged_from_clusters": [m["cluster_id"] for m in members],
        "member_atom_ids": all_atoms,
        "representative_statements": all_reps[:10],
    }


def process(category, sim_threshold=0.75):
    in_path = PROC_DIR / f"{category}_labeled_clusters.json"
    with open(in_path, encoding="utf-8") as f:
        data = json.load(f)
    clusters = data["clusters"]
    print(f"【Step 8】category={category}  输入 {len(clusters)} 簇")

    # 8.1 找候选对
    pairs, emb = find_candidate_pairs(clusters, sim_threshold)

    # 8.2 union-find 组建连通分量
    uf = UnionFind(len(clusters))
    for i, j, _ in pairs:
        uf.union(i, j)
    groups_map = {}
    for idx in range(len(clusters)):
        root = uf.find(idx)
        groups_map.setdefault(root, []).append(idx)
    candidate_groups_raw = [g for g in groups_map.values() if len(g) >= 2]
    single_clusters = [g[0] for g in groups_map.values() if len(g) == 1]

    # 控制每组规模：大组按 KMeans 切成多个小组
    MAX_GROUP_SIZE = 6
    candidate_groups = []
    for g in candidate_groups_raw:
        if len(g) <= MAX_GROUP_SIZE:
            candidate_groups.append(g)
        else:
            # 大组：用 KMeans 在 embedding 空间切分
            from sklearn.cluster import KMeans
            sub_emb = emb[g]
            n_sub = max(2, (len(g) + MAX_GROUP_SIZE - 1) // MAX_GROUP_SIZE)
            km = KMeans(n_clusters=n_sub, random_state=42, n_init=5)
            labels_sub = km.fit_predict(sub_emb)
            for lb in set(labels_sub):
                sub = [g[i] for i, lb_i in enumerate(labels_sub) if lb_i == lb]
                if len(sub) >= 2:
                    candidate_groups.append(sub)
                else:
                    single_clusters.extend(sub)
    print(f"[Step 8.2] 候选合并组: {len(candidate_groups)}（原始 {len(candidate_groups_raw)} 组，已用 KMeans 切大组）")
    print(f"           单独簇: {len(single_clusters)}")
    if candidate_groups:
        sizes = sorted([len(g) for g in candidate_groups], reverse=True)
        print(f"           组规模分布: {sizes[:10]}{'...' if len(sizes)>10 else ''}")

    # 8.3 LLM 确认
    print(f"[Step 8.3] LLM 确认合并 (并发 {MAX_WORKERS})...")
    group_decisions = []
    total_usage = {"prompt_tokens": 0, "completion_tokens": 0}
    t0 = time.time()
    done = 0

    def _task(group):
        decision, usage = confirm_group(group, clusters)
        return group, decision, usage

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        futures = [pool.submit(_task, g) for g in candidate_groups]
        for fu in as_completed(futures):
            group, decision, usage = fu.result()
            group_decisions.append((group, decision))
            done += 1
            total_usage["prompt_tokens"] += usage.get("prompt_tokens", 0) or 0
            total_usage["completion_tokens"] += usage.get("completion_tokens", 0) or 0
            if done % 10 == 0 or done == len(candidate_groups):
                print(f"  进度 {done}/{len(candidate_groups)}  用时 {time.time()-t0:.1f}s", flush=True)

    # 8.4 真正合并
    final_demands = merge_clusters(clusters, group_decisions)

    # 排序 (T → AI → size)
    final_demands.sort(key=lambda d: (d.get("demand_tier", 9), -d.get("ai_score", 0), -d.get("size", 0)))

    # 重新编号
    for i, d in enumerate(final_demands, 1):
        d["demand_id"] = f"{category}_demand_{i:03d}"

    # 输出
    out_path = PROC_DIR / f"{category}_merged_demands.json"
    out_data = {
        "category": category,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "input_clusters": len(clusters),
        "candidate_groups": len(candidate_groups),
        "single_clusters": len(single_clusters),
        "final_demand_count": len(final_demands),
        "token_usage": total_usage,
        "estimated_cost_rmb": round(
            total_usage["prompt_tokens"] / 1e6 * 1 + total_usage["completion_tokens"] / 1e6 * 2, 4
        ),
        "demands": final_demands,
    }
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out_data, f, ensure_ascii=False, indent=2)

    print(f"\n✅ 写入 {out_path}")
    print(f"   {len(clusters)} 簇 → {len(final_demands)} 个最终需求点")
    print(f"   合并节省: {len(clusters) - len(final_demands)} 个簇")
    print(f"   Token: 输入 {total_usage['prompt_tokens']:,}  输出 {total_usage['completion_tokens']:,}")
    print(f"   费用: ¥{out_data['estimated_cost_rmb']}")
    print(f"   用时: {time.time()-t0:.1f}s")

    # 简要统计
    type_dist = Counter(d.get("demand_type", "?") for d in final_demands)
    tier_dist = Counter(d.get("demand_tier", 0) for d in final_demands)
    merged_count = sum(1 for d in final_demands if len(d.get("merged_from_clusters", [])) > 1)
    print(f"\n   类型分布: {dict(type_dist)}")
    print(f"   梯队分布: {dict(tier_dist)}")
    print(f"   实际合并的需求点: {merged_count}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--category", required=True, choices=["wechat", "social", "ai", "more"])
    ap.add_argument("--sim", type=float, default=0.75, help="候选合并对的相似度阈值")
    args = ap.parse_args()

    if not API_KEY:
        print("❌ DEEPSEEK_API_KEY 未设置")
        sys.exit(1)
    process(args.category, args.sim)


if __name__ == "__main__":
    main()
