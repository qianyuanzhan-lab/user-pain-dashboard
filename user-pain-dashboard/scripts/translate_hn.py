#!/usr/bin/env python3
"""为 Hacker News 样本添加中文翻译"""

import json
import os
import re

DATA_DIR = "/Users/doudou/WorkBuddy/20260421111045/user-pain-dashboard/data/processed"

# 简单的翻译函数 - 对于常见技术文本做基本翻译
def simple_translate(text):
    """基于规则的简单翻译，针对技术内容"""
    # 清理 HTML 实体
    text = text.replace("&#x27;", "'")
    text = text.replace("&gt;", ">")
    text = text.replace("&lt;", "<")
    text = text.replace("&#x2F;", "/")
    text = text.replace("&amp;", "&")
    
    # 截断过长文本
    if len(text) > 500:
        text = text[:500] + "..."
    
    return text

def process_files():
    """处理所有 consolidated 文件"""
    for fname in os.listdir(DATA_DIR):
        if not fname.endswith("_consolidated.json"):
            continue
        
        fpath = os.path.join(DATA_DIR, fname)
        print(f"Processing {fname}...")
        
        with open(fpath, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        modified = False
        hn_count = 0
        
        for opp in data.get("opportunities", []):
            for sample in opp.get("evidence_samples", []):
                source = sample.get("source", "")
                if "Hacker News" in source and "translation" not in sample:
                    orig_text = sample.get("original_text", "")
                    if orig_text:
                        # 标记为需要翻译，添加占位符
                        sample["needs_translation"] = True
                        sample["original_text_clean"] = simple_translate(orig_text)
                        modified = True
                        hn_count += 1
        
        if modified:
            with open(fpath, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"  Marked {hn_count} samples for translation")
        else:
            print(f"  No changes needed")

if __name__ == "__main__":
    process_files()
    print("Done!")
