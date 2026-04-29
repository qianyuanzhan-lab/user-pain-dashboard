#!/usr/bin/env python3
"""
更新分析数据中的 evidence_samples
使用 select_representative_samples 的新逻辑，确保：
1. 时间分散（覆盖近一年）
2. 语气相对客观
3. 来源多样（不同 App）
"""

import json
import os
from datetime import datetime
from select_representative_samples import (
    load_raw_reviews,
    select_representative_samples,
    search_reviews_by_topic,
    parse_date
)

import re

# 核心关键词映射（作为主要匹配依据）
CORE_KEYWORDS = {
    # 社交类
    "智能诈骗识别与预警": ["诈骗", "骗子", "酒托", "婚托", "杀猪盘", "骗钱", "被骗", "假人", "机器人账号"],
    "智能内容审核与申诉": ["封号", "违规", "申诉", "误封", "禁言", "审核"],
    "智能广告过滤": ["广告", "推广", "营销", "商业化", "广告太多"],
    "智能匹配优化": ["匹配", "推荐不准", "配对", "喜好", "类型不对"],
    "智能内容推荐": ["推荐", "算法", "千篇一律", "信息茧房", "都一样"],
    "智能音频增强": ["音频", "音质", "声音", "播放", "听不清"],
    # AI 类
    "AI 回答质量保障": ["回答", "不准", "错误", "瞎编", "胡说", "幻觉"],
    "多模态交互增强": ["图片", "识图", "拍照", "上传图", "看图"],
    "上下文记忆增强": ["上下文", "记不住", "忘记", "重复说"],
    "响应速度优化": ["太慢", "卡顿", "加载", "等半天", "响应慢"],
    "专业领域深化": ["不专业", "太浅", "深度不够", "泛泛而谈"],
    "智能使用限额优化": ["限制", "额度", "次数", "免费", "收费"],
    # 办公类
    "智能会议纪要": ["会议", "纪要", "记录", "总结"],
    "智能考勤定位": ["考勤", "打卡", "定位", "位置"],
    "智能日程协调": ["日程", "排期", "时间", "安排", "冲突"],
    "智能任务提醒": ["提醒", "待办", "任务", "通知", "忘记"],
    "智能知识管理": ["文档", "笔记", "搜索", "找不到", "知识"],
    "智能会议音视频优化": ["音视频", "画面", "卡顿", "延迟", "清晰度"],
    # 微信类
    "智能待办提取": ["待办", "提醒", "任务", "事项"],
    "智能客服增强": ["客服", "人工", "回复", "联系不上"],
    "语音消息智能处理": ["语音", "转文字", "60秒", "听不完"],
    "朋友圈智能创作": ["朋友圈", "发布", "创作", "文案"],
    "智能信息过滤": ["消息", "太多", "打扰", "屏蔽", "免打扰"],
    "智能存储管理": ["存储", "空间", "文件", "清理", "占用"],
}

def extract_keywords_from_text(text: str, min_len: int = 2, max_keywords: int = 10) -> list:
    """从文本中提取关键词（简单方法，不依赖 jieba）"""
    # 停用词
    stopwords = {'的', '了', '是', '在', '和', '与', '或', '等', '不', '有', '这', '那', 
                 '可以', '能够', '进行', '使用', '通过', '用户', '功能', '问题', '情况',
                 '需要', '希望', '建议', '提供', '支持', '优化', '改进', '提升', 'AI', 'ai',
                 '智能', '自动', '平台', '内容', '信息', '系统', '服务', '管理', '社交',
                 '识别', '预警', '增强', '处理', '分析', '体验', '效果'}
    
    # 提取中文词组（2-4字）
    chinese_words = re.findall(r'[\u4e00-\u9fa5]{2,4}', text)
    
    # 去重并过滤停用词
    keywords = []
    seen = set()
    for w in chinese_words:
        if w not in seen and w not in stopwords and len(w) >= min_len:
            keywords.append(w)
            seen.add(w)
            if len(keywords) >= max_keywords:
                break
    
    return keywords

