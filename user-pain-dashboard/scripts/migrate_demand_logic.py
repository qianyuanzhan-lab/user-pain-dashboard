#!/usr/bin/env python3
"""
将已验证的需求推演逻辑迁移到 ai/social/more 三个类目
处理逻辑与 convert_v3_to_json.py 一致：
  1. 样本质量过滤（低质量/语义混乱过滤）
  2. 从原始评论重新匹配高质量样本
  3. 生成需求总结（user_voice）
  4. 生成口语化 AI 描述（ai_description）
  5. 梯队排序（功能需求 > 能力改进 > 体验优化）
"""

import json
import re
import os
from datetime import datetime
from pathlib import Path
from collections import defaultdict

BASE = Path(__file__).parent.parent

# ─────────────────────────────────────────
# 低质量过滤规则（与 wechat 保持一致）
# ─────────────────────────────────────────
LOW_QUALITY_PATTERNS = [
    r'^.{0,15}$',
    r'^(垃圾|真垃圾|垃圾软件|差评|一星).{0,10}$',
    r'(加两个0|加个0|给我加钱|还给我钱|还我钱)',
    r'^(好|不好|可以|还行|一般).{0,5}$',
    r'(.)\1{5,}',
    r'^(差评)+\s*(差评)*',
    r'搞抽象|整活|玩梗|os[:：]',
    r'[😭🙃😅🤣😂💀]{2,}',
    r'人民的好软件|良心软件',
    r'(一|有)?个叫.{2,8}的.{0,15}(花|扣|偷|拿).{0,5}(我的)?(钱|money)',
    r'(看|等)\d+秒.{0,5}广告',
]

INCOHERENT_PATTERNS = [
    r'。\s*[？?]',
    r'[？?]\s*[？?]',
    r'什么意思.{0,10}[？?]',
    r'我请问',
    r'你们能不能.{0,10}(管|处理)',
    r'太倒霉',
]

HIGH_QUALITY_INDICATORS = [
    '希望', '建议', '能不能', '可以', '如果', '为什么',
    '每次', '总是', '经常', '一直', '有时候',
    '之前', '以前', '更新后', '现在',
    '工作', '生活', '学习', '重要',
    '导致', '影响', '无法', '不能',
]


def is_incoherent_content(content):
    sentences = re.split(r'[。！？?!]', content)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 3]
    question_marks = content.count('？') + content.count('?')
    if len(sentences) > 0 and question_marks > len(sentences) * 0.5:
        return True
    incoherent_count = sum(1 for p in INCOHERENT_PATTERNS if re.search(p, content))
    if incoherent_count >= 2:
        return True
    if len(sentences) >= 4:
        sentence_keywords = []
        for s in sentences:
            kws = set(re.findall(r'[\u4e00-\u9fa5]{2,4}', s))
            sentence_keywords.append(kws)
        if len(sentence_keywords) >= 3:
            overlaps = []
            for i in range(len(sentence_keywords) - 1):
                overlap = len(sentence_keywords[i] & sentence_keywords[i+1])
                overlaps.append(overlap)
            if sum(overlaps) / len(overlaps) < 0.5:
                return True
    return False


def assess_sample_quality(content, demand_title, demand_keywords):
    score = 5.0
    length = len(content)
    if length < 20:
        return 0
    elif length < 30:
        score -= 2
    elif length >= 50:
        score += 1
    elif length >= 100:
        score += 2

    for pattern in LOW_QUALITY_PATTERNS:
        if re.search(pattern, content):
            return 0

    if is_incoherent_content(content):
        return 0

    high_quality_count = sum(1 for ind in HIGH_QUALITY_INDICATORS if ind in content)
    score += min(high_quality_count * 0.5, 2)

    title_keywords = extract_keywords(demand_title)
    all_keywords = list(title_keywords) + list(demand_keywords)
    relevance_count = sum(1 for kw in all_keywords if kw in content)
    score += min(relevance_count * 0.5, 2)

    has_structure = any([
        '我' in content and ('想' in content or '希望' in content or '建议' in content),
        '能不能' in content or '可以' in content,
        '为什么' in content or '怎么' in content,
        '问题' in content or '功能' in content,
    ])
    if has_structure:
        score += 1

    negative_words = ['垃圾', '恶心', '烂', '死', '傻', '狗', '坑']
    negative_count = sum(1 for w in negative_words if w in content)
    if negative_count >= 3:
        score -= 2

    scenario_indicators = ['使用', '操作', '点击', '打开', '发送', '接收', '查看']
    if any(s in content for s in scenario_indicators):
        score += 0.5

    return max(0, min(10, score))


