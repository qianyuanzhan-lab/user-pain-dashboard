#!/usr/bin/env python3
"""
Step 9: 把 merged_demands.json 转换为 dashboard 可用的 *_ai_opportunities_consolidated.json
================================================================
输入:
  data/processed/{category}_merged_demands.json  (Step 8 输出)
  data/processed/{category}_atoms.json           (找 source_review_id)
  data/processed/{category}_candidates.json      (找原文、评分、URL)
输出:
  data/processed/{category}_ai_opportunities_consolidated.json

格式对齐 wechat 版本，字段：
  id, title, description, ai_intervention_type, user_pain_summary,
  priority (P0/P1/P2), cross_product_relevance, source_stats,
  evidence_samples (3-5 条带 content/rating/url), mention_count,
  ai_solution, ai_description, ai_keywords, ai_score,
  demand_tier, sample_count, user_voice
"""

import os
import sys
import json
import math
import argparse
from pathlib import Path
from datetime import datetime, timezone
from collections import Counter

ROOT = Path(__file__).parent.parent
PROC_DIR = ROOT / "data/processed"

# ============================================
# 综合评分配置（用户选 B：30/40/30）
# ============================================
WEIGHT_IMPORTANCE = 0.30
WEIGHT_AI = 0.40
WEIGHT_COMMONALITY = 0.30

SENTIMENT_INTENSITY = {
    "angry": 1.0, "disgusted": 1.0,
    "frustrated": 0.7,
    "disappointed": 0.5,
    "suggesting": 0.3,
    "neutral": 0.1,
}


def calc_importance_score(d):
    """问题重要度 0-10"""
    size = d.get("size", 1)
    # log 压缩 mention_count: size=1→0, size=10→2.3, size=100→4.6, size=300→5.7
    size_norm = min(math.log1p(size) * 1.5, 6)  # 0-6

    avg_w = d.get("avg_weight_signal", 3.0)
    # 权重信号：AppStore 是 1-5 评分（低分=痛点强），HN 是归一化的 1-5
    # 大部分混合簇里 avg_w 在 1.5-3 之间，越低越痛
    # 转成 0-2 加分，1分痛点最强
    weight_norm = max(0, min((5 - avg_w) / 2, 2))  # 0-2

    # 情绪强度：取分布加权平均
    sent_dist = d.get("sentiment_distribution", {})
    total = sum(sent_dist.values()) or 1
    avg_intensity = sum(SENTIMENT_INTENSITY.get(s, 0.5) * c for s, c in sent_dist.items()) / total
    sent_norm = avg_intensity * 1.5  # 0-1.5

    # T1 加分
    tier_bonus = {1: 0.5, 2: 0.0, 3: -0.5}.get(d.get("demand_tier", 2), 0)

    score = size_norm + weight_norm + sent_norm + tier_bonus
    return max(0, min(score, 10))


def calc_ai_relevance_score(d):
    """AI 参与度 0-10"""
    ai = d.get("ai_score", 5)
    # ai_score 1-10，直接用
    # 7+ 加成 0.5（AI 是核心方案的需求要更靠前）
    bonus = 0.5 if ai >= 7 else 0
    return min(ai + bonus, 10)


def calc_commonality_score(d):
    """共性程度 0-10"""
    products = d.get("product_distribution", {})
    sources = d.get("source_distribution", {})
    p_count = len(products)
    s_count = len(sources)

    # 产品维度（1产品=0, 2=2, 3=4, 5=6, 10=8）
    p_norm = min(math.log1p(p_count) * 3, 7)  # 0-7

    # 数据源维度（1=0, 2=1.5, 3=3）—— 跨3源是最强信号
    s_norm = (s_count - 1) * 1.5  # 0-3

    return min(p_norm + s_norm, 10)


def calc_final_score(d):
    """综合分 0-10"""
    imp = calc_importance_score(d)
    ai = calc_ai_relevance_score(d)
    comm = calc_commonality_score(d)
    final = WEIGHT_IMPORTANCE * imp + WEIGHT_AI * ai + WEIGHT_COMMONALITY * comm
    return {
        "final_score": round(final, 2),
        "importance_score": round(imp, 2),
        "ai_relevance_score": round(ai, 2),
        "commonality_score": round(comm, 2),
    }

SRC_LABEL = {
    "appstore": "App Store",
    "googleplay": "Google Play",
    "hackernews": "Hacker News",
}


