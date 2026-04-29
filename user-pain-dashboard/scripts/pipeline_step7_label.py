#!/usr/bin/env python3
"""
Step 7: LLM 给每个簇起标题 + 描述 + AI 介入评分
================================================================
输入: data/processed/{category}_clusters.json
      data/processed/{category}_atoms.json (用于补充全部成员的诉求)
输出: data/processed/{category}_labeled_clusters.json

每个簇生成一个"草稿需求点"，含 title/description/ai_score 等。
不在这一步做合并，仅生成标题元数据，留 Step 8 二级聚合。

用法:
  python3 pipeline_step7_label.py --category social
  python3 pipeline_step7_label.py --category social --limit 5    # 试点
"""

import os
import sys
import json
import time
import argparse
import urllib.request
import urllib.error
from pathlib import Path
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed

ROOT = Path(__file__).parent.parent
PROC_DIR = ROOT / "data/processed"

API_URL = "https://api.deepseek.com/v1/chat/completions"
MODEL = "deepseek-chat"
MAX_WORKERS = 15
TIMEOUT = 60
MAX_RETRY = 3

# 加载 .env
env_path = ROOT.parent / ".env"
if env_path.exists():
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")


PROMPT_TEMPLATE = """你是产品分析师，从一组语义相近的「用户需求原子」（已聚类为同一个簇）中提炼需求点。

【簇上下文】
- 赛道: {category}
- 簇大小: {size} 条原子
- 涉及产品: {products}
- 来源分布: {sources}
- 视角分布: {perspectives}
- 类型分布: {types}
- 情绪分布: {sentiments}

【簇内诉求样本】（最多 {sample_count} 条）
{statements}

【任务】
为这个簇生成一个完整的"需求点"标签。如果簇内诉求其实是无意义的（比如纯情绪、跑题、无诉求），标 is_meaningful=false。

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
**demand_type 判定规则（非常重要，必须按顺序问）**

三选一：功能缺失 / 体验问题 / 平台策略

1. 是否关于【定价 / 封号 / 广告频次 / 实名认证 / KYC / 合规 / 隐私监控 / 内容审核规则 / 退款 / 商业化】等商业/合规/运营决策？
   → ✅ 是 = 平台策略
   - 典型："会员太贵"、"误封申诉无门"、"广告太多"、"被强制实名"、"平台监控用户"

2. 是否要求【新增 / 提供 / 支持 / 开放】一个目前不存在的功能或能力？
   → ✅ 是 = 功能缺失
   - 典型："希望支持多账号"、"希望有人工客服"、"希望开放 API"、"增加暗色模式"
   - 关键词："希望支持 X"、"希望有 X"、"希望能 X"、"增加 X"

3. 都不是，说明产品已有此功能但做得不好（慢/乱/不准/不稳/卡/错/丑）
   → ✅ = 体验问题
   - 典型："推荐不准"、"加载卡"、"匹配质量差"、"翻译不准"、"客服响应慢"

边界参考：
- "推荐算法推的都是我不想看的" = 体验问题（算法已有，质量差）
- "希望能关闭算法推荐" = 功能缺失（需新增开关）
- "广告太多" = 平台策略（商业决策）
- "广告加载卡顿" = 体验问题（性能）
- "客服没人回复" = 体验问题（有客服，服务差）
- "希望有人工客服" = 功能缺失（只有 bot）
- "封号审核太严" = 平台策略（风控策略）
- "AI 识别误判导致封号" = 平台策略（审核规则，非 AI 能力问题本身）
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

【输出格式】仅输出如下 JSON，不要任何解释:
{{
  "title": "一句话标题，写成「希望……」「X 应该……」「X 存在……问题」",
  "description": "1-2 句话描述这个需求点，说明用户在什么场景下、希望什么结果",
  "demand_type": "功能缺失|体验问题|平台策略",
  "demand_tier": 1,
  "ai_score": 5,
  "ai_intervention_type": "重量介入|轻量介入|无关",
  "ai_description": "AI 可以怎么介入解决这个需求（一句话）",
  "ai_keywords": ["关键词1", "关键词2"],
  "semantic_fingerprint": "产品类别 + 功能模块 + 核心动作（用空格分隔，3-6 词）",
  "is_meaningful": true
}}

【其他字段约束】
- demand_tier: 1=功能缺失或明确问题(如登录失败)；2=具体能力改进(推荐算法优化)；3=泛化体验优化(界面更好看)
- ai_score 1-10:
    1-3 = 工程/合规/商业模式问题，AI 帮不上
    4-6 = AI 可辅助（智能客服/推荐/降噪）
    7-10 = AI 是核心方案（语义理解/生成/智能匹配）
- ai_intervention_type:
    重量介入 = AI 是核心解决方案
    轻量介入 = AI 作为辅助手段
    无关 = AI 帮不上，纯工程/产品策略
- semantic_fingerprint 用于后续簇合并，要简洁、可比较，例如"社交App 推荐算法 优化"
"""


def call_deepseek(prompt, retry=0):
    body = {
        "model": MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.2,
        "max_tokens": 800,
        "response_format": {"type": "json_object"},
    }
    req = urllib.request.Request(
        API_URL,
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json",
        },
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


