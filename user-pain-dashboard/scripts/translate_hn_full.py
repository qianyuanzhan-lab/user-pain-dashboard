#!/usr/bin/env python3
"""
Hacker News 评论中文翻译脚本
- 过滤一年前的老数据
- 支持多种翻译方式：DeepSeek API / Google Translate (免费)
- 批量处理所有评论
"""

import json
import os
import re
import time
import urllib.request
import urllib.error
import urllib.parse
from datetime import datetime, timedelta
from typing import List, Dict, Any

# 配置
INPUT_DIR = "/Users/doudou/WorkBuddy/20260421111045/user-pain-dashboard/data/raw/hackernews"
OUTPUT_DIR = "/Users/doudou/WorkBuddy/20260421111045/user-pain-dashboard/data/processed/hackernews_translated"

# 一年前的截止日期
ONE_YEAR_AGO = datetime.now() - timedelta(days=365)


def clean_html_entities(text: str) -> str:
    """清理 HTML 实体"""
    replacements = {
        "&#x27;": "'",
        "&quot;": '"',
        "&gt;": ">",
        "&lt;": "<",
        "&#x2F;": "/",
        "&amp;": "&",
        "&#x3D;": "=",
        "&nbsp;": " ",
        "&#32;": " ",
        "&#39;": "'",
        "&#34;": '"',
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


def translate_with_google_free(text: str, max_retries: int = 3) -> str:
    """
    使用 Google Translate 免费 API 进行翻译
    """
    if not text or len(text.strip()) == 0:
        return ""
    
    for attempt in range(max_retries):
        try:
            # 使用 Google Translate 免费 API
            base_url = "https://translate.googleapis.com/translate_a/single"
            params = {
                'client': 'gtx',
                'sl': 'en',
                'tl': 'zh-CN',
                'dt': 't',
                'q': text[:5000]  # 限制长度
            }
            url = f"{base_url}?{urllib.parse.urlencode(params)}"
            
            req = urllib.request.Request(url, headers={
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            })
            
            with urllib.request.urlopen(req, timeout=30) as response:
                result = json.loads(response.read().decode('utf-8'))
                # 解析结果
                if result and result[0]:
                    translated = ''.join([item[0] for item in result[0] if item[0]])
                    return translated
            
            return ""
        
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)  # 指数退避
            else:
                print(f"    翻译失败 (重试{max_retries}次后): {str(e)[:50]}")
                return ""
    
    return ""


def translate_with_deepseek(text: str, api_key: str) -> str:
    """
    使用 DeepSeek API 进行翻译
    """
    if not api_key or not text:
        return ""
    
    try:
        url = "https://api.deepseek.com/v1/chat/completions"
        
        prompt = f"""请将以下英文评论翻译成通顺的中文。要求：
1. 保持原意，使表达符合中文习惯
2. 技术术语可保留英文
3. 直接输出翻译结果

原文：{text}

翻译："""
        
        payload = {
            "model": "deepseek-chat",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.3,
            "max_tokens": 1500,
        }
        
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(url, data=data, headers={
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {api_key}',
        })
        
        with urllib.request.urlopen(req, timeout=60) as response:
            result = json.loads(response.read().decode('utf-8'))
            return result['choices'][0]['message']['content'].strip()
    
    except Exception as e:
        print(f"    DeepSeek 翻译失败: {e}")
        return ""


def filter_by_date(comments: List[Dict], cutoff_date: datetime) -> List[Dict]:
    """
    过滤掉指定日期之前的评论
    """
    filtered = []
    removed_count = 0
    
    for c in comments:
        created_str = c.get('created_at', '')[:10]
        try:
            created_date = datetime.strptime(created_str, '%Y-%m-%d')
            if created_date >= cutoff_date:
                filtered.append(c)
            else:
                removed_count += 1
        except:
            filtered.append(c)
    
    if removed_count > 0:
        print(f"  过滤掉 {removed_count} 条一年前的老数据")
    
    return filtered


def translate_hn_file(input_file: str, output_file: str, api_key: str = None, use_google: bool = True):
    """
    翻译单个 HN 数据文件
    """
    print(f"\n{'='*60}")
    print(f"处理文件: {os.path.basename(input_file)}")
    print(f"{'='*60}")
    
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    comments = data.get('comments', [])
    original_count = len(comments)
    
    # 过滤老数据
    comments = filter_by_date(comments, ONE_YEAR_AGO)
    print(f"  原始评论: {original_count} 条")
    print(f"  一年内评论: {len(comments)} 条")
    
    if not comments:
        print("  无数据需要处理")
        return 0
    
    translated_comments = []
    total = len(comments)
    success_count = 0
    
    for i, comment in enumerate(comments):
        original = comment.get('content', '')
        cleaned = clean_text(original)
        
        new_comment = comment.copy()
        new_comment['content'] = cleaned
        
        # 翻译
        if api_key:
            translation = translate_with_deepseek(cleaned, api_key)
        elif use_google:
            translation = translate_with_google_free(cleaned)
            time.sleep(0.3)  # 避免请求过快
        else:
            translation = ""
        
        new_comment['content_zh'] = translation
        translated_comments.append(new_comment)
        
        if translation:
            success_count += 1
        
        # 显示进度
        if (i + 1) % 50 == 0 or i == total - 1:
            pct = (i + 1) / total * 100
            print(f"  进度: {i+1}/{total} ({pct:.1f}%) - 翻译成功: {success_count}")
    
    # 更新数据
    output_data = data.copy()
    output_data['comments'] = translated_comments
    output_data['translation_info'] = {
        'translated_at': datetime.now().isoformat(),
        'original_count': original_count,
        'filtered_count': len(translated_comments),
        'removed_old_data': original_count - len(comments),
        'translated_success': success_count,
        'cutoff_date': ONE_YEAR_AGO.strftime('%Y-%m-%d'),
        'method': 'DeepSeek API' if api_key else ('Google Translate' if use_google else 'No translation'),
    }
    
    # 保存
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
    
    print(f"  保存到: {output_file}")
    print(f"  翻译成功率: {success_count}/{len(translated_comments)} ({success_count/len(translated_comments)*100:.1f}%)")
    
    return len(translated_comments)


def main():
    """主函数"""
    print("=" * 60)
    print("Hacker News 评论翻译工具")
    print(f"过滤截止日期: {ONE_YEAR_AGO.strftime('%Y-%m-%d')} 之前的数据")
    print("=" * 60)
    
    # 检查 API key
    api_key = os.environ.get('DEEPSEEK_API_KEY', '')
    
    if api_key:
        print("✓ 使用 DeepSeek API 进行翻译")
        use_google = False
    else:
        print("⚠ 未设置 DEEPSEEK_API_KEY")
        print("✓ 使用 Google Translate 免费 API 进行翻译")
        use_google = True
    
    # 创建输出目录
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # 处理所有文件
    total_translated = 0
    
    for fname in sorted(os.listdir(INPUT_DIR)):
        if not fname.endswith('.json'):
            continue
        
        input_path = os.path.join(INPUT_DIR, fname)
        output_path = os.path.join(OUTPUT_DIR, fname.replace('.json', '_translated.json'))
        
        count = translate_hn_file(input_path, output_path, api_key, use_google)
        total_translated += count
    
    print("\n" + "=" * 60)
    print(f"完成！共处理 {total_translated} 条评论")
    print(f"输出目录: {OUTPUT_DIR}")
    print("=" * 60)


if __name__ == '__main__':
    main()
