#!/usr/bin/env python3
"""
将 V3 版需求点数据转换为 Dashboard 兼容的 CategoryAIAnalysis JSON 格式
包含样本质量评估，确保选取有信息价值的样本
"""

import json
import re
from datetime import datetime
from pathlib import Path

# V3 文件路径
V3_FILE = Path(__file__).parent.parent / "data/processed/demand_points_with_samples_v3.txt"
OUTPUT_FILE = Path(__file__).parent.parent / "data/processed/wechat_ai_opportunities_consolidated.json"
RAW_DATA_FILE = Path(__file__).parent.parent / "data/raw/appstore/wechat_20260423.json"

# 低质量内容模式（会被过滤）
LOW_QUALITY_PATTERNS = [
    r'^.{0,15}$',  # 太短（<=15字）
    r'^(垃圾|真垃圾|垃圾软件|差评|一星).{0,10}$',  # 纯情绪发泄
    r'(加两个0|加个0|给我加钱|还给我钱|还我钱)',  # 无意义玩笑/无理诉求
    r'^(好|不好|可以|还行|一般).{0,5}$',  # 过于简短的评价
    r'(.)\1{5,}',  # 重复字符超过5个
    r'^(差评)+\s*(差评)*',  # "差评差评"重复开头
    r'搞抽象|整活|玩梗|os[:：]',  # 网络梗/玩梗内容
    r'[😭🙃😅🤣😂💀]{2,}',  # emoji堆砌（2个及以上）
    r'人民的好软件|良心软件',  # 反讽表达
    r'(一|有)?个叫.{2,8}的.{0,15}(花|扣|偷|拿).{0,5}(我的)?(钱|money)',  # 拟人化抱怨
    r'(看|等)\d+秒.{0,5}广告',  # 夸张反讽（"看30秒广告"）
    r'先看.{0,5}广告.{0,10}再看.{0,5}广告',  # 重复夸张
]

# 语义混乱特征（会被降权或过滤）
INCOHERENT_PATTERNS = [
    r'。\s*[？?]',  # 句号后紧跟问号（逻辑跳跃）
    r'[？?]\s*[？?]',  # 连续问号（情绪化质问）
    r'什么意思.{0,10}[？?]',  # "什么意思？"开头的质问
    r'我请问',  # 质问语气
    r'你们能不能.{0,10}(管|处理)',  # 情绪化要求
    r'太倒霉',  # 纯抱怨
]

def is_incoherent_content(content):
    """
    检测内容是否语义混乱、逻辑跳跃
    特征：
    1. 多个不相关的话题混在一起
    2. 大量反问句堆砌
    3. 情绪化宣泄而非问题描述
    """
    # 1. 句子数量与问号数量比例
    sentences = re.split(r'[。！？?!]', content)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 3]
    question_marks = content.count('？') + content.count('?')
    
    # 问号太多（超过句子数的一半）说明是情绪化质问
    if len(sentences) > 0 and question_marks > len(sentences) * 0.5:
        return True
    
    # 2. 检测语义混乱模式
    incoherent_count = sum(1 for p in INCOHERENT_PATTERNS if re.search(p, content))
    if incoherent_count >= 2:
        return True
    
    # 3. 话题跳跃检测：短句太多且关键词分散
    if len(sentences) >= 4:
        # 提取每句的关键词
        sentence_keywords = []
        for s in sentences:
            kws = set(re.findall(r'[\u4e00-\u9fa5]{2,4}', s))
            sentence_keywords.append(kws)
        
        # 相邻句子关键词重叠度低说明话题跳跃
        if len(sentence_keywords) >= 3:
            overlaps = []
            for i in range(len(sentence_keywords) - 1):
                overlap = len(sentence_keywords[i] & sentence_keywords[i+1])
                overlaps.append(overlap)
            # 平均重叠少于0.5个关键词，说明话题跳跃严重
            if sum(overlaps) / len(overlaps) < 0.5:
                return True
    
    return False

