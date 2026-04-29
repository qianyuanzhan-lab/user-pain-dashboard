#!/usr/bin/env python3
"""
需求提取器 V3 - 数据驱动版
核心改变：
1. 不用预设模板，从数据中聚类提取需求场景
2. 过滤技术问题（崩溃、卡顿、闪退等），只保留真正的需求
3. AI机会标记为"待分析"，不预设解决方案
4. 只处理近一年内的数据
"""

import json
import os
import re
import hashlib
from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple, Set
from collections import defaultdict, Counter

# ============================================
# 技术问题关键词（用于过滤）
# ============================================
TECH_ISSUE_KEYWORDS = {
    # 性能问题
    '闪退', '崩溃', 'crash', '卡顿', '卡死', '死机', '黑屏', '白屏',
    '打不开', '进不去', '启动不了', '闪屏', 'bug', 'BUG',
    # 网络问题
    '网络错误', '连接失败', '加载失败', '超时', 'timeout', '断开连接',
    # 安装问题
    '安装失败', '更新失败', '下载失败', '无法安装', '无法更新',
    # 登录问题（技术层面）
    '登录失败', '登不上', '验证码错误', '闪退登录',
    # 系统兼容
    '兼容', '适配', 'iOS', 'Android', '系统版本', '手机型号',
    # 存储问题
    '占用空间', '内存不足', '存储', '缓存',
    # 耗电发热
    '耗电', '发热', '发烫', '电量', '掉电',
}

# 需求场景关键词模式（用于识别真正的需求）
NEED_PATTERNS = {
    # 功能需求
    'want_feature': [
        r'希望(能|可以|有)',
        r'想要',
        r'需要',
        r'建议(增加|添加|加上)',
        r'能不能(增加|添加|有)',
        r'为什么(没有|不能)',
        r'应该(有|增加)',
        r'缺少',
        r'没有.*功能',
    ],
    # 体验需求
    'experience': [
        r'太(麻烦|复杂|难)',
        r'不(方便|好用|人性化)',
        r'操作.*繁琐',
        r'找不到',
        r'不知道(怎么|如何)',
    ],
    # 场景需求（用户描述具体使用场景）
    'scenario': [
        r'(每次|每天|经常).*(都|要|得)',
        r'用.*的时候',
        r'(工作|生活|学习)中',
        r'和(朋友|家人|同事)',
    ],
}

def is_tech_issue(text: str) -> bool:
    """判断是否为技术问题"""
    text_lower = text.lower()
    
    # 检查技术问题关键词
    for keyword in TECH_ISSUE_KEYWORDS:
        if keyword.lower() in text_lower:
            # 进一步判断是否真的是技术问题
            # 如果同时包含需求描述，则不算技术问题
            has_need = any(
                re.search(pattern, text)
                for patterns in NEED_PATTERNS.values()
                for pattern in patterns
            )
            if not has_need:
                return True
    
    return False

def extract_need_intent(text: str):
    """提取需求意图（核心诉求）"""
    # 按优先级匹配
    patterns = [
        # 直接表达的需求
        (r'希望(能|可以)?(.{5,50})', 2),
        (r'想要(.{5,50})', 1),
        (r'需要(.{5,50})', 1),
        (r'建议(.{5,50})', 1),
        (r'能不能(.{5,50})', 1),
        (r'应该(.{5,50})', 1),
        # 反向表达的需求
        (r'为什么(不能|没有|不)(.{5,40})', 2),
        (r'(没有|缺少)(.{5,30})(功能|选项|设置)', 2),
        # 痛点表达
        (r'太(麻烦|复杂|难)(.{5,30})', 2),
        (r'每次都(要|得)(.{5,40})', 2),
    ]
    
    for pattern, group in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(group).strip()
    
    return None

def extract_keywords(text: str, top_n: int = 5) -> List[str]:
    """提取关键词"""
    # 简单的关键词提取（基于词频和长度）
    # 去掉常见停用词
    stopwords = {'的', '了', '是', '在', '我', '有', '和', '就', '不', '人', '都', '一', '一个', '上', '也', '很', '到', '说', '要', '去', '你', '会', '着', '没有', '看', '好', '自己', '这', '这个', '那', '那个', '还', '能', '对', '可以', '什么', '这样', '那样', '吗', '吧', '呢', '啊', '哦', '嗯', '哈', '呀', '啦'}
    
    # 分词（简单按标点和空格分割）
    words = re.findall(r'[\u4e00-\u9fa5]{2,6}|[a-zA-Z]{3,}', text)
    
    # 过滤停用词和单字
    words = [w for w in words if w not in stopwords and len(w) >= 2]
    
    # 统计词频
    word_counts = Counter(words)
    
    return [w for w, c in word_counts.most_common(top_n)]

