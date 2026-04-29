#!/usr/bin/env python3
"""
Step 8.5: 全局去重兜底合并
================================================================
对 Step 8 产出的需求点，分批让 LLM 看所有标题，找出语义重复的需求点并合并。

流程:
  1. 把全部 N 个需求点按批次（每批 30 个）喂给 LLM
  2. LLM 返回"应该合并的组"，比如 [[3,17], [5,22,41], ...]
  3. 跨批次的合并对：再扫描一遍相邻批次的 bridge 情况
  4. 用 UnionFind 合并成连通分量，输出最终需求点

用法:
  python3 pipeline_step8_5_dedup.py --category social
  python3 pipeline_step8_5_dedup.py --category social --batch-size 30
"""

import os
import sys
import json
import time
import argparse
import urllib.request
from pathlib import Path
from datetime import datetime, timezone
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed

ROOT = Path(__file__).parent.parent
PROC_DIR = ROOT / "data/processed"

API_URL = "https://api.deepseek.com/v1/chat/completions"
MODEL = "deepseek-chat"
TIMEOUT = 90
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


class UF:
    def __init__(self, n):
        self.p = list(range(n))
    def find(self, x):
        while self.p[x] != x:
            self.p[x] = self.p[self.p[x]]
            x = self.p[x]
        return x
    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.p[ra] = rb


PROMPT = """你是产品分析师。下面是 {n} 个「需求点」的标题和简短描述，它们已经经过初步合并，但可能仍有**描述同一底层需求**的重复项。

【任务】
只合并**真正等价**的需求。要非常克制、宁缺毋滥——如果任何一项细节不同，就不合并。

**严格判定规则（都满足才合并）：**
1. 用户真正想要的**结果**是同一个（不是"都与推荐算法相关"，而是"用户想要的具体解决方案相同"）
2. **功能/操作维度相同**（例如都在抱怨"信息流推荐"，而不是"信息流推荐" + "朋友推荐"混在一起）
3. **类型一致**（功能缺失≠体验问题≠平台策略，不跨类合并）
4. **粒度可比**（大类不能吞小类，例如"希望 AI 更智能"不能吞掉"希望 AI 记忆对话历史"）

**不该合并的案例：**
- "希望推荐更精准" vs "希望能关闭推荐" → 前者是质量问题，后者是要功能，别合
- "希望客服回复及时" vs "希望有人工客服" → 前者已有客服，后者没有，别合
- "希望广告少一点" vs "希望广告能关" → 频次 vs 开关，别合
- "希望支持暗色模式" vs "希望支持 iPad 适配" → 不同功能，别合
- "AI 回答准确度" vs "AI 记忆对话" → 不同能力，别合
- "ChatGPT 订阅太贵" vs "希望支持订阅分级" → 定价 vs 功能，别合

**可以合并的案例：**
- "Soul 匹配不准" + "豆瓣匹配不准" + "微博推人不准" → 合并为"社交 App 的匹配/推荐算法不准"
- "Discord 卡顿" + "微信卡顿" → 可合为"常用社交 App 卡顿"

【需求点列表】
{demand_list}

【输出格式】只输出 JSON（不要任何解释）：
{{
  "merge_groups": [
    {{
      "indices": [0, 4],
      "merged_title": "合并后统一标题",
      "merged_description": "1 句话描述",
      "reason": "为什么它们描述同一需求（一句话）"
    }}
  ]
}}

**再强调一遍：宁缺毋滥，不确定就不合并。多数批次应该只有 0-2 个合并组。**
如果你觉得没有可合并的，返回 {{"merge_groups": []}}.
"""


