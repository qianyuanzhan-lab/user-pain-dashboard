#!/usr/bin/env python3
"""
清理 consolidated 数据中超过一年的 Hacker News 样本
并统计需要翻译的样本数量
"""

import json
import os
import re
from datetime import datetime, timedelta

DATA_DIR = "/Users/doudou/WorkBuddy/20260421111045/user-pain-dashboard/data/processed"
RAW_HN_DIR = "/Users/doudou/WorkBuddy/20260421111045/user-pain-dashboard/data/raw/hackernews"

# 时间阈值：一年前
CUTOFF_DATE = datetime.now() - timedelta(days=365)

def load_hn_dates():
    """从原始 HN 数据中加载评论的创建时间"""
    hn_dates = {}  # source_url -> created_at
    
    for fname in os.listdir(RAW_HN_DIR):
        if not fname.endswith(".json"):
            continue
        fpath = os.path.join(RAW_HN_DIR, fname)
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                data = json.load(f)
            for comment in data.get("comments", []):
                url = comment.get("source_url", "")
                created = comment.get("created_at", "")
                if url and created:
                    hn_dates[url] = created
        except Exception as e:
            print(f"Error loading {fname}: {e}")
    
    print(f"Loaded {len(hn_dates)} HN comment dates")
    return hn_dates

def parse_date(date_str):
    """解析日期字符串"""
    if not date_str:
        return None
    try:
        # 尝试 ISO 格式
        if "T" in date_str:
            return datetime.fromisoformat(date_str.replace("Z", "+00:00")).replace(tzinfo=None)
        # 尝试 YYYY-MM-DD 格式
        return datetime.strptime(date_str[:10], "%Y-%m-%d")
    except:
        return None

def is_too_old(sample, hn_dates):
    """判断样本是否太旧"""
    source_url = sample.get("source_url", "")
    
    # 优先用原始数据的时间
    if source_url in hn_dates:
        dt = parse_date(hn_dates[source_url])
        if dt and dt < CUTOFF_DATE:
            return True, hn_dates[source_url]
    
    # 其次用样本自带的 date 字段
    sample_date = sample.get("date", "")
    if sample_date:
        dt = parse_date(sample_date)
        if dt and dt < CUTOFF_DATE:
            return True, sample_date
    
    # 没有日期信息的，检查 URL 里的 ID（HN ID 越小越老）
    # 大约 2024-01 的评论 ID 在 38000000 左右
    if source_url and "item?id=" in source_url:
        match = re.search(r'id=(\d+)', source_url)
        if match:
            comment_id = int(match.group(1))
            # ID < 38000000 大约是 2024 年之前的数据
            if comment_id < 38000000:
                return True, f"ID {comment_id} (估算为旧数据)"
    
    return False, None

def clean_consolidated_files():
    """清理所有 consolidated 文件中的旧 HN 数据"""
    hn_dates = load_hn_dates()
    
    stats = {
        "files_processed": 0,
        "samples_removed": 0,
        "samples_kept": 0,
        "needs_translation": 0,
    }
    
    for fname in sorted(os.listdir(DATA_DIR)):
        if not fname.endswith("_consolidated.json"):
            continue
        
        fpath = os.path.join(DATA_DIR, fname)
        print(f"\n{'='*50}")
        print(f"Processing: {fname}")
        
        with open(fpath, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        modified = False
        file_removed = 0
        file_kept = 0
        file_needs_trans = 0
        
        for opp in data.get("ai_opportunities", []):
            title = opp.get("title", "")
            samples = opp.get("evidence_samples", [])
            new_samples = []
            
            for sample in samples:
                source = sample.get("source", "")
                
                # 只处理 Hacker News 来源
                if "Hacker News" not in source:
                    new_samples.append(sample)
                    continue
                
                # 检查是否太旧
                is_old, date_info = is_too_old(sample, hn_dates)
                if is_old:
                    print(f"  ✗ 删除旧样本 [{title}]: {date_info}")
                    file_removed += 1
                    modified = True
                else:
                    new_samples.append(sample)
                    file_kept += 1
                    
                    # 检查是否需要翻译
                    if not sample.get("translation"):
                        file_needs_trans += 1
            
            opp["evidence_samples"] = new_samples
        
        if modified:
            with open(fpath, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"  删除: {file_removed}, 保留: {file_kept}, 需翻译: {file_needs_trans}")
        
        stats["files_processed"] += 1
        stats["samples_removed"] += file_removed
        stats["samples_kept"] += file_kept
        stats["needs_translation"] += file_needs_trans
    
    print(f"\n{'='*50}")
    print("汇总统计:")
    print(f"  处理文件: {stats['files_processed']}")
    print(f"  删除旧样本: {stats['samples_removed']}")
    print(f"  保留样本: {stats['samples_kept']}")
    print(f"  需要翻译: {stats['needs_translation']}")
    print(f"{'='*50}")
    
    return stats

if __name__ == "__main__":
    clean_consolidated_files()