# 高质量内容特征
HIGH_QUALITY_INDICATORS = [
    '希望', '建议', '能不能', '可以', '如果', '为什么',  # 功能建议
    '每次', '总是', '经常', '一直', '有时候',  # 使用频率描述
    '之前', '以前', '更新后', '现在',  # 版本对比
    '工作', '生活', '学习', '重要',  # 使用场景
    '导致', '影响', '无法', '不能',  # 问题影响
]


def load_raw_reviews():
    """加载原始评论数据，建立文本到元数据的映射"""
    review_map = {}
    all_reviews = []
    
    if not RAW_DATA_FILE.exists():
        print(f"警告: 原始数据文件不存在: {RAW_DATA_FILE}")
        return review_map, all_reviews
    
    with open(RAW_DATA_FILE, 'r', encoding='utf-8') as f:
        raw_data = json.load(f)
    
    for review in raw_data.get('reviews', []):
        content = review.get('content', '')
        if content:
            review_item = {
                'content': content,
                'author': review.get('author', ''),
                'date': format_date(review.get('date', '')),
                'rating': review.get('rating', 0),
                'app_name': review.get('app_name', '微信'),
                'url': review.get('url', '')
            }
            all_reviews.append(review_item)
            
            # 用内容作为 key（可能有重复，取第一个）
            if content not in review_map:
                review_map[content] = review_item
    
    print(f"已加载 {len(review_map)} 条原始评论数据")
    return review_map, all_reviews


def format_date(date_str):
    """格式化日期为友好显示格式"""
    if not date_str:
        return ''
    try:
        # 处理 ISO 格式：2026-04-21T22:55:35-07:00
        dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        return dt.strftime('%Y-%m-%d')
    except:
        return date_str[:10] if len(date_str) >= 10 else date_str


def assess_sample_quality(content, demand_title, demand_keywords):
    """
    评估样本质量，返回质量分数 (0-10)
    分数越高越适合展示
    """
    score = 5.0  # 基础分
    
    # 1. 长度检查
    length = len(content)
    if length < 20:
        return 0  # 太短直接淘汰
    elif length < 30:
        score -= 2
    elif length >= 50:
        score += 1
    elif length >= 100:
        score += 2
    
    # 2. 低质量模式检查
    for pattern in LOW_QUALITY_PATTERNS:
        if re.search(pattern, content):
            return 0  # 匹配低质量模式直接淘汰
    
    # 2.5 语义混乱检测（情绪化宣泄、逻辑跳跃）
    if is_incoherent_content(content):
        return 0  # 语义混乱直接淘汰
    
    # 3. 高质量特征检查
    high_quality_count = sum(1 for ind in HIGH_QUALITY_INDICATORS if ind in content)
    score += min(high_quality_count * 0.5, 2)  # 最多加2分
    
    # 4. 与需求标题的相关性
    title_keywords = extract_keywords(demand_title)
    content_lower = content.lower()
    relevance_count = sum(1 for kw in title_keywords if kw in content_lower)
    relevance_count += sum(1 for kw in demand_keywords if kw in content_lower)
    score += min(relevance_count * 0.5, 2)  # 最多加2分
    
    # 5. 语义完整性检查（有主语+谓语+宾语的结构）
    has_structure = any([
        '我' in content and ('想' in content or '希望' in content or '建议' in content),
        '能不能' in content or '可以' in content,
        '为什么' in content or '怎么' in content,
        '问题' in content or '功能' in content,
    ])
    if has_structure:
        score += 1
    
    # 6. 纯情绪发泄检查（负面情绪词过多）
    negative_words = ['垃圾', '恶心', '烂', '死', '傻', '狗', '坑']
    negative_count = sum(1 for w in negative_words if w in content)
    if negative_count >= 3:
        score -= 2  # 情绪过重
    
    # 7. 有具体场景描述加分
    scenario_indicators = ['使用', '操作', '点击', '打开', '发送', '接收', '查看']
    if any(s in content for s in scenario_indicators):
        score += 0.5
    
    return max(0, min(10, score))