def call_deepseek(prompt, retry=0):
    body = {
        "model": MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.1,
        "max_tokens": 3000,
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


def batch_dedup(demands, batch_indices):
    """对一批 demands 调用 LLM 查重，返回 merge_groups（批内局部下标）"""
    demand_list_text = ""
    for local_i, global_i in enumerate(batch_indices):
        d = demands[global_i]
        type_str = d.get("demand_type", "")
        tier = d.get("demand_tier", "?")
        demand_list_text += f"[{local_i}] ({type_str}/T{tier}) {d.get('title','')} — {d.get('description','')[:80]}\n"

    prompt = PROMPT.format(n=len(batch_indices), demand_list=demand_list_text)
    text, usage = call_deepseek(prompt)
    if not text:
        return [], usage
    try:
        parsed = json.loads(text)
        groups = parsed.get("merge_groups", [])
        # 转成全局下标
        global_groups = []
        for g in groups:
            local_idx = g.get("indices", [])
            global_idx = [batch_indices[i] for i in local_idx if 0 <= i < len(batch_indices)]
            if len(global_idx) >= 2:
                global_groups.append({
                    "indices": global_idx,
                    "merged_title": g.get("merged_title", ""),
                    "merged_description": g.get("merged_description", ""),
                    "reason": g.get("reason", ""),
                })
        return global_groups, usage
    except json.JSONDecodeError:
        return [], usage


def process(category, batch_size=30):
    in_path = PROC_DIR / f"{category}_merged_demands.json"
    with open(in_path, encoding="utf-8") as f:
        data = json.load(f)
    demands = data["demands"]
    n = len(demands)
    print(f"【Step 8.5】全局去重  输入 {n} 个需求点  batch_size={batch_size}")

    # 生成批次：常规顺序批 + 一个交叉批（错位），减少跨批次漏合并
    batches = []
    for start in range(0, n, batch_size):
        batches.append(list(range(start, min(start + batch_size, n))))
    # 交叉批：从 batch_size/2 开始
    half = batch_size // 2
    for start in range(half, n, batch_size):
        end = min(start + batch_size, n)
        if end - start >= 2:
            batches.append(list(range(start, end)))

    print(f"  批次数: {len(batches)}（含常规+交叉）")

    # 并发处理所有批次
    all_groups = []
    total_usage = {"prompt_tokens": 0, "completion_tokens": 0}
    t0 = time.time()
    done = 0

    def _task(batch):
        return batch_dedup(demands, batch)

    with ThreadPoolExecutor(max_workers=5) as pool:
        futures = [pool.submit(_task, b) for b in batches]
        for fu in as_completed(futures):
            groups, usage = fu.result()
            all_groups.extend(groups)
            done += 1
            total_usage["prompt_tokens"] += usage.get("prompt_tokens", 0) or 0
            total_usage["completion_tokens"] += usage.get("completion_tokens", 0) or 0
            print(f"  进度 {done}/{len(batches)}  本批合并组 {len(groups)}  用时 {time.time()-t0:.1f}s", flush=True)

    print(f"\n  LLM 建议的合并组总数: {len(all_groups)}")
    for g in all_groups:
        print(f"    [{len(g['indices'])}合1] {g['merged_title'][:40]}  ← {g['indices']}")

    # 用 UnionFind 合并
    uf = UF(n)
    for g in all_groups:
        idxs = g["indices"]
        for i in range(1, len(idxs)):
            uf.union(idxs[0], idxs[i])

    # 记录每个根对应的合并信息
    root_info = {}
    for g in all_groups:
        root = uf.find(g["indices"][0])
        if root not in root_info:
            root_info[root] = g
        else:
            # 如果已有信息，追加原因
            root_info[root]["reason"] += " | " + g.get("reason", "")

    # 把 demands 按 root 分组
    groups_map = {}
    for i in range(n):
        root = uf.find(i)
        groups_map.setdefault(root, []).append(i)

    # 构建最终需求列表
    final_demands = []
    for root, indices in groups_map.items():
        if len(indices) == 1:
            # 单独保留
            final_demands.append(demands[indices[0]])
        else:
            # 合并
            members = [demands[i] for i in indices]
            info = root_info.get(root, {})

            # 合并分布
            src = Counter()
            prod = Counter()
            pers = Counter()
            sent = Counter()
            all_atoms = []
            all_reps = []
            merged_from = []
            for m in members:
                for k, v in m.get("source_distribution", {}).items(): src[k] += v
                for k, v in m.get("product_distribution", {}).items(): prod[k] += v
                for k, v in m.get("perspective_distribution", {}).items(): pers[k] += v
                for k, v in m.get("sentiment_distribution", {}).items(): sent[k] += v
                all_atoms.extend(m.get("member_atom_ids", []))
                all_reps.extend(m.get("representative_statements", []))
                merged_from.extend(m.get("merged_from_clusters", []))

            total_size = sum(m["size"] for m in members)
            avg_w = sum(m.get("avg_weight_signal", 0) * m["size"] for m in members) / max(total_size, 1)

            # 挑合并后的 type/tier/ai_score：取加权众数 or 最大
            type_dist = Counter()
            for m in members: type_dist[m.get("demand_type","?")] += m["size"]
            best_type = type_dist.most_common(1)[0][0]
            best_tier = min(m.get("demand_tier", 2) for m in members)  # 取最激进的梯队
            best_ai = max(m.get("ai_score", 0) for m in members)

            # 取样一个 ai_description：size 最大的那个
            biggest = max(members, key=lambda m: m["size"])

            final_demands.append({
                "demand_id": None,
                "title": info.get("merged_title") or biggest.get("title", ""),
                "description": info.get("merged_description") or biggest.get("description", ""),
                "demand_type": best_type,
                "demand_tier": best_tier,
                "ai_score": best_ai,
                "ai_intervention_type": biggest.get("ai_intervention_type", ""),
                "ai_description": biggest.get("ai_description", ""),
                "ai_keywords": biggest.get("ai_keywords", []),
                "size": total_size,
                "source_distribution": dict(src),
                "product_distribution": dict(prod.most_common(20)),
                "perspective_distribution": dict(pers),
                "sentiment_distribution": dict(sent),
                "avg_weight_signal": round(avg_w, 2),
                "merged_from_clusters": merged_from,
                "dedup_note": info.get("reason", ""),
                "member_atom_ids": all_atoms,
                "representative_statements": all_reps[:10],
            })

    # 排序
    final_demands.sort(key=lambda d: (d.get("demand_tier", 9), -d.get("ai_score", 0), -d.get("size", 0)))
    for i, d in enumerate(final_demands, 1):
        d["demand_id"] = f"{category}_demand_{i:03d}"

    # 写出
    out_path = PROC_DIR / f"{category}_merged_demands.json"
    out = {
        "category": category,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "input_demands": n,
        "llm_suggested_merges": len(all_groups),
        "final_demand_count": len(final_demands),
        "token_usage": total_usage,
        "estimated_cost_rmb": round(
            total_usage["prompt_tokens"] / 1e6 * 1 + total_usage["completion_tokens"] / 1e6 * 2, 4
        ),
        "input_clusters": data.get("input_clusters", n),
        "candidate_groups": data.get("candidate_groups", 0),
        "demands": final_demands,
    }
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    elapsed = time.time() - t0
    print(f"\n✅ {n} → {len(final_demands)} （节省 {n - len(final_demands)} 个）")
    print(f"   Token: 输入 {total_usage['prompt_tokens']:,}  输出 {total_usage['completion_tokens']:,}")
    print(f"   费用: ¥{out['estimated_cost_rmb']}")
    print(f"   用时: {elapsed:.1f}s")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--category", required=True, choices=["wechat", "social", "ai", "more"])
    ap.add_argument("--batch-size", type=int, default=30)
    args = ap.parse_args()
    if not API_KEY:
        print("❌ DEEPSEEK_API_KEY 未设置"); sys.exit(1)
    process(args.category, args.batch_size)


if __name__ == "__main__":
    main()
