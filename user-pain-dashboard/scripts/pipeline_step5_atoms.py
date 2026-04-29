#!/usr/bin/env python3
"""
Step 5: DeepSeek 抽取需求原子
================================================================
输入: data/processed/{category}_candidates.json
输出: data/processed/{category}_atoms.json

每条评论可以抽出 0-3 个需求原子（atom）。

用法:
  python3 pipeline_step5_atoms.py --category social --limit 20  # 试点
  python3 pipeline_step5_atoms.py --category social             # 全量
"""

import os
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
MAX_WORKERS = 20
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

# ============================================
# Prompt
# ============================================
PROMPT_TEMPLATE = """你是产品需求分析师，从用户评论中抽取「需求原子」。

【上下文】
- 来源: {source}（appstore/googleplay = 大众消费者，hackernews = 技术社区/海外开发者）
- 产品/话题: {product}
- 评分/权重: {weight}
- 视角: {perspective}（consumer 或 tech）

【任务】
从评论中识别用户明确表达或强烈暗示的"需求/诉求/痛点"，用 JSON 输出。

【规则】
1. 一条评论可抽出 0-3 个独立的需求原子（视信息量而定）
2. 评论只是情绪宣泄、没有可操作诉求时，atoms 返回 []
3. need_statement: 一句话、主谓宾完整、去掉个人化修饰，写成"希望……"或"X 应该……"或"X 存在……问题"
4. feature: 具体到功能模块（如"推荐算法"、"私信通知"、"会员价格"），不要太泛
5. sentiment 五选一: angry / frustrated / disappointed / suggesting / neutral
6. type 三选一: 功能缺失 / 体验问题 / 平台策略
7. perspective 已给定，直接沿用

【评论原文】
«{content}»

【输出格式】仅输出如下 JSON，不要任何解释、前缀、代码块标记:
{{"atoms": [{{"need_statement": "...", "product": "...", "feature": "...", "sentiment": "...", "type": "...", "perspective": "{perspective}"}}]}}
"""

