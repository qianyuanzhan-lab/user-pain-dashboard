#!/usr/bin/env python3
"""
Step 8.6: 描述修订
================================================================
对每个最终需求点，基于 title + 原始代表诉求，让 LLM 重写 description。
确保 description 既解释 title，又扎根于用户真实原话。

输入: data/processed/{category}_merged_demands.json  (Step 8.5 输出)
输出: 覆盖写回相同文件（description 字段重生成）

用法:
  python3 pipeline_step8_6_refine.py --category social
"""

import os
import sys
import json
import time
import argparse
import urllib.request
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

env_path = ROOT.parent / ".env"
if env_path.exists():
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line: continue
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")


PROMPT = """你是产品文档编辑。下面是一个「需求点」的标题和来自用户原始评论的诉求证据。

【需求点标题】
{title}

【原始用户诉求样本】（从 {total} 条原子中抽取代表）
{samples}

【任务】
重写这个需求点的"描述"，要求：
1. **紧扣标题**：描述必须是对标题的展开解释，不能说别的
2. **扎根证据**：描述必须是能从上面的用户诉求样本里推导出来的，不能凭空添加
3. **具体场景**：点出用户在什么情况下、希望什么结果
4. **简洁**：1-2 句话，不超过 80 字
5. 不要写成"用户希望…"这种空洞套话，用具体的动词和对象

【输出格式】仅输出 JSON，不要解释:
{{"description": "重写后的描述"}}
"""


def call_deepseek(prompt, retry=0):
    body = {
        "model": MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.2,
        "max_tokens": 300,
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


def refine_one(demand):
    title = demand.get("title", "")
    reps = demand.get("representative_statements", [])[:6]
    total = demand.get("size", len(reps))
    samples_text = "\n".join(f"{i+1}. {s}" for i, s in enumerate(reps))
    prompt = PROMPT.format(title=title, total=total, samples=samples_text)
    text, usage = call_deepseek(prompt)
    if not text:
        return demand, usage
    try:
        parsed = json.loads(text)
        new_desc = parsed.get("description", "").strip()
        if new_desc:
            demand["description_original"] = demand.get("description", "")
            demand["description"] = new_desc
    except json.JSONDecodeError:
        pass
    return demand, usage


def process(category):
    in_path = PROC_DIR / f"{category}_merged_demands.json"
    with open(in_path, encoding="utf-8") as f:
        data = json.load(f)
    demands = data["demands"]
    print(f"【Step 8.6】category={category}  修订 {len(demands)} 个描述")

    total_usage = {"prompt_tokens": 0, "completion_tokens": 0}
    t0 = time.time()
    done = 0
    refined = [None] * len(demands)

    def _task(idx, d):
        return idx, refine_one(d)

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        futures = [pool.submit(_task, i, d) for i, d in enumerate(demands)]
        for fu in as_completed(futures):
            idx, (new_d, usage) = fu.result()
            refined[idx] = new_d
            done += 1
            total_usage["prompt_tokens"] += usage.get("prompt_tokens", 0) or 0
            total_usage["completion_tokens"] += usage.get("completion_tokens", 0) or 0
            if done % 10 == 0 or done == len(demands):
                print(f"  进度 {done}/{len(demands)}  用时 {time.time()-t0:.1f}s", flush=True)

    data["demands"] = [r for r in refined if r]
    data["refined_at"] = datetime.now(timezone.utc).isoformat()
    data["refine_token_usage"] = total_usage

    with open(in_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    cost = total_usage["prompt_tokens"] / 1e6 * 1 + total_usage["completion_tokens"] / 1e6 * 2
    print(f"\n✅ 覆盖写回 {in_path.name}")
    print(f"   Token: 输入 {total_usage['prompt_tokens']:,}  输出 {total_usage['completion_tokens']:,}")
    print(f"   费用: ¥{cost:.4f}  用时: {time.time()-t0:.1f}s")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--category", required=True, choices=["wechat", "social", "ai", "more"])
    args = ap.parse_args()
    if not API_KEY:
        print("❌ DEEPSEEK_API_KEY 未设置"); sys.exit(1)
    process(args.category)


if __name__ == "__main__":
    main()