def determine_priority(demand):
    """根据 demand_tier + ai_score + size 综合定优先级"""
    tier = demand.get("demand_tier", 2)
    ai = demand.get("ai_score", 5)
    size = demand.get("size", 1)

    # P0: T1 + AI≥7
    # P1: T1 其他 | T2 + AI≥6
    # P2: 其他
    if tier == 1 and ai >= 7:
        return "P0"
    if tier == 1 or (tier == 2 and ai >= 6):
        return "P1"
    return "P2"


def pick_evidence_samples(demand, atom_map, candidate_map, max_samples=5):
    """从 member_atom_ids 反推原始评论，选 3-5 条最佳样本"""
    atom_ids = demand.get("member_atom_ids", [])
    # 拿到对应的 atoms
    atoms = [atom_map.get(aid) for aid in atom_ids if aid in atom_map]
    atoms = [a for a in atoms if a]

    # 去重 source_review_id（一条评论可能产生多个 atom）
    seen_reviews = set()
    review_items = []
    for a in atoms:
        rid = a["source_review_id"]
        if rid in seen_reviews:
            continue
        seen_reviews.add(rid)
        cand = candidate_map.get(rid)
        if not cand:
            continue
        review_items.append({
            "candidate": cand,
            "atom": a,
        })

    # 按 (weight_signal, quality_score) 排序，选最强的
    review_items.sort(
        key=lambda x: (
            -(x["candidate"].get("weight_signal", 0) if x["candidate"].get("source") == "hackernews"
              else (6 - x["candidate"].get("rating", 3))),  # 低评分=痛点强，反向
            -x["candidate"].get("quality_score", 0),
        )
    )

    # 生成 evidence_samples
    samples = []
    for idx, item in enumerate(review_items[:max_samples]):
        cand = item["candidate"]
        atom = item["atom"]
        src = cand.get("source", "")
        product = cand.get("app_name") or cand.get("story_title", "")[:40] or "-"
        samples.append({
            "id": cand.get("id", f"unknown_{idx}"),
            "app_name": product,
            "author": cand.get("author", "anonymous"),
            "content": cand.get("content_zh") or cand.get("content", ""),
            "original_text": cand.get("content_zh") or cand.get("content", ""),
            "rating": cand.get("rating", 0),
            "date": cand.get("date", ""),
            "source_url": cand.get("source_url", ""),
            "source": f"{SRC_LABEL.get(src, src)} - {product}",
            "relevance_note": atom.get("need_statement", ""),
            "pain_point_extracted": atom.get("need_statement", ""),
            "sentiment_score": sentiment_to_score(atom.get("sentiment", "neutral")),
            "relevance_score": round(cand.get("quality_score", 5), 1),
        })
    return samples


def sentiment_to_score(s):
    return {
        "angry": 0.9,
        "frustrated": 0.7,
        "disappointed": 0.5,
        "neutral": 0.0,
        "suggesting": 0.3,
        "disgusted": 0.9,
    }.get(s, 0.5)