# ============================================
# 调用 DeepSeek
# ============================================
def call_deepseek(prompt, retry=0):
    body = {
        "model": MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.2,
        "max_tokens": 1200,
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


def extract_atoms(candidate):
    """对单条候选评论调用 DeepSeek，返回 atoms list"""
    src = candidate.get("source", "")
    product = candidate.get("app_name") or candidate.get("story_title", "")[:50] or "未知"
    weight = candidate.get("weight_signal", 3)
    perspective = "tech" if src == "hackernews" else "consumer"
    content = (candidate.get("content_zh") or candidate.get("content", ""))[:1500]

    prompt = PROMPT_TEMPLATE.format(
        source=src,
        product=product,
        weight=weight,
        perspective=perspective,
        content=content,
    )
    text, usage = call_deepseek(prompt)
    if not text:
        return [], usage

    try:
        parsed = json.loads(text)
        atoms = parsed.get("atoms", []) if isinstance(parsed, dict) else []
    except json.JSONDecodeError:
        return [], usage

    # 补全字段
    enriched = []
    for i, atom in enumerate(atoms):
        if not isinstance(atom, dict) or not atom.get("need_statement"):
            continue
        enriched.append({
            "atom_id": f"{candidate['id']}_a{i+1}",
            "source_review_id": candidate["id"],
            "source": src,
            "source_product": product,
            "source_date": candidate.get("date", ""),
            "source_url": candidate.get("source_url", ""),
            "weight_signal": weight,
            "perspective": perspective,
            "need_statement": atom.get("need_statement", "").strip(),
            "product": atom.get("product", product),
            "feature": atom.get("feature", "").strip(),
            "sentiment": atom.get("sentiment", "neutral"),
            "type": atom.get("type", "体验问题"),
        })
    return enriched, usage


# ============================================
# 主流程
# ============================================
def process(category, limit=None):
    in_path = PROC_DIR / f"{category}_candidates.json"
    with open(in_path, encoding="utf-8") as f:
        data = json.load(f)
    candidates = data.get("candidates", [])

    # 检查点：加载已处理过的 review_id 集合
    suffix_chk = f"_sample{limit}" if limit else ""
    ckpt_path = PROC_DIR / f"{category}_atoms{suffix_chk}.checkpoint.json"
    done_ids = set()
    resumed_atoms = []
    resumed_usage = {"prompt_tokens": 0, "completion_tokens": 0}
    if ckpt_path.exists() and not limit:
        with open(ckpt_path, encoding="utf-8") as f:
            ck = json.load(f)
        resumed_atoms = ck.get("atoms", [])
        resumed_usage = ck.get("token_usage", resumed_usage)
        done_ids = set(ck.get("done_ids", []))
        print(f"  📌 续跑: 已完成 {len(done_ids)} 条，已抽 {len(resumed_atoms)} 个原子")

    if limit:
        # 均匀从三个来源各抽一点，保证试点的多样性
        if limit < len(candidates):
            from collections import defaultdict
            by_src = defaultdict(list)
            for c in candidates:
                by_src[c["source"]].append(c)
            # 按来源比例抽样
            sampled = []
            total = len(candidates)
            for src, items in by_src.items():
                n = max(1, int(limit * len(items) / total))
                sampled.extend(items[:n])
            candidates = sampled[:limit]

    # 过滤掉已完成的（断点续跑）
    if done_ids:
        candidates = [c for c in candidates if c["id"] not in done_ids]

    print(f"【Step 5】category={category}  本次待处理 {len(candidates)} 条")
    print(f"  模型: {MODEL}  并发: {MAX_WORKERS}")

    all_atoms = list(resumed_atoms)
    total_usage = dict(resumed_usage)
    failed = 0
    t0 = time.time()
    done = 0
    done_ids_local = set(done_ids)

    def _task(c):
        return c, extract_atoms(c)

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        futures = [pool.submit(_task, c) for c in candidates]
        for fu in as_completed(futures):
            c, (atoms, usage) = fu.result()
            done += 1
            done_ids_local.add(c["id"])
            if atoms:
                all_atoms.extend(atoms)
            else:
                failed += 1
            total_usage["prompt_tokens"] += usage.get("prompt_tokens", 0) or 0
            total_usage["completion_tokens"] += usage.get("completion_tokens", 0) or 0
            if done % 20 == 0 or done == len(candidates):
                elapsed = time.time() - t0
                print(f"  进度 {done}/{len(candidates)}  原子数 {len(all_atoms)}  失败/空 {failed}  用时 {elapsed:.1f}s", flush=True)
            # 每 100 条保存检查点
            if done % 100 == 0 and not limit:
                with open(ckpt_path, "w", encoding="utf-8") as f:
                    json.dump({
                        "category": category,
                        "done_ids": list(done_ids_local),
                        "atoms": all_atoms,
                        "token_usage": total_usage,
                        "saved_at": datetime.now(timezone.utc).isoformat(),
                    }, f, ensure_ascii=False)

    # 保存
    suffix = f"_sample{limit}" if limit else ""
    out_path = PROC_DIR / f"{category}_atoms{suffix}.json"
    out_data = {
        "category": category,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "input_reviews": len(candidates),
        "atoms_extracted": len(all_atoms),
        "empty_or_failed": failed,
        "avg_atoms_per_review": round(len(all_atoms) / max(len(candidates), 1), 2),
        "token_usage": total_usage,
        "estimated_cost_rmb": round(
            total_usage["prompt_tokens"] / 1e6 * 1 + total_usage["completion_tokens"] / 1e6 * 2, 4
        ),
        "atoms": all_atoms,
    }
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out_data, f, ensure_ascii=False, indent=2)

    elapsed = time.time() - t0
    print(f"\n✅ 写入 {out_path}")
    print(f"   评论 {len(candidates)} → 原子 {len(all_atoms)}  (平均 {out_data['avg_atoms_per_review']}/条)")
    print(f"   失败/空: {failed}")
    print(f"   Token: 输入 {total_usage['prompt_tokens']:,}  输出 {total_usage['completion_tokens']:,}")
    print(f"   费用: ¥{out_data['estimated_cost_rmb']:.4f}")
    print(f"   用时: {elapsed:.1f}s")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--category", required=True, choices=["wechat", "social", "ai", "more"])
    ap.add_argument("--limit", type=int, default=None, help="只处理前 N 条（试点用）")
    args = ap.parse_args()

    if not API_KEY:
        print("❌ DEEPSEEK_API_KEY 未设置")
        exit(1)

    process(args.category, args.limit)


if __name__ == "__main__":
    main()