def extract_keywords(text):
    words = re.findall(r'[\u4e00-\u9fa5]{2,}', text)
    stopwords = {'希望', '能够', '可以', '进行', '使用', '用户', '功能', '问题', '体验', '更好', '更加'}
    return [w for w in words if w not in stopwords]


def find_best_samples_from_raw(demand_title, demand_keywords, all_reviews, max_samples=5):
    scored_reviews = []
    title_keywords = extract_keywords(demand_title)
    all_keywords = set(title_keywords + list(demand_keywords))

    for review in all_reviews:
        content = review['content']
        relevance = sum(1 for kw in all_keywords if kw in content)
        if relevance == 0:
            continue
        quality = assess_sample_quality(content, demand_title, demand_keywords)
        if quality > 2:
            combined_score = quality * 0.6 + min(relevance * 2, 10) * 0.4
            scored_reviews.append((combined_score, review))

    scored_reviews.sort(key=lambda x: x[0], reverse=True)
    return [r[1] for r in scored_reviews[:max_samples]]


def format_date(date_str):
    if not date_str:
        return ''
    try:
        dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        return dt.strftime('%Y-%m-%d')
    except:
        return date_str[:10] if len(date_str) >= 10 else date_str


def generate_demand_summary(title, samples, mention_count):
    if not samples:
        return f"用户希望{title}，但目前体验不佳"

    all_text = ' '.join([s['content'] for s in samples[:5]])
    core = title.replace('希望', '').replace('想要', '').strip()

    problem_scene = None
    if any(kw in all_text for kw in ['模糊', '压缩', '画质', '糊', '不清晰', '失真']):
        problem_scene = '发出去的内容画质被压缩变差'
    elif any(kw in all_text for kw in ['折叠', '被折叠', '误伤']) :
        if '误伤' in all_text or '正常' in all_text:
            problem_scene = '正常发布内容却被误判折叠'
        else:
            problem_scene = '重要信息被折叠看不到'
    elif any(kw in all_text for kw in ['准确', '不准', '识别错', '繁体']):
        problem_scene = '当前识别准确率不够高'
    elif ('以前' in all_text or '之前' in all_text) and ('现在没' in all_text or '不可以了' in all_text or '怎么不' in all_text):
        problem_scene = '之前有这个功能但现在用不了了'
    elif any(kw in all_text for kw in ['增加', '加个', '添加', '新增', '希望有']):
        problem_scene = '目前缺少这个功能'
    elif any(kw in all_text for kw in ['编辑', '修改', '更改', '二次']):
        problem_scene = '发布后无法修改，只能删除重发'
    elif any(kw in all_text for kw in ['人工客服', '找不到客服', '机器人', '转人工']):
        problem_scene = '遇到问题只能找机器人，转不了人工'
    elif any(kw in all_text for kw in ['封号', '封了', '限制', '验证', '被封']):
        if '莫名' in all_text or '无缘无故' in all_text or '正常' in all_text:
            problem_scene = '正常使用却被系统误判限制'
        else:
            problem_scene = '功能使用受到限制'
    elif any(kw in all_text for kw in ['崩溃', '闪退', '卡死', '黑屏', '卡顿']):
        problem_scene = '功能不稳定，频繁崩溃或卡顿'
    elif any(kw in all_text for kw in ['隐私', '泄露', '数据', '安全']):
        problem_scene = '对数据安全和隐私保护存在顾虑'
    elif any(kw in all_text for kw in ['慢', '延迟', '卡']):
        problem_scene = '响应速度慢，影响使用体验'

    if problem_scene:
        return f"用户想要{core}，因为{problem_scene}"
    else:
        return f"用户希望{core}"