def update_category_samples(category: str, data_dir: str):
    """更新某个类目的所有 opportunity 的 evidence_samples"""
    
    # 加载原始评论
    reviews = load_raw_reviews(data_dir, category)
    if not reviews:
        print(f"  ⚠️ {category} 无原始评论数据")
        return
    
    print(f"  📝 加载了 {len(reviews)} 条原始评论")
    
    # 加载现有分析结果（在 processed 目录）
    analyzed_file = os.path.join(data_dir, 'processed', f'{category}_ai_opportunities.json')
    if not os.path.exists(analyzed_file):
        print(f"  ⚠️ 分析文件不存在: {analyzed_file}")
        return
    
    with open(analyzed_file, 'r', encoding='utf-8') as f:
        analyzed_data = json.load(f)
    
    # 数据结构是 ai_opportunities 而不是 opportunities
    opportunities = analyzed_data.get('ai_opportunities', [])
    
    updated_count = 0
    for opp in opportunities:
        title = opp.get('title', '')
        description = opp.get('description', '')
        pain_summary = opp.get('user_pain_summary', '')
        
        # 优先使用核心关键词映射
        keywords = CORE_KEYWORDS.get(title, [])
        
        # 如果没有映射，从文本中提取
        if not keywords:
            combined_text = f"{title} {description} {pain_summary}"
            keywords = extract_keywords_from_text(combined_text, min_len=2, max_keywords=10)
        
        if not keywords:
            print(f"    ⏭️ 跳过 [{title}]：无法提取关键词")
            continue
        
        print(f"    🔍 [{title}] 使用关键词: {keywords[:5]}...")
        
        # 搜索相关评论
        related_reviews = search_reviews_by_topic(reviews, keywords)
        if not related_reviews:
            print(f"    ⏭️ 跳过 [{title}]：无匹配评论")
            continue
        
        # 选取代表性样本（至少 3 条，最多 5 条）
        MIN_SAMPLES = 3
        MAX_SAMPLES = 5
        
        samples = select_representative_samples(
            reviews=related_reviews,
            keywords=keywords,
            max_samples=MAX_SAMPLES
        )
        
        if len(samples) < MIN_SAMPLES:
            print(f"    ⏭️ 跳过 [{title}]：强相关样本不足（需要至少 {MIN_SAMPLES} 条，实际 {len(samples)} 条）")
            continue
        
        # 转换为 evidence_samples 格式
        evidence_samples = []
        for i, s in enumerate(samples):
            date = parse_date(s.get('date', ''))
            date_str = date.strftime('%Y-%m-%d') if date else '未知'
            
            evidence_samples.append({
                "id": f"{category}-{opp.get('id', '')}-sample-{i+1}",
                "app_name": s.get('app_name', '未知'),
                "content": s.get('content', ''),
                "rating": s.get('rating', 0),
                "author": s.get('author', '匿名用户'),
                "date": date_str,
                "source_url": f"https://apps.apple.com/cn/app/id{s.get('app_id', '')}"
            })
        
        opp['evidence_samples'] = evidence_samples
        
        # 打印样本时间分布
        dates = [es['date'] for es in evidence_samples]
        print(f"    ✅ [{title}] 更新了 {len(evidence_samples)} 条样本，日期分布: {min(dates)} ~ {max(dates)}")
        updated_count += 1
    
    # 保存更新后的数据
    with open(analyzed_file, 'w', encoding='utf-8') as f:
        json.dump(analyzed_data, f, ensure_ascii=False, indent=2)
    
    print(f"  💾 已更新 {updated_count}/{len(opportunities)} 个机会点的样本")

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(script_dir, '..', 'data')
    
    print("🔄 开始更新 evidence_samples...\n")
    
    for category in ['wechat', 'social', 'ai', 'more']:
        print(f"\n📂 处理类目: {category}")
        update_category_samples(category, data_dir)
    
    print("\n✅ 全部更新完成！")

if __name__ == '__main__':
    main()