def extract_keywords(text):
    """从文本中提取关键词"""
    # 简单分词，取长度>=2的词
    words = re.findall(r'[\u4e00-\u9fa5]{2,}', text)
    # 过滤停用词
    stopwords = {'希望', '能够', '可以', '进行', '使用', '用户', '功能', '问题', '体验', '更好', '更加'}
    return [w for w in words if w not in stopwords]


def find_review_metadata(content, review_map):
    """通过内容查找评论的元数据"""
    # 精确匹配
    if content in review_map:
        return review_map[content]
    
    # 模糊匹配：去除空格和标点后比较
    content_clean = re.sub(r'\s+', '', content)
    for raw_content, metadata in review_map.items():
        raw_clean = re.sub(r'\s+', '', raw_content)
        # 检查是否包含关系（V3 样本可能是截取的）
        if content_clean in raw_clean or raw_clean in content_clean:
            return metadata
        # 前50字符匹配
        if len(content_clean) > 20 and len(raw_clean) > 20:
            if content_clean[:50] == raw_clean[:50]:
                return metadata
    
    return None


def find_best_samples_from_raw(demand_title, demand_keywords, all_reviews, max_samples=5):
    """
    从原始评论中找出与需求点最相关的高质量样本
    """
    scored_reviews = []
    title_keywords = extract_keywords(demand_title)
    all_keywords = set(title_keywords + demand_keywords)
    
    for review in all_reviews:
        content = review['content']
        
        # 计算与需求点的相关性
        content_lower = content.lower()
        relevance = sum(1 for kw in all_keywords if kw in content_lower)
        
        if relevance == 0:
            continue  # 完全不相关，跳过
        
        # 评估样本质量
        quality = assess_sample_quality(content, demand_title, demand_keywords)
        
        if quality > 2:  # 降低质量阈值，确保有足够样本
            # 综合分 = 质量分 * 0.6 + 相关性分 * 0.4
            combined_score = quality * 0.6 + min(relevance * 2, 10) * 0.4
            scored_reviews.append((combined_score, quality, relevance, review))
    
    # 按综合分排序，取前 N 个
    scored_reviews.sort(key=lambda x: x[0], reverse=True)
    
    return [r[3] for r in scored_reviews[:max_samples]]