def generate_ai_description(ai_keywords, ai_score, title):
    if not ai_keywords or ai_score <= 2:
        return "该问题主要涉及工程实现或平台策略，AI 介入空间有限"

    keyword_explanations = {
        '智能客服辅助': '用 AI 客服理解用户意图，自动分流常见问题',
        '意图理解': '让 AI 识别用户真实诉求，减少来回沟通的成本',
        '智能客服': '引入 AI 客服处理高频问题，把人工留给复杂场景',
        '智能排序': '根据用户偏好智能排序内容，把重要的放前面',
        '内容推荐': '用算法推荐用户可能感兴趣的内容',
        'AI编辑': 'AI 辅助用户编辑和润色发布内容',
        '智能推荐': '基于用户画像推荐相关内容',
        '内容理解': '理解内容语义，提供更精准的分类',
        '智能判定折叠规则': 'AI 识别长文关键信息，智能决定哪些该折叠',
        '用户可选控制': '用户设置偏好后，AI 学习并记住',
        '智能过滤': '自动过滤低质量或不感兴趣的内容',
        '语义搜索': '支持自然语言搜索，理解用户想找什么',
        '智能搜索': '增强搜索能力，支持模糊匹配和联想',
        '智能风控': '用 AI 识别风险行为，减少误判正常用户',
        '行为分析': '分析行为模式，区分正常使用和异常',
        'AI超分辨率': '用 AI 超分技术在不增加体积的前提下提升画质',
        '智能压缩优化': '用 AI 算法在压缩时保留更多细节',
        'ASR已成熟': '语音识别技术已成熟，可以做到高准确率',
        '准确率可优化': '通过持续学习用户习惯提升识别准确率',
        'AI辅助排版': 'AI 帮用户自动调整图文排版',
        '配文建议': 'AI 根据图片内容推荐合适的文案',
        'AI配乐推荐': 'AI 根据图片内容和情绪推荐背景音乐',
        '情绪匹配': '分析内容情绪，推荐匹配的配乐',
        '智能分级': '根据消息重要性智能分级，避免打扰',
        '优先级排序': '重要消息优先提醒，普通消息静默',
        '个性化推荐': '根据用户行为和偏好个性化推荐内容',
        'AI安全检测': 'AI 识别违规内容，减少误判和漏判',
        '隐私保护': '数据本地化处理，减少隐私泄露风险',
        '智能摘要': 'AI 自动提取长文核心信息，快速了解重点',
        '自动翻译': 'AI 实时翻译，打通语言障碍',
        '情感分析': '分析用户情感，提供更贴心的响应',
        '智能对话': 'AI 支持多轮对话，理解上下文语境',
        '知识检索': 'AI 快速检索相关知识，辅助决策',
        '代码辅助': 'AI 辅助代码补全和错误检测',
        '文本生成': 'AI 根据场景自动生成合适的文本内容',
    }

    explanations = []
    for kw in ai_keywords[:3]:
        if kw in keyword_explanations:
            explanations.append(keyword_explanations[kw])
        else:
            if 'AI' in kw or '智能' in kw:
                explanations.append(f'借助{kw}提升用户体验')
            elif '优化' in kw or '提升' in kw:
                explanations.append(f'通过{kw}改善当前问题')

    if explanations:
        return '；'.join(explanations[:2])
    elif ai_keywords:
        return f"可尝试 {'、'.join(ai_keywords[:2])} 等方向优化"
    else:
        return "AI 介入空间待评估"


def get_demand_tier(title):
    """判断需求所属梯队，数字越小优先级越高"""
    experience_keywords = ['体验更好', '更完善', '更好用', '更稳定', '更及时', '适配更好', '更方便', '体验优化']
    if any(kw in title for kw in experience_keywords):
        return 3

    feature_keywords = ['希望能', '希望有', '希望可以', '希望增加', '希望添加', '希望支持']
    if any(kw in title for kw in feature_keywords):
        return 1

    problem_keywords = ['被封', '限制', '遇到问题', '太大', '太多', '卡死', '闪退', '崩溃', '黑屏']
    if any(kw in title for kw in problem_keywords):
        return 1

    return 2