def cluster_needs(reviews: List[Dict]) -> List[Dict]:
    """聚类相似需求"""
    # 按关键词聚类
    clusters = defaultdict(lambda: {
        'count': 0,
        'samples': [],
        'keywords': Counter(),
        'sources': Counter(),
        'intents': [],
    })
    
    for review in reviews:
        text = review['text']
        
        # 跳过技术问题
        if is_tech_issue(text):
            continue
        
        # 提取需求意图
        intent = extract_need_intent(text)
        if not intent:
            continue
        
        # 提取关键词用于聚类
        keywords = extract_keywords(text)
        if not keywords:
            continue
        
        # 用前两个关键词作为聚类key
        cluster_key = '_'.join(sorted(keywords[:2]))
        
        cluster = clusters[cluster_key]
        cluster['count'] += 1
        cluster['samples'].append(review)
        cluster['intents'].append(intent)
        cluster['sources'][review.get('source', 'unknown')] += 1
        for kw in keywords:
            cluster['keywords'][kw] += 1
    
    return clusters

def merge_similar_clusters(clusters: Dict) -> List[Dict]:
    """合并相似的聚类"""
    # 按数量排序
    sorted_clusters = sorted(
        clusters.items(),
        key=lambda x: x[1]['count'],
        reverse=True
    )
    
    merged = []
    used_keys = set()
    
    for key, cluster in sorted_clusters:
        if key in used_keys:
            continue
        
        if cluster['count'] < 3:  # 至少3条才有效
            continue
        
        # 检查是否可以和已有的合并
        merged_with = None
        top_keywords = set(w for w, c in cluster['keywords'].most_common(5))
        
        for existing in merged:
            existing_keywords = set(existing['top_keywords'])
            # 如果关键词重叠超过60%，合并
            overlap = len(top_keywords & existing_keywords) / max(len(top_keywords), 1)
            if overlap > 0.6:
                merged_with = existing
                break
        
        if merged_with:
            # 合并到现有聚类
            merged_with['count'] += cluster['count']
            merged_with['samples'].extend(cluster['samples'])
            merged_with['intents'].extend(cluster['intents'])
            for src, cnt in cluster['sources'].items():
                merged_with['sources'][src] = merged_with['sources'].get(src, 0) + cnt
            for kw, cnt in cluster['keywords'].items():
                merged_with['all_keywords'][kw] = merged_with['all_keywords'].get(kw, 0) + cnt
        else:
            # 创建新聚类
            merged.append({
                'key': key,
                'count': cluster['count'],
                'samples': cluster['samples'],
                'intents': cluster['intents'],
                'sources': dict(cluster['sources']),
                'top_keywords': list(w for w, c in cluster['keywords'].most_common(5)),
                'all_keywords': dict(cluster['keywords']),
            })
        
        used_keys.add(key)
    
    return merged

def generate_need_title(cluster: Dict) -> str:
    """从聚类数据生成需求标题"""
    # 用最常见的意图生成标题
    intent_counts = Counter(cluster['intents'])
    if intent_counts:
        top_intent = intent_counts.most_common(1)[0][0]
        # 清理并截断
        title = re.sub(r'[，。！？,.!?].*', '', top_intent)
        if len(title) > 20:
            title = title[:20] + '...'
        return title
    
    # fallback: 用关键词
    return ' + '.join(cluster['top_keywords'][:3])

def select_best_samples(samples: List[Dict], max_count: int = 5) -> List[Dict]:
    """选择最佳样本"""
    # 评分标准：长度适中、有明确意图、情感强烈
    def score_sample(s):
        text = s.get('text', '')
        score = 0
        
        # 长度适中（30-200字）
        if 30 <= len(text) <= 200:
            score += 3
        elif len(text) > 200:
            score += 1
        
        # 有明确需求表达
        if any(kw in text for kw in ['希望', '建议', '需要', '想要']):
            score += 2
        
        # 有具体场景描述
        if any(kw in text for kw in ['每次', '经常', '工作', '生活']):
            score += 2
        
        # 情感强烈
        if any(kw in text for kw in ['真的', '太', '非常', '特别', '强烈']):
            score += 1
        
        return score
    
    scored = [(s, score_sample(s)) for s in samples]
    scored.sort(key=lambda x: x[1], reverse=True)
    
    # 去重选择
    selected = []
    seen_texts = set()
    
    for sample, score in scored:
        text = sample.get('text', '')[:50]
        if text not in seen_texts:
            selected.append({
                'original_text': sample.get('text', ''),
                'source': sample.get('source', ''),
                'app_name': sample.get('app_name', ''),
                'date': sample.get('date', ''),
            })
            seen_texts.add(text)
        
        if len(selected) >= max_count:
            break
    
    return selected