def label_cluster(cluster, atom_map, category, sample_count=8):
    """为单个簇生成标题元数据"""
    member_atoms = [atom_map[a] for a in cluster["member_atom_ids"] if a in atom_map]

    # 按权重排序，取前 sample_count 个
    member_atoms.sort(key=lambda a: -a.get("weight_signal", 0))
    samples = member_atoms[:sample_count]
    statements_text = "\n".join(f"{i+1}. {s['need_statement']}（产品：{s.get('product') or s.get('source_product','')}, 来源：{s['source']}）"
                                  for i, s in enumerate(samples))

    products = list(cluster.get("product_distribution", {}).keys())[:5]
    prompt = PROMPT_TEMPLATE.format(
        category=category,
        size=cluster["size"],
        products=", ".join(products) if products else "未知",
        sources=cluster.get("source_distribution", {}),
        perspectives=cluster.get("perspective_distribution", {}),
        types=cluster.get("type_distribution", {}),
        sentiments=cluster.get("sentiment_distribution", {}),
        sample_count=len(samples),
        statements=statements_text,
    )
    text, usage = call_deepseek(prompt)
    if not text:
        return None, usage
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        return None, usage
    return parsed, usage


def process(category, limit=None):
    cl_path = PROC_DIR / f"{category}_clusters.json"
    at_path = PROC_DIR / f"{category}_atoms.json"
    with open(cl_path, encoding="utf-8") as f:
        cl_data = json.load(f)
    with open(at_path, encoding="utf-8") as f:
        at_data = json.load(f)
    atom_map = {a["atom_id"]: a for a in at_data["atoms"]}

    clusters = cl_data["clusters"]
    if limit:
        clusters = clusters[:limit]

    print(f"【Step 7】category={category}  待处理 {len(clusters)} 簇  并发 {MAX_WORKERS}")

    labeled = [None] * len(clusters)
    total_usage = {"prompt_tokens": 0, "completion_tokens": 0}
    fail_idxs = []
    t0 = time.time()
    done = 0

    def _task(idx, cluster):
        result, usage = label_cluster(cluster, atom_map, category)
        return idx, cluster, result, usage

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        futures = [pool.submit(_task, i, c) for i, c in enumerate(clusters)]
        for fu in as_completed(futures):
            idx, cluster, result, usage = fu.result()
            done += 1
            total_usage["prompt_tokens"] += usage.get("prompt_tokens", 0) or 0
            total_usage["completion_tokens"] += usage.get("completion_tokens", 0) or 0
            if result and result.get("title"):
                # 合并簇元数据 + LLM 标签
                merged = {
                    "cluster_id": cluster["cluster_id"],
                    "size": cluster["size"],
                    **result,  # title, description, demand_type, etc.
                    "source_distribution": cluster.get("source_distribution", {}),
                    "product_distribution": cluster.get("product_distribution", {}),
                    "sentiment_distribution": cluster.get("sentiment_distribution", {}),
                    "perspective_distribution": cluster.get("perspective_distribution", {}),
                    "avg_weight_signal": cluster.get("avg_weight_signal", 0),
                    "member_atom_ids": cluster["member_atom_ids"],
                    "representative_statements": cluster.get("representative_statements", []),
                }
                labeled[idx] = merged
            else:
                fail_idxs.append(idx)
            if done % 10 == 0 or done == len(clusters):
                elapsed = time.time() - t0
                print(f"  进度 {done}/{len(clusters)}  用时 {elapsed:.1f}s", flush=True)

    labeled = [x for x in labeled if x]

    # 输出
    suffix = f"_sample{limit}" if limit else ""
    out_path = PROC_DIR / f"{category}_labeled_clusters{suffix}.json"
    out_data = {
        "category": category,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "input_clusters": len(clusters),
        "labeled_clusters": len(labeled),
        "failed": len(fail_idxs),
        "token_usage": total_usage,
        "estimated_cost_rmb": round(
            total_usage["prompt_tokens"] / 1e6 * 1 + total_usage["completion_tokens"] / 1e6 * 2, 4
        ),
        "clusters": labeled,
    }
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out_data, f, ensure_ascii=False, indent=2)

    elapsed = time.time() - t0
    print(f"\n✅ 写入 {out_path}")
    print(f"   簇 {len(clusters)} → 标签成功 {len(labeled)}  失败 {len(fail_idxs)}")
    print(f"   Token: 输入 {total_usage['prompt_tokens']:,}  输出 {total_usage['completion_tokens']:,}")
    print(f"   费用: ¥{out_data['estimated_cost_rmb']:.4f}")
    print(f"   用时: {elapsed:.1f}s")

    # 简要统计
    if labeled:
        from collections import Counter
        meaningful = sum(1 for c in labeled if c.get("is_meaningful", True))
        type_dist = Counter(c.get("demand_type", "?") for c in labeled)
        tier_dist = Counter(c.get("demand_tier", 0) for c in labeled)
        ai_avg = sum(c.get("ai_score", 0) for c in labeled) / len(labeled)
        print(f"\n   有意义簇: {meaningful}/{len(labeled)}")
        print(f"   类型分布: {dict(type_dist)}")
        print(f"   梯队分布: {dict(tier_dist)}")
        print(f"   平均 AI 分: {ai_avg:.1f}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--category", required=True, choices=["wechat", "social", "ai", "more"])
    ap.add_argument("--limit", type=int, default=None)
    args = ap.parse_args()

    if not API_KEY:
        print("❌ DEEPSEEK_API_KEY 未设置")
        sys.exit(1)
    process(args.category, args.limit)


if __name__ == "__main__":
    main()