def process_category(category):
    """处理单个类目"""
    print(f"\n{'='*60}")
    print(f"处理类目: {category.upper()}")
    print('='*60)

    # 1. 加载原始评论
    raw_path = BASE / f'data/raw/appstore/{category}_20260423.json'
    with open(raw_path) as f:
        raw_data = json.load(f)

    all_reviews = []
    review_map = {}
    for r in raw_data.get('reviews', []):
        content = r.get('content', '')
        if not content:
            continue
        item = {
            'content': content,
            'author': r.get('author', ''),
            'date': format_date(r.get('date', '')),
            'rating': r.get('rating', 0),
            'app_name': r.get('app_name', ''),
            'url': r.get('url', ''),
        }
        all_reviews.append(item)
        if content not in review_map:
            review_map[content] = item

    print(f"加载原始评论: {len(all_reviews)} 条")

    # 2. 加载已有的 consolidated 数据
    consolidated_path = BASE / f'data/processed/{category}_ai_opportunities_consolidated.json'
    with open(consolidated_path) as f:
        data = json.load(f)

    original_opps = data.get('ai_opportunities', [])
    print(f"原有需求点: {len(original_opps)} 个")

    # 3. 处理每个需求点
    updated_opps = []
    for opp in original_opps:
        title = opp.get('title', '')
        ai_keywords = opp.get('ai_keywords', [])
        ai_score = opp.get('ai_score', 0)
        mention_count = opp.get('mention_count', 0)

        # 移除 HN 单条样本（之前分析过是误匹配）
        orig_samples = opp.get('evidence_samples', [])
        hn_removed = sum(1 for s in orig_samples if 'Hacker News' in s.get('source', ''))

        # 从原始数据中重新筛选高质量样本
        best_samples = find_best_samples_from_raw(title, ai_keywords, all_reviews, max_samples=5)

        # 构建 evidence_samples
        evidence_samples = []
        seen = set()
        for review in best_samples:
            content = review['content']
            if content in seen:
                continue
            seen.add(content)
            rating = review['rating']
            evidence_samples.append({
                'original_text': content,
                'source': f"App Store - {review['app_name']}",
                'pain_point_extracted': title,
                'sentiment_score': 0.2 if rating <= 2 else (0.6 if rating <= 4 else 0.8),
                'relevance_score': 8.0,
                'content': content,
                'app_name': review['app_name'],
                'author': review['author'],
                'date': review['date'],
                'rating': rating,
                'source_url': review['url'],
            })

        # 生成需求总结和AI描述
        user_voice = generate_demand_summary(title, best_samples, mention_count)
        ai_description = generate_ai_description(ai_keywords, ai_score, title)

        # 梯队
        demand_tier = get_demand_tier(title)

        updated_opp = dict(opp)  # 保留原有字段
        updated_opp['evidence_samples'] = evidence_samples
        updated_opp['user_voice'] = user_voice
        updated_opp['ai_description'] = ai_description
        updated_opp['demand_tier'] = demand_tier
        updated_opp['sample_count'] = len(evidence_samples)

        updated_opps.append(updated_opp)

        if hn_removed > 0:
            print(f"  [{title[:20]}...] 移除 {hn_removed} 条HN误匹配，新增 {len(evidence_samples)} 条高质量样本")

    # 4. 排序：梯队 > AI评分 > 提及数
    updated_opps.sort(key=lambda x: (
        x.get('demand_tier', 2),
        -x.get('ai_score', 0),
        -x.get('mention_count', 0),
    ))

    # 重新编号
    for idx, opp in enumerate(updated_opps):
        opp['id'] = f'{category}_demand_{idx + 1}'

    # 5. 保存
    data['ai_opportunities'] = updated_opps
    data['updated_at'] = datetime.now().isoformat()

    with open(consolidated_path, 'w') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    # 统计
    tier_counts = {1: 0, 2: 0, 3: 0}
    for opp in updated_opps:
        tier_counts[opp.get('demand_tier', 2)] += 1

    print(f"完成 ✓ | T1(功能/问题):{tier_counts[1]} T2(能力改进):{tier_counts[2]} T3(体验优化):{tier_counts[3]}")
    print(f"前5条：")
    tier_names = {1: '功能/问题', 2: '能力改进', 3: '体验优化'}
    for i, opp in enumerate(updated_opps[:5]):
        t = opp.get('demand_tier', 2)
        print(f"  [{i+1}] T{t}({tier_names[t]}) AI:{opp.get('ai_score',0)}/10 | {opp['title'][:28]}")


if __name__ == '__main__':
    for cat in ['ai', 'social', 'more']:
        process_category(cat)
    print("\n\n✅ 全部完成！")