def convert(category):
    # 加载三个输入
    md_path = PROC_DIR / f"{category}_merged_demands.json"
    at_path = PROC_DIR / f"{category}_atoms.json"
    cd_path = PROC_DIR / f"{category}_candidates.json"

    with open(md_path, encoding="utf-8") as f:
        md = json.load(f)
    with open(at_path, encoding="utf-8") as f:
        ad = json.load(f)
    with open(cd_path, encoding="utf-8") as f:
        cd = json.load(f)

    atom_map = {a["atom_id"]: a for a in ad["atoms"]}
    candidate_map = {c["id"]: c for c in cd["candidates"]}

    demands = md["demands"]
    print(f"输入 {len(demands)} 个需求点")

    # 给每个 demand 计算综合分
    for d in demands:
        d["_scores"] = calc_final_score(d)

    # 综合排序：final_score 降序，平局时 importance > ai > size
    demands.sort(key=lambda d: (
        -d["_scores"]["final_score"],
        -d["_scores"]["importance_score"],
        -d["_scores"]["ai_relevance_score"],
        -d.get("size", 0),
    ))

    opportunities = []
    for i, d in enumerate(demands, 1):
        priority = determine_priority(d)
        evidence = pick_evidence_samples(d, atom_map, candidate_map, max_samples=5)
        scores = d["_scores"]

        # cross_product_relevance: 列出主要产品
        products = list(d.get("product_distribution", {}).keys())

        # sources: 列表
        sources = [SRC_LABEL.get(s, s) for s in d.get("source_distribution", {}).keys()]

        # user_pain_summary: 用描述或代表性诉求
        reps = d.get("representative_statements", [])
        pain_summary = d.get("description", "")
        if not pain_summary and reps:
            pain_summary = reps[0]

        # user_voice: 选一条最有力的代表性诉求
        user_voice = reps[0] if reps else ""

        opp = {
            "id": f"{category}_demand_{i}",
            "title": d.get("title", ""),
            "description": d.get("description", ""),   # LLM 修订后的自洽描述
            "stats_label": f"用户实际提及{d.get('size', 0)}条 | AI介入可能性{d.get('ai_score', 0)}/10",
            "ai_intervention_type": d.get("ai_intervention_type", "") or "轻量介入",
            "user_pain_summary": d.get("description", ""),
            "priority": priority,
            "cross_product_relevance": [category],  # 与现有字段兼容
            "source_stats": {
                "products_mentioned": products[:10],
                "sources": sources,
                "exact_match_count": d.get("size", 0),
                "source_breakdown": d.get("source_distribution", {}),
                "perspective_breakdown": d.get("perspective_distribution", {}),
            },
            "evidence_samples": evidence,
            "mention_count": d.get("size", 0),
            "merged_from": d.get("merged_from_clusters", []),
            "ai_solution": d.get("ai_description", ""),
            "ai_description": d.get("ai_description", ""),
            "ai_keywords": d.get("ai_keywords", []),
            "ai_score": d.get("ai_score", 5),
            "user_voice": user_voice,
            "sample_count": len(evidence),
            "demand_tier": d.get("demand_tier", 2),
            "demand_type": d.get("demand_type", ""),
            # 新增跨数据源信息
            "product_breakdown": d.get("product_distribution", {}),
            "sentiment_breakdown": d.get("sentiment_distribution", {}),
            "cross_product_count": len(products),
            # 新增综合排序分（用户决策 B：30/40/30）
            "final_score": scores["final_score"],
            "importance_score": scores["importance_score"],
            "ai_relevance_score": scores["ai_relevance_score"],
            "commonality_score": scores["commonality_score"],
        }
        opportunities.append(opp)

    # 组装
    data_sources = sorted(set(
        ds for d in demands
        for ds in d.get("source_distribution", {}).keys()
    ))

    # 收集所有涉及的产品
    all_products = set()
    for d in demands:
        for p in d.get("product_distribution", {}).keys():
            all_products.add(p)

    CATEGORY_NAMES = {
        "wechat": "微信",
        "social": "社交娱乐",
        "ai": "AI 工具",
        "more": "效率工具",
    }

    out = {
        "category": category,
        "category_name": CATEGORY_NAMES.get(category, category),
        "analysis_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "data_sources": data_sources,
        "products_analyzed": sorted(all_products)[:50],
        "total_reviews_analyzed": cd["stats"]["candidate_total"],
        "total_items_analyzed": cd["stats"]["candidate_total"],
        "pipeline": {
            "raw_items": cd["stats"]["raw_total"],
            "candidate_items": cd["stats"]["candidate_total"],
            "atoms_extracted": ad["atoms_extracted"],
            "clusters_produced": md["input_clusters"],
            "final_demands": len(opportunities),
        },
        "ranking_config": {
            "weights": {
                "importance": WEIGHT_IMPORTANCE,
                "ai_relevance": WEIGHT_AI,
                "commonality": WEIGHT_COMMONALITY,
            },
            "description": "综合分 = 0.30×重要度 + 0.40×AI参与度 + 0.30×共性程度",
        },
        "ai_opportunities": opportunities,
    }

    out_path = PROC_DIR / f"{category}_ai_opportunities_consolidated.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    print(f"✅ 写入 {out_path}")
    print(f"   {len(opportunities)} 个 ai_opportunities")
    print(f"   数据源: {data_sources}")

    # Priority 分布
    pri = Counter(o["priority"] for o in opportunities)
    print(f"   优先级: {dict(pri)}")

    # 综合排序前 10 预览
    print(f"\n   综合分 Top 10（30/40/30）:")
    for i, o in enumerate(opportunities[:10], 1):
        print(f"     #{i}  final={o['final_score']:.2f}  imp={o['importance_score']:.1f}  ai={o['ai_relevance_score']:.1f}  comm={o['commonality_score']:.1f}  | size={o['mention_count']:>3}  T{o['demand_tier']}  {o['title'][:45]}")



def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--category", required=True, choices=["wechat", "social", "ai", "more"])
    args = ap.parse_args()
    convert(args.category)


if __name__ == "__main__":
    main()