def format_data_sources(sources: Dict) -> str:
    """格式化数据来源"""
    source_names = {
        'appstore': 'App Store',
        'googleplay': 'Google Play',
        'hackernews': 'Hacker News',
    }
    
    parts = []
    for src, count in sorted(sources.items(), key=lambda x: -x[1]):
        name = source_names.get(src, src)
        parts.append(f'{name}({count})')
    
    return '、'.join(parts)

def process_category(category: str, data_dir: str, one_year_ago: datetime) -> Dict:
    """处理单个类目"""
    raw_dir = os.path.join(data_dir, 'raw')
    all_reviews = []
    
    # 加载所有数据源
    for source_dir in ['appstore', 'googleplay', 'hackernews']:
        source_path = os.path.join(raw_dir, source_dir)
        if not os.path.isdir(source_path):
            continue
        
        for filename in os.listdir(source_path):
            if not filename.startswith(category) or not filename.endswith('.json'):
                continue
            
            filepath = os.path.join(source_path, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                items = data.get('reviews', []) or data.get('comments', []) or data.get('complaints', [])
                
                for item in items:
                    # 检查时间（近一年）
                    date_str = item.get('date', '') or item.get('timestamp', '')
                    if date_str:
                        try:
                            # 尝试解析日期
                            if 'T' in date_str:
                                item_date = datetime.fromisoformat(date_str.replace('Z', '+00:00').split('+')[0])
                            else:
                                item_date = datetime.strptime(date_str[:10], '%Y-%m-%d')
                            
                            if item_date < one_year_ago:
                                continue
                        except:
                            pass  # 无法解析日期，保留
                    
                    text = item.get('content') or item.get('text') or item.get('title') or ''
                    if len(text) < 15:  # 太短的跳过
                        continue
                    
                    all_reviews.append({
                        'text': text,
                        'source': source_dir,
                        'app_name': item.get('app_name', ''),
                        'date': date_str,
                        'rating': item.get('rating', 0),
                    })
                    
            except Exception as e:
                print(f"  加载 {filepath} 失败: {e}")
    
    print(f"  {category}: 加载 {len(all_reviews)} 条评论")
    
    # 聚类需求
    clusters = cluster_needs(all_reviews)
    print(f"  {category}: 初步聚类 {len(clusters)} 个")
    
    # 合并相似聚类
    merged = merge_similar_clusters(clusters)
    print(f"  {category}: 合并后 {len(merged)} 个需求")
    
    # 生成结果
    opportunities = []
    for cluster in merged[:30]:  # 最多30个需求
        title = generate_need_title(cluster)
        
        opportunities.append({
            'id': hashlib.md5(title.encode()).hexdigest()[:8],
            'title': title,
            'mention_count': cluster['count'],
            'keywords': cluster['top_keywords'],
            'data_sources': format_data_sources(cluster['sources']),
            'ai_opportunity': '待分析',  # 不预设，标记为待分析
            'evidence_samples': select_best_samples(cluster['samples']),
        })
    
    # 按提及数排序
    opportunities.sort(key=lambda x: -x['mention_count'])
    
    return {
        'category': category,
        'generated_at': datetime.now().isoformat(),
        'total_reviews': len(all_reviews),
        'needs_identified': len(opportunities),
        'ai_opportunities': opportunities,
    }

def main():
    """主函数"""
    data_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
    one_year_ago = datetime.now() - timedelta(days=365)
    
    print("=" * 60)
    print("需求提取器 V3 - 数据驱动版")
    print(f"时间范围: {one_year_ago.strftime('%Y-%m-%d')} 至今")
    print("=" * 60)
    
    categories = ['wechat', 'social', 'ai', 'more']
    
    for category in categories:
        print(f"\n处理类目: {category}")
        result = process_category(category, data_dir, one_year_ago)
        
        # 保存结果
        output_dir = os.path.join(data_dir, 'processed')
        os.makedirs(output_dir, exist_ok=True)
        
        output_path = os.path.join(output_dir, f'{category}_ai_opportunities.json')
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        print(f"  保存到: {output_path}")
        
        # 打印摘要
        print(f"\n  TOP 5 需求:")
        for i, opp in enumerate(result['ai_opportunities'][:5], 1):
            print(f"  {i}. {opp['title']} ({opp['mention_count']}次)")
            print(f"     来源: {opp['data_sources']}")
    
    print("\n" + "=" * 60)
    print("处理完成！")
    print("=" * 60)

if __name__ == '__main__':
    main()