def parse_v3_file(filepath):
    """解析 V3 格式的需求点文件"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    demands = []
    current_category = ''
    
    # 按需求点分隔符拆分
    blocks = re.split(r'\n─{20,}\n', content)
    
    # 需要合并相邻的块（标题块 + 样本块）
    i = 0
    while i < len(blocks):
        block = blocks[i].strip()
        
        # 检查是否是大分类标题
        category_match = re.search(r'【(功能需求|问题反馈|平台策略)】', block)
        if category_match:
            current_category = category_match.group(1)
            i += 1
            continue
        
        # 检查是否是需求点标题块：#1 希望...
        title_match = re.match(r'#(\d+)\s+(.+?)(?:\n|$)', block)
        if title_match:
            # 合并标题块和下一个样本块
            combined_block = block
            if i + 1 < len(blocks):
                next_block = blocks[i + 1].strip()
                if next_block.startswith('典型样本：') or '[1]' in next_block:
                    combined_block = block + '\n' + next_block
                    i += 1  # 跳过样本块
            
            demand = parse_demand_block(combined_block, current_category)
            if demand:
                demands.append(demand)
        
        i += 1
    
    return demands


def parse_demand_block(block, category):
    """解析单个需求点块"""
    demand = {
        'title': '',
        'subcategory': category,
        'mention_count': 0,
        'ai_score': 0,
        'ai_direction': '',
        'ai_keywords': [],
        'samples': []
    }
    
    lines = block.split('\n')
    
    for i, line in enumerate(lines):
        line_stripped = line.strip()
        
        # 解析标题行：#1 希望能找到人工客服解决问题
        title_match = re.match(r'#\d+\s+(.+)', line_stripped)
        if title_match:
            demand['title'] = title_match.group(1).strip()
            continue
        
        # 解析元数据行：提及: 10条 | AI介入分: 6/10 | 智能客服辅助、意图理解
        if '提及:' in line_stripped and 'AI介入分:' in line_stripped:
            # 提取提及数
            mention_match = re.search(r'提及:\s*(\d+)条', line_stripped)
            if mention_match:
                demand['mention_count'] = int(mention_match.group(1))
            
            # 提取 AI 评分
            ai_match = re.search(r'AI介入分:\s*(\d+)/10', line_stripped)
            if ai_match:
                demand['ai_score'] = int(ai_match.group(1))
            
            # 提取 AI 方向（在最后一个 | 之后的内容）
            parts = line_stripped.split('|')
            if len(parts) >= 3:
                direction = parts[-1].strip()
                demand['ai_direction'] = direction
                demand['ai_keywords'] = [kw.strip() for kw in re.split(r'[、,，]', direction) if kw.strip()]
            continue
        
        # 解析样本：[1] ★☆☆☆☆ (1星)
        sample_match = re.match(r'\[(\d+)\]\s*([★☆]+)\s*\((\d+)星\)', line_stripped)
        if sample_match:
            idx = int(sample_match.group(1))
            rating = int(sample_match.group(3))
            
            # 查找下一行的内容：「...」
            for j in range(i + 1, min(i + 5, len(lines))):
                content_line = lines[j].strip()
                content_match = re.search(r'「(.+?)」', content_line)
                if content_match:
                    demand['samples'].append({
                        'index': idx,
                        'rating': rating,
                        'content': content_match.group(1)
                    })
                    break
    
    if demand['title'] and demand['mention_count'] > 0:
        return demand
    return None


def determine_priority(mention_count, ai_score):
    """根据提及数和 AI 评分确定优先级"""
    if mention_count >= 50 or ai_score >= 8:
        return 'P0'
    elif mention_count >= 20 or ai_score >= 6:
        return 'P1'
    elif mention_count >= 5 or ai_score >= 4:
        return 'P2'
    else:
        return 'P3'


def determine_intervention_type(ai_score):
    """根据 AI 评分确定介入类型"""
    if ai_score >= 7:
        return '重量介入'
    else:
        return '轻量介入'


def generate_demand_summary(title, samples, mention_count):
    """
    基于所有高质量样本生成需求总结
    不是展示单条评论，而是总结所有评论的核心诉求
    格式：口语化、结构化，说明用户想要什么、为什么想要
    """
    if not samples:
        return f"用户希望{title}，但目前体验不佳"
    
    # 提取样本中的关键内容
    all_text = ' '.join([s['content'] for s in samples[:5]])  # 最多用5条
    
    # 核心诉求（从标题提取）
    core = title.replace('希望', '').replace('想要', '').strip()
    
    # 识别具体的问题场景（按优先级排序，取第一个匹配的）
    problem_scene = None
    
    # 1. 画质/压缩问题
    if any(kw in all_text for kw in ['模糊', '压缩', '画质', '糊', '不清晰', '失真']):
        problem_scene = '发出去的内容画质被压缩变差'
    
    # 2. 折叠相关
    elif any(kw in all_text for kw in ['折叠', '被折叠', '误伤']):
        if '误伤' in all_text or '正常' in all_text:
            problem_scene = '正常发布内容却被误判折叠'
        else:
            problem_scene = '重要信息被折叠看不到'
    
    # 3. 准确率问题
    elif any(kw in all_text for kw in ['准确', '不准', '识别错', '繁体']):
        problem_scene = '当前识别准确率不够高'
    
    # 4. 功能曾经有但现在没了
    elif ('以前' in all_text or '之前' in all_text) and ('现在没' in all_text or '不可以了' in all_text or '怎么不' in all_text):
        problem_scene = '之前有这个功能但现在用不了了'
    
    # 5. 想要但没有
    elif any(kw in all_text for kw in ['增加', '加个', '添加', '新增', '希望有']):
        problem_scene = '目前缺少这个功能'
    
    # 6. 编辑/修改需求
    elif any(kw in all_text for kw in ['编辑', '修改', '更改', '二次']):
        problem_scene = '发布后无法修改，只能删除重发'
    
    # 7. 客服问题
    elif any(kw in all_text for kw in ['人工客服', '找不到客服', '机器人', '转人工']):
        problem_scene = '遇到问题只能找机器人，转不了人工'
    
    # 8. 误封/限制
    elif any(kw in all_text for kw in ['封号', '封了', '限制', '验证', '被封']):
        if '莫名' in all_text or '无缘无故' in all_text or '正常' in all_text:
            problem_scene = '正常使用却被系统误判限制'
        else:
            problem_scene = '功能使用受到限制'
    
    # 组装总结
    if problem_scene:
        summary = f"用户想要{core}，因为{problem_scene}"
    else:
        summary = f"用户希望{core}"
    
    return summary


def generate_ai_description(ai_keywords, ai_score, title):
    """
    根据 AI 关键词生成口语化的介入说明
    说明 AI 如何解决这个问题，而非重复数据统计
    """
    if not ai_keywords or ai_score <= 2:
        # 低分或无关键词，说明 AI 介入空间有限
        return "该问题主要涉及工程实现或平台策略，AI 介入空间有限"
    
    # 关键词到口语化说明的映射
    keyword_explanations = {
        # 客服/对话类
        '智能客服辅助': '用 AI 客服理解用户意图，自动分流常见问题',
        '意图理解': '让 AI 识别用户真实诉求，减少来回沟通的成本',
        '智能客服': '引入 AI 客服处理高频问题，把人工留给复杂场景',
        
        # 内容/推荐类
        '智能排序': '根据用户偏好智能排序内容，把重要的放前面',
        '内容推荐': '用算法推荐用户可能感兴趣的内容',
        'AI编辑': 'AI 辅助用户编辑和润色发布内容',
        '智能推荐': '基于用户画像推荐相关内容',
        '内容理解': '理解内容语义，提供更精准的分类',
        
        # 折叠/过滤类
        '智能判定折叠规则': 'AI 识别长文关键信息，智能决定哪些该折叠',
        '用户可选控制': '用户设置偏好后，AI 学习并记住',
        '智能过滤': '自动过滤低质量或不感兴趣的内容',
        
        # 搜索/发现类
        '语义搜索': '支持自然语言搜索，理解用户想找什么',
        '智能搜索': '增强搜索能力，支持模糊匹配和联想',
        
        # 安全/风控类
        '智能风控': '用 AI 识别风险行为，减少误判正常用户',
        '行为分析': '分析行为模式，区分正常使用和异常',
        
        # 图像/视频类
        'AI超分辨率': '用 AI 超分技术在不增加体积的前提下提升画质',
        '智能压缩优化': '用 AI 算法在压缩时保留更多细节',
        
        # 语音类
        'ASR已成熟': '语音识别技术已成熟，可以做到高准确率',
        '准确率可优化': '通过持续学习用户习惯提升识别准确率',
        
        # 编辑/创作类
        'AI辅助排版': 'AI 帮用户自动调整图文排版',
        '配文建议': 'AI 根据图片内容推荐合适的文案',
        'AI配乐推荐': 'AI 根据图片内容和情绪推荐背景音乐',
        '情绪匹配': '分析内容情绪，推荐匹配的配乐',
        
        # 通知类
        '智能分级': '根据消息重要性智能分级，避免打扰',
        '优先级排序': '重要消息优先提醒，普通消息静默',
        
        # 特殊情况
        '金融合规问题': '涉及金融合规，AI 介入需要配合风控策略',
        '平台策略问题': '这是平台策略问题，需要人工审核流程配合',
        '合规问题为主': '主要是合规问题，AI 可以辅助但不能主导',
        '合规要求': '合规要求决定，AI 只能在规则内优化体验',
        
        # 工程/非AI类
        '工程问题': '这是工程实现问题，需要技术团队优化',
        '非AI问题': '该问题更适合通过产品设计或工程手段解决',
    }
    
    # 生成说明
    explanations = []
    for kw in ai_keywords[:3]:  # 最多取3个关键词
        if kw in keyword_explanations:
            explanations.append(keyword_explanations[kw])
        else:
            # 通用处理：尝试根据关键词构造自然说明
            if 'AI' in kw or '智能' in kw:
                explanations.append(f'借助{kw}提升用户体验')
            elif '优化' in kw or '提升' in kw:
                explanations.append(f'通过{kw}改善当前问题')
    
    if explanations:
        return '；'.join(explanations[:2])  # 最多保留2条说明
    elif ai_keywords:
        return f"可尝试 {'、'.join(ai_keywords[:2])} 等方向优化"
    else:
        return "AI 介入空间待评估"


def convert_to_ai_opportunity(demand, idx, review_map, all_reviews):
    """将需求点转换为 AIOpportunity 格式"""
    priority = determine_priority(demand['mention_count'], demand['ai_score'])
    intervention_type = determine_intervention_type(demand['ai_score'])
    
    # 从原始评论中找出高质量样本
    best_samples = find_best_samples_from_raw(
        demand['title'], 
        demand['ai_keywords'], 
        all_reviews, 
        max_samples=5
    )
    
    # 如果从原始数据找不到足够样本，用 V3 中的样本补充
    v3_samples = []
    for sample in demand['samples']:
        metadata = find_review_metadata(sample['content'], review_map)
        quality = assess_sample_quality(sample['content'], demand['title'], demand['ai_keywords'])
        if quality > 2:  # 降低质量阈值，确保有足够样本
            v3_samples.append({
                'content': sample['content'],
                'author': metadata['author'] if metadata else '',
                'date': metadata['date'] if metadata else '',
                'rating': metadata['rating'] if metadata else sample['rating'],
                'url': metadata['url'] if metadata else '',
                'quality': quality
            })
    
    # 合并两个来源的样本，去重并排序
    all_samples = []
    seen_contents = set()
    
    # 先加入从原始数据找到的高质量样本
    for review in best_samples:
        content = review['content']
        if content not in seen_contents:
            seen_contents.add(content)
            quality = assess_sample_quality(content, demand['title'], demand['ai_keywords'])
            all_samples.append({
                'content': content,
                'author': review['author'],
                'date': review['date'],
                'rating': review['rating'],
                'url': review['url'],
                'quality': quality
            })
    
    # 再加入 V3 中的高质量样本
    for sample in v3_samples:
        if sample['content'] not in seen_contents:
            seen_contents.add(sample['content'])
            all_samples.append(sample)
    
    # 按质量分排序，取前5个
    all_samples.sort(key=lambda x: x['quality'], reverse=True)
    final_samples = all_samples[:5]
    
    # 构建 evidence_samples
    evidence_samples = []
    for sample in final_samples:
        evidence_samples.append({
            'original_text': sample['content'],
            'source': 'App Store - 微信',
            'pain_point_extracted': demand['subcategory'],
            'sentiment_score': 0.2 if sample['rating'] <= 2 else (0.6 if sample['rating'] <= 4 else 0.8),
            'relevance_score': 8.0,
            'content': sample['content'],
            'app_name': '微信',
            'author': sample['author'],
            'date': sample['date'],
            'rating': sample['rating'],
            'source_url': sample['url'] or 'https://apps.apple.com/cn/app/微信/id414478124?see-all=reviews'
        })
    
    # 生成基于所有样本的需求总结（而非单条评论）
    user_voice = generate_demand_summary(demand['title'], final_samples, demand['mention_count'])
    
    return {
        'id': f'wechat_demand_{idx + 1}',
        'title': demand['title'],
        'description': f"用户反馈：{demand['mention_count']}条 | AI介入评分：{demand['ai_score']}/10",
        'ai_intervention_type': intervention_type,
        'user_pain_summary': f"用户反馈了关于「{demand['title']}」的需求",
        'priority': priority,
        'cross_product_relevance': ['wechat'],
        'source_stats': {
            'products_mentioned': ['微信'],
            'sources': ['App Store'],
            'exact_match_count': demand['mention_count']
        },
        'evidence_samples': evidence_samples,
        'mention_count': demand['mention_count'],
        'merged_from': [demand['subcategory']] if demand['subcategory'] else [],
        'ai_solution': f"AI方向：{demand['ai_direction']}" if demand['ai_direction'] else '',
        'ai_description': generate_ai_description(demand['ai_keywords'], demand['ai_score'], demand['title']),
        'ai_keywords': demand['ai_keywords'],
        'ai_score': demand['ai_score'],  # 添加原始评分用于排序
        'user_voice': user_voice,
        'sample_count': len(final_samples)
    }


def main():
    # 先加载原始评论数据
    review_map, all_reviews = load_raw_reviews()
    
    print("正在解析 V3 需求点文件...")
    demands = parse_v3_file(V3_FILE)
    print(f"解析到 {len(demands)} 个需求点")
    
    # 转换为 AIOpportunity 格式
    ai_opportunities = []
    
    for idx, demand in enumerate(demands):
        opp = convert_to_ai_opportunity(demand, idx, review_map, all_reviews)
        ai_opportunities.append(opp)
        sample_count = opp.get('sample_count', 0)
        print(f"  [{idx+1}] {demand['title'][:25]}... - {demand['mention_count']}条反馈, 筛选{sample_count}个高质量样本")
    
    # 排序逻辑：
    # 1. 第一梯队：具体功能缺失/明确问题（优先）
    # 2. 第二梯队：具体能力改进
    # 3. 第三梯队：体验优化类（往后排）
    # 同梯队内按 AI评分 > 提及数 排序
    
    def get_demand_tier(title):
        """判断需求所属梯队，数字越小优先级越高"""
        # 体验优化类关键词（第三梯队，往后排）
        experience_keywords = ['体验更好', '更完善', '更好用', '更稳定', '更及时', '适配更好', '更方便']
        if any(kw in title for kw in experience_keywords):
            return 3
        
        # 具体功能需求关键词（第一梯队）
        feature_keywords = ['希望能', '希望有', '希望可以', '希望增加', '希望添加', '希望支持']
        if any(kw in title for kw in feature_keywords):
            return 1
        
        # 明确问题类（第一梯队）
        problem_keywords = ['被封', '限制', '遇到问题', '太大', '太多', '卡死', '闪退', '崩溃', '黑屏']
        if any(kw in title for kw in problem_keywords):
            return 1
        
        # 其他默认第二梯队（具体能力改进）
        return 2
    
    # 为每个需求点添加梯队标记
    for opp in ai_opportunities:
        opp['demand_tier'] = get_demand_tier(opp['title'])
    
    # 按梯队 > AI评分 > 提及数 排序
    ai_opportunities.sort(key=lambda x: (
        x.get('demand_tier', 2),  # 梯队（小的优先）
        -x.get('ai_score', 0),     # AI评分（大的优先，所以取负）
        -x.get('mention_count', 0) # 提及数（大的优先，所以取负）
    ))
    
    # 重新编号 id
    for idx, opp in enumerate(ai_opportunities):
        opp['id'] = f'wechat_demand_{idx + 1}'
    
    print(f"\n排序后前10条（按新规则：梯队 > AI评分 > 提及数）:")
    tier_names = {1: '功能/问题', 2: '能力改进', 3: '体验优化'}
    for i, opp in enumerate(ai_opportunities[:10]):
        tier = opp.get('demand_tier', 2)
        print(f"  [{i+1}] T{tier}({tier_names[tier]}) AI:{opp.get('ai_score', 0)}/10 | {opp['title'][:25]}...")
    
    # 构建完整的 CategoryAIAnalysis 结构
    output = {
        'category': 'wechat',
        'generated_at': datetime.now().isoformat(),
        'data_sources': ['appstore'],
        'total_items_analyzed': sum(d['mention_count'] for d in demands),
        'ai_opportunities': ai_opportunities
    }
    
    # 写入 JSON 文件
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    total_samples = sum(opp.get('sample_count', 0) for opp in ai_opportunities)
    print(f"\n✅ 已生成: {OUTPUT_FILE}")
    print(f"   共 {len(ai_opportunities)} 个需求点")
    print(f"   总计 {output['total_items_analyzed']} 条用户反馈")
    print(f"   筛选 {total_samples} 个高质量样本")


if __name__ == '__main__':
    main()
