#!/usr/bin/env python3
"""
Hacker News 评论中文翻译脚本 V2
- 过滤一年前的老数据
- 使用 MyMemory 翻译 API（免费，每天 5000 词）
- 支持断点续传
"""

import json
import os
import re
import time
import urllib.request
import urllib.error
import urllib.parse
from datetime import datetime, timedelta
from typing import List, Dict

# 配置
INPUT_DIR = "/Users/doudou/WorkBuddy/20260421111045/user-pain-dashboard/data/raw/hackernews"
OUTPUT_DIR = "/Users/doudou/WorkBuddy/20260421111045/user-pain-dashboard/data/processed/hackernews_translated"

# 一年前的截止日期
ONE_YEAR_AGO = datetime.now() - timedelta(days=365)


def clean_html_entities(text: str) -> str:
    """清理 HTML 实体"""
    replacements = {
        "&#x27;": "'", "&quot;": '"', "&gt;": ">", "&lt;": "<",
        "&#x2F;": "/", "&amp;": "&", "&#x3D;": "=", "&nbsp;": " ",
        "&#32;": " ", "&#39;": "'", "&#34;": '"',
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text


def clean_text(text: str) -> str:
    """清理文本"""
    if not text:
        return ""
    text = clean_html_entities(text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def translate_with_mymemory(text: str, max_retries: int = 3) -> str:
    """
    使用 MyMemory API 进行翻译（免费）
    https://mymemory.translated.net/doc/spec.php
    """
    if not text or len(text.strip()) < 3:
        return text  # 太短的文本不翻译
    
    # 限制文本长度
    text = text[:500]
    
    for attempt in range(max_retries):
        try:
            base_url = "https://api.mymemory.translated.net/get"
            params = {
                'q': text,
                'langpair': 'en|zh-CN',
                'de': 'user@example.com'  # 可选邮箱
            }
            url = f"{base_url}?{urllib.parse.urlencode(params)}"
            
            req = urllib.request.Request(url, headers={
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'
            })
            
            with urllib.request.urlopen(req, timeout=30) as response:
                result = json.loads(response.read().decode('utf-8'))
                
                if result.get('responseStatus') == 200:
                    translated = result.get('responseData', {}).get('translatedText', '')
                    # 检查翻译质量
                    match = result.get('responseData', {}).get('match', 0)
                    if match > 0.5 or translated:
                        return translated
            
            return ""
        
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(1)
            else:
                return ""
    
    return ""


def translate_with_libre(text: str) -> str:
    """
    使用 LibreTranslate 公共实例（备选）
    """
    if not text or len(text.strip()) < 3:
        return text
    
    try:
        url = "https://libretranslate.com/translate"
        payload = {
            'q': text[:500],
            'source': 'en',
            'target': 'zh',
            'format': 'text'
        }
        
        data = urllib.parse.urlencode(payload).encode('utf-8')
        req = urllib.request.Request(url, data=data, headers={
            'Content-Type': 'application/x-www-form-urlencoded',
            'User-Agent': 'Mozilla/5.0'
        })
        
        with urllib.request.urlopen(req, timeout=30) as response:
            result = json.loads(response.read().decode('utf-8'))
            return result.get('translatedText', '')
    
    except:
        return ""


def filter_by_date(comments: List[Dict], cutoff_date: datetime) -> List[Dict]:
    """过滤掉指定日期之前的评论"""
    filtered = []
    removed = 0
    
    for c in comments:
        created_str = c.get('created_at', '')[:10]
        try:
            created_date = datetime.strptime(created_str, '%Y-%m-%d')
            if created_date >= cutoff_date:
                filtered.append(c)
            else:
                removed += 1
        except:
            filtered.append(c)
    
    if removed > 0:
        print(f"  过滤掉 {removed} 条一年前的老数据")
    
    return filtered


def translate_file(input_file: str, output_file: str):
    """翻译单个文件"""
    print(f"\n{'='*60}")
    print(f"处理: {os.path.basename(input_file)}")
    print(f"{'='*60}")
    
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    comments = data.get('comments', [])
    original_count = len(comments)
    
    # 过滤老数据
    comments = filter_by_date(comments, ONE_YEAR_AGO)
    print(f"  原始: {original_count} → 一年内: {len(comments)}")
    
    if not comments:
        print("  无数据")
        return 0
    
    # 检查是否已有部分翻译
    existing_translated = {}
    if os.path.exists(output_file):
        try:
            with open(output_file, 'r', encoding='utf-8') as f:
                existing = json.load(f)
            for c in existing.get('comments', []):
                if c.get('content_zh'):
                    existing_translated[c.get('id')] = c.get('content_zh')
            print(f"  已有翻译: {len(existing_translated)} 条")
        except:
            pass
    
    translated_comments = []
    success = 0
    total = len(comments)
    
    for i, comment in enumerate(comments):
        cid = comment.get('id', '')
        original = comment.get('content', '')
        cleaned = clean_text(original)
        
        new_comment = comment.copy()
        new_comment['content'] = cleaned
        
        # 检查是否已翻译
        if cid in existing_translated:
            new_comment['content_zh'] = existing_translated[cid]
            success += 1
        else:
            # 翻译
            translation = translate_with_mymemory(cleaned)
            if not translation:
                translation = translate_with_libre(cleaned)
            
            new_comment['content_zh'] = translation
            if translation:
                success += 1
            
            time.sleep(0.5)  # 限速
        
        translated_comments.append(new_comment)
        
        # 每 100 条保存一次（断点续传）
        if (i + 1) % 100 == 0:
            _save_progress(output_file, data, translated_comments, original_count)
            print(f"  进度: {i+1}/{total} ({(i+1)/total*100:.1f}%) 翻译成功: {success}")
    
    # 最终保存
    _save_progress(output_file, data, translated_comments, original_count)
    print(f"  完成: {success}/{total} ({success/total*100:.1f}%)")
    
    return total


def _save_progress(output_file: str, original_data: Dict, comments: List[Dict], original_count: int):
    """保存进度"""
    output_data = original_data.copy()
    output_data['comments'] = comments
    output_data['translation_info'] = {
        'translated_at': datetime.now().isoformat(),
        'original_count': original_count,
        'filtered_count': len(comments),
        'translated_success': sum(1 for c in comments if c.get('content_zh')),
        'cutoff_date': ONE_YEAR_AGO.strftime('%Y-%m-%d'),
        'method': 'MyMemory + LibreTranslate',
    }
    
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)


def main():
    print("=" * 60)
    print("Hacker News 评论翻译工具 V2")
    print(f"过滤截止: {ONE_YEAR_AGO.strftime('%Y-%m-%d')} 之前的数据")
    print("=" * 60)
    
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    total = 0
    for fname in sorted(os.listdir(INPUT_DIR)):
        if not fname.endswith('.json'):
            continue
        
        input_path = os.path.join(INPUT_DIR, fname)
        output_path = os.path.join(OUTPUT_DIR, fname.replace('.json', '_translated.json'))
        
        count = translate_file(input_path, output_path)
        total += count
    
    print("\n" + "=" * 60)
    print(f"完成！共处理 {total} 条评论")
    print(f"输出: {OUTPUT_DIR}")
    print("=" * 60)


if __name__ == '__main__':
    main()
