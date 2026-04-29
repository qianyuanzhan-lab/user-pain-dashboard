#!/usr/bin/env python3
"""
需求整合脚本
目的：
1. 合并相似/重叠的痛点需求，让提及数更集中
2. 从合并后的样本池中选择更有说服力的证据
3. 为每个需求生成 AI 介入分析信息
4. 确保每个类目有各自独特的需求（不完全相同）
"""

import json
import os
import re
from typing import List, Dict, Any, Tuple
from collections import defaultdict

# ============================================
# 按类目定制的合并规则
# 每个类目只合并与该类目相关的痛点
# ============================================

# 微信生态：聚焦即时通讯、小程序、支付场景
WECHAT_MERGE_RULES = {
    '消息与通知问题': ['消息延迟', '通知丢失', '通知过多', '已读状态', '消息撤回'],
    '存储与性能': ['占用过大', '清理困难', '卡顿延迟', '耗电发热'],
    '社交压力与隐私': ['互动障碍', '隐私泄露', '行为追踪', '朋友圈压力'],
    '小程序体验': ['小程序卡顿', '小程序闪退', '权限滥用'],
    '支付与转账': ['支付失败', '转账限制', '退款困难'],
    '账号安全': ['账号封禁', '登录失败', '验证繁琐'],
    '客服响应': ['客服难联系', '机器人客服', '问题未解决', '申诉困难'],
}

# 社交娱乐：聚焦匹配、内容、社区氛围
SOCIAL_MERGE_RULES = {
    '匹配与推荐': ['匹配问题', '推荐不准', '信息茧房'],
    '真实性与安全': ['虚假诈骗', '虚假内容', '骚扰信息', '照骗问题'],
    '社区氛围': ['社区氛围', '低质评论', '水军刷屏'],
    '内容质量': ['内容低质', '内容匮乏', '内容重复'],
    '会员与付费': ['付费不值', '会员付费', '订阅扣费', '隐性收费'],
    '应用性能': ['占用过大', '卡顿延迟', '功能崩溃', '耗电发热'],
    '广告干扰': ['广告过多', '广告误触', '开屏广告', '弹窗广告'],
    '账号问题': ['账号封禁', '账号绑定', '登录失败'],
}

# AI 应用：聚焦 AI 能力、响应、成本
AI_MERGE_RULES = {
    'AI 回答质量': ['AI回答质量', 'AI代码质量', 'AI信息过时', 'AI幻觉'],
    'AI 记忆能力': ['AI记忆差', '上下文丢失', '对话遗忘'],
    '使用限制与成本': ['AI使用限制', 'AI定价贵', '次数限制', '积分不足'],
    '响应速度': ['AI响应慢', '生成卡顿', '等待时间长'],
    '内容审核': ['AI过度审核', '敏感词过滤', '创作受限'],
    '存储与性能': ['占用过大', '卡顿延迟', '功能崩溃', '耗电发热'],
    '交互体验': ['操作复杂', '界面丑陋', '功能难找'],
    '账号与付费': ['账号封禁', '付费不值', '订阅扣费'],
}

# 更多场景：办公、教育、效率工具
MORE_MERGE_RULES = {
    '协作效率': ['协作卡顿', '同步延迟', '文档冲突'],
    '会议体验': ['会议卡顿', '音画不同步', '噪音问题', '回声'],
    '通知打扰': ['通知过多', '消息轰炸', '已读压力'],
    '学习功能': ['课程质量', '答题错误', '进度丢失'],
    '工具性能': ['占用过大', '启动缓慢', '卡顿延迟', '耗电发热'],
    '付费问题': ['付费不值', '订阅扣费', '功能阉割'],
    '账号问题': ['账号封禁', '登录失败', '数据同步'],
    '广告问题': ['广告过多', '广告误触', '开屏广告'],
}

# 按类目选择合并规则
CATEGORY_MERGE_RULES = {
    'wechat': WECHAT_MERGE_RULES,
    'social': SOCIAL_MERGE_RULES,
    'ai': AI_MERGE_RULES,
    'more': MORE_MERGE_RULES,
}

# ============================================
# AI 介入分析模板
# 每个痛点类型对应的 AI 解决方案
# ============================================

AI_SOLUTIONS = {
    # 微信生态
    '消息与通知问题': {
        'ai_solution': '智能消息管理',
        'ai_description': 'AI 自动识别消息重要程度，智能分级提醒；学习用户习惯，在合适时机推送；自动归类群消息，提取关键信息摘要',
        'ai_keywords': ['消息分级', '智能提醒', '信息摘要'],
        'user_voice': '群消息太多了，重要的信息经常被淹没',
    },
    '存储与性能': {
        'ai_solution': '智能存储优化',
        'ai_description': 'AI 分析文件使用频率和重要性，自动推荐清理方案；智能压缩不常用内容；后台资源智能调度降低耗电',
        'ai_keywords': ['智能清理', '自动压缩', '资源调度'],
        'user_voice': '占用几十G空间，清理功能又不敢用，怕删掉重要文件',
    },
    '社交压力与隐私': {
        'ai_solution': 'AI 隐私助手',
        'ai_description': 'AI 帮助用户管理社交边界，智能分组可见范围；识别潜在隐私风险并提醒；提供"社交降压"模式',
        'ai_keywords': ['隐私保护', '社交边界', '智能分组'],
        'user_voice': '不想让所有人看到我的朋友圈，分组又太麻烦',
    },
    '小程序体验': {
        'ai_solution': '小程序智能加速',
        'ai_description': 'AI 预测用户常用小程序并预加载；智能缓存管理；优化启动流程减少等待时间',
        'ai_keywords': ['预加载', '智能缓存', '启动优化'],
        'user_voice': '每次打开小程序都要等很久，体验太差了',
    },
    '支付与转账': {
        'ai_solution': '智能支付助手',
        'ai_description': 'AI 识别异常交易并提醒；智能推荐最优支付方式；自动记账和消费分析',
        'ai_keywords': ['风险识别', '智能推荐', '消费分析'],
        'user_voice': '转错账了客服也不管，太难追回了',
    },
    '账号安全': {
        'ai_solution': 'AI 安全守护',
        'ai_description': 'AI 行为分析识别异常登录；智能风控减少误封；提供更便捷的身份验证方式',
        'ai_keywords': ['行为分析', '智能风控', '身份验证'],
        'user_voice': '号被封了申诉好几次都不给解，也不说明原因',
    },
    '客服响应': {
        'ai_solution': 'AI 客服升级',
        'ai_description': '更智能的 AI 客服理解复杂问题；快速转人工通道；问题追踪和进度提醒',
        'ai_keywords': ['智能客服', '问题追踪', '快速响应'],
        'user_voice': '客服永远是机器人回复，问题解决不了',
    },
    
    # 社交娱乐
    '匹配与推荐': {
        'ai_solution': '真实匹配算法',
        'ai_description': 'AI 多维度分析用户真实偏好；打破信息茧房引入新鲜内容；基于深度兴趣而非表面数据匹配',
        'ai_keywords': ['深度匹配', '兴趣挖掘', '茧房破解'],
        'user_voice': '推荐的人都不合适，感觉算法根本不懂我',
    },
    '真实性与安全': {
        'ai_solution': 'AI 真人验证',
        'ai_description': 'AI 图片鉴伪识别照骗；行为分析识别机器人和骗子；实时预警诈骗风险',
        'ai_keywords': ['图片鉴伪', '行为分析', '诈骗预警'],
        'user_voice': '遇到好多假照片和骗子，浪费时间又担心被骗',
    },
    '社区氛围': {
        'ai_solution': 'AI 社区净化',
        'ai_description': 'AI 识别水军和低质内容；维护健康讨论氛围；智能过滤引战和负面信息',
        'ai_keywords': ['内容过滤', '氛围维护', '水军识别'],
        'user_voice': '评论区全是水军和杠精，正常讨论都没法进行',
    },
    '内容质量': {
        'ai_solution': 'AI 内容优选',
        'ai_description': 'AI 识别优质原创内容优先推荐；过滤低质搬运内容；支持用户个性化品味学习',
        'ai_keywords': ['原创优先', '品味学习', '质量筛选'],
        'user_voice': '刷到的内容越来越水，找个有深度的内容太难了',
    },
    '会员与付费': {
        'ai_solution': '智能权益推荐',
        'ai_description': 'AI 分析使用习惯推荐最适合的会员方案；透明化付费项说明；智能提醒避免忘记取消订阅',
        'ai_keywords': ['权益匹配', '透明消费', '订阅管理'],
        'user_voice': '开了会员发现功能都用不上，感觉被坑了',
    },
    '应用性能': {
        'ai_solution': '智能性能优化',
        'ai_description': 'AI 根据使用场景动态调整性能策略；智能预加载常用内容；后台资源智能管理',
        'ai_keywords': ['动态优化', '预加载', '资源管理'],
        'user_voice': '用一会儿就发烫卡顿，电量也掉得飞快',
    },
    '广告干扰': {
        'ai_solution': 'AI 广告优化',
        'ai_description': 'AI 学习用户偏好减少无关广告；智能规避误触设计；提供广告免打扰时段',
        'ai_keywords': ['精准投放', '防误触', '免打扰'],
        'user_voice': '广告又多又容易误点，体验太差了',
    },
    '账号问题': {
        'ai_solution': 'AI 账号守护',
        'ai_description': 'AI 行为分析减少误封；智能身份验证替代繁琐流程；账号异常快速预警',
        'ai_keywords': ['误封减少', '智能验证', '异常预警'],
        'user_voice': '莫名其妙就被封号，申诉也没人理',
    },
    
    # AI 应用
    'AI 回答质量': {
        'ai_solution': '回答质量增强',
        'ai_description': '引入实时信息检索确保时效性；增强专业领域知识；明确标注不确定内容避免幻觉',
        'ai_keywords': ['实时检索', '专业增强', '幻觉标注'],
        'user_voice': '回答经常不准确，尤其是专业问题和最新信息',
    },
    'AI 记忆能力': {
        'ai_solution': '长期记忆系统',
        'ai_description': '构建用户专属记忆库；支持跨对话上下文关联；重要信息永久保存',
        'ai_keywords': ['记忆库', '上下文关联', '永久记忆'],
        'user_voice': '每次对话都要重新说一遍背景，太麻烦了',
    },
    '使用限制与成本': {
        'ai_solution': '智能用量管理',
        'ai_description': 'AI 优化问答效率减少无效消耗；提供更灵活的付费方案；智能推荐最优使用策略',
        'ai_keywords': ['效率优化', '灵活付费', '用量策略'],
        'user_voice': '免费次数用完就要付费，价格还不便宜',
    },
    '响应速度': {
        'ai_solution': '加速响应',
        'ai_description': '边生成边输出减少等待；智能预测常见问题预生成；优化模型推理效率',
        'ai_keywords': ['流式输出', '预生成', '推理优化'],
        'user_voice': '等待回复的时间太长了，急用的时候很着急',
    },
    '内容审核': {
        'ai_solution': '智能审核优化',
        'ai_description': 'AI 理解创作意图减少误判；提供审核解释和修改建议；支持申诉快速响应',
        'ai_keywords': ['意图理解', '修改建议', '快速申诉'],
        'user_voice': '正常创作内容也被审核拦截，创作空间太小了',
    },
    '交互体验': {
        'ai_solution': '自然交互升级',
        'ai_description': 'AI 学习用户习惯自动调整界面；智能功能推荐；提供个性化使用引导',
        'ai_keywords': ['习惯学习', '功能推荐', '个性化引导'],
        'user_voice': '功能太多了找不到，操作也不够直观',
    },
    
    # 更多场景
    '协作效率': {
        'ai_solution': 'AI 协作助手',
        'ai_description': 'AI 自动处理文档冲突；智能任务分配和进度追踪；自动生成会议纪要',
        'ai_keywords': ['冲突处理', '任务追踪', '纪要生成'],
        'user_voice': '多人协作经常冲突，同步也老出问题',
    },
    '会议体验': {
        'ai_solution': 'AI 会议增强',
        'ai_description': 'AI 实时降噪和回声消除；智能字幕和翻译；自动提取会议要点',
        'ai_keywords': ['智能降噪', '实时字幕', '要点提取'],
        'user_voice': '会议经常听不清，网络一卡就跟不上了',
    },
    '通知打扰': {
        'ai_solution': '智能勿扰模式',
        'ai_description': 'AI 识别消息重要程度智能分级；学习工作节奏自动调整通知时机；紧急消息才打扰',
        'ai_keywords': ['消息分级', '节奏学习', '智能打扰'],
        'user_voice': '工作群消息太多了，重要的总是漏看',
    },
    '学习功能': {
        'ai_solution': 'AI 学习助手',
        'ai_description': 'AI 个性化学习路径规划；智能答疑和错题分析；学习进度智能提醒',
        'ai_keywords': ['路径规划', '智能答疑', '进度提醒'],
        'user_voice': '题目讲解不清楚，遇到问题找不到人问',
    },
    '工具性能': {
        'ai_solution': '智能性能调优',
        'ai_description': 'AI 分析使用模式优化资源分配；智能清理缓存；后台任务智能调度',
        'ai_keywords': ['资源优化', '智能清理', '任务调度'],
        'user_voice': '软件越用越卡，占用空间也越来越大',
    },
    '付费问题': {
        'ai_solution': '智能订阅管理',
        'ai_description': 'AI 分析使用情况推荐最优方案；到期提醒和自动续费管理；权益使用透明展示',
        'ai_keywords': ['方案推荐', '续费管理', '权益透明'],
        'user_voice': '开了会员但很多功能用不上，感觉不值',
    },
    '广告问题': {
        'ai_solution': 'AI 广告过滤',
        'ai_description': 'AI 学习用户偏好精准过滤无关广告；智能防误触机制；提供无广告专注模式',
        'ai_keywords': ['精准过滤', '防误触', '专注模式'],
        'user_voice': '广告太多影响使用，还总是容易误点',
    },
}

# 默认 AI 方案（兜底）
# 注意：这个兜底方案仅作最后的保险，不应该被大量使用。
# 如果某个痛点标题匹配到这里，说明 AI_SOLUTIONS 需要扩充。
# 同时运行 scripts/fix_generic_user_voice.py 和 fix_ai_subtype_voice.py 补充独立文案。
DEFAULT_AI_SOLUTION = {
    'ai_solution': '待分析',
    'ai_description': '该需求暂未匹配到预定义方案，请扩充 AI_SOLUTIONS 或运行 fix_generic_user_voice.py 补充',
    'ai_keywords': ['待补充'],
    'user_voice': '用户反馈了此问题但未归入已知类别，需进一步分析',
}

# 样本质量评分规则
def score_sample(sample: Dict, pain_title: str = None) -> float:
    """
    评估样本质量，分数越高越好
    增强相关性权重：样本必须直接描述问题本身
    """
    text = sample.get('original_text', '')
    score = 0.0
    
    # 0. 优先使用预计算的相关性分数（如果有）
    if 'relevance_score' in sample:
        score += sample['relevance_score'] * 0.5  # 相关性分数占一半权重
    
    # 1. 长度适中（50-200字最佳）
    length = len(text)
    if 50 <= length <= 200:
        score += 3.0
    elif 30 <= length <= 300:
        score += 2.0
    elif length > 10:
        score += 1.0
    
    # 2. 包含具体场景描述（加分）
    scenario_keywords = ['每次', '经常', '总是', '一直', '已经', '好几次', '多次', 
                        '昨天', '今天', '刚才', '之前', '最近']
    for kw in scenario_keywords:
        if kw in text:
            score += 1.0
            break
    
    # 3. 包含具体问题描述（加分）- 增强权重
    problem_patterns = ['无法', '不能', '失败', '出错', '崩溃', '闪退', '卡住',
                       '收不到', '发不出', '打不开', '加载不了', '显示不了',
                       '一直', '老是', '又', '还是']
    problem_count = sum(1 for p in problem_patterns if p in text)
    score += min(problem_count * 0.8, 3.0)  # 最多加 3 分
    
    # 4. 情感强度（中等情感比极端更可信）
    sentiment = sample.get('sentiment_score', 0.5)
    if 0.3 <= sentiment <= 0.7:
        score += 1.0
    
    # 5. 包含对比或建议（加分）
    if any(kw in text for kw in ['希望', '建议', '应该', '可以', '以前', '之前还']):
        score += 1.5
    
    # 6. 避免纯情绪宣泄（减分）- 加强惩罚
    emo_only = ['垃圾', '辣鸡', '差评', '一星', '烂', '坑', '傻逼', '脑残', '智障']
    if any(text.strip().startswith(kw) or text.strip() == kw for kw in emo_only):
        score -= 3.0
    
    # 7. 避免太短或无实质内容
    if length < 15:
        score -= 2.0
    elif text.count('。') == 0 and text.count('，') == 0 and length < 30:
        score -= 1.0
    
    # 8. 避免通用/模糊的评价（减分）
    vague_patterns = ['还行', '一般', '凑合', '就那样', '马马虎虎', '还好吧']
    if any(vp in text for vp in vague_patterns):
        score -= 1.5
    
    # 9. 如果有痛点标题，检查是否直接相关
    if pain_title:
        # 直接提到痛点关键词的加分
        pain_keywords = {
            '卡顿': ['卡', '慢', '延迟', '卡顿', '卡死'],
            '闪退': ['闪退', '崩溃', '闪', '退出'],
            '广告': ['广告', '弹窗', '推广'],
            '存储': ['内存', '空间', '存储', '占用', 'G'],
            '通知': ['通知', '消息', '提醒', '收不到'],
            '封禁': ['封', '禁', '账号', '限制'],
            'AI': ['AI', '智能', '回答', '生成'],
        }
        for key, kws in pain_keywords.items():
            if key in pain_title:
                if any(kw in text for kw in kws):
                    score += 2.0
                break
    
    return score


def find_merge_target(title: str, category: str) -> str:
    """查找痛点应该合并到哪个目标（按类目使用不同规则）"""
    merge_rules = CATEGORY_MERGE_RULES.get(category, {})
    
    for target, sources in merge_rules.items():
        if title == target:
            return target
        for source in sources:
            if source in title or title in source:
                return target
    return title  # 不合并，保持原样


def get_ai_solution_info(title: str) -> Dict[str, Any]:
    """获取痛点对应的 AI 解决方案信息"""
    # 精确匹配
    if title in AI_SOLUTIONS:
        return AI_SOLUTIONS[title]
    
    # 去除空格后再精确匹配一次（兼容 'AI 回答质量' / 'AI回答质量'）
    title_stripped = title.replace(' ', '')
    for key in AI_SOLUTIONS:
        if key.replace(' ', '') == title_stripped:
            return AI_SOLUTIONS[key]
    
    # 模糊匹配（只在 key 长度 >= 4 且完全包含时命中，避免短关键词误匹配）
    for key, solution in AI_SOLUTIONS.items():
        if len(key) >= 4 and (key in title or title in key):
            return solution
    
    return DEFAULT_AI_SOLUTION


def consolidate_opportunities(data: Dict, category: str) -> Dict:
    """整合痛点需求（按类目使用不同的合并规则）"""
    opportunities = data.get('ai_opportunities', [])
    
    # 按合并目标分组（使用类目特定的规则）
    merged_groups: Dict[str, List[Dict]] = defaultdict(list)
    for opp in opportunities:
        target = find_merge_target(opp['title'], category)
        merged_groups[target].append(opp)
    
    # 生成合并后的痛点列表
    new_opportunities = []
    for target_title, group in merged_groups.items():
        if len(group) == 1:
            # 不需要合并
            opp = group[0].copy()
            opp['merged_from'] = None
        else:
            # 需要合并
            opp = merge_opportunities(target_title, group)
        
        # 优选样本，传入痛点标题用于相关性评分
        opp['evidence_samples'] = select_best_samples(
            opp.get('evidence_samples', []), 
            max_count=5,
            pain_title=target_title
        )
        
        # 重新计算提及数
        total_mentions = sum(
            g.get('source_stats', {}).get('exact_match_count', 0) 
            for g in group
        )
        opp['source_stats'] = opp.get('source_stats', {})
        opp['source_stats']['exact_match_count'] = total_mentions
        opp['mention_count'] = total_mentions
        
        # 更新描述
        merged_names = [g['title'] for g in group] if len(group) > 1 else None
        if merged_names:
            opp['description'] = f"整合了「{'、'.join(merged_names[:3])}」等 {len(group)} 类相关反馈，共 {total_mentions} 条提及"
            opp['merged_from'] = merged_names
        else:
            opp['description'] = f"共 {total_mentions} 条用户反馈提及此问题"
        
        # 添加 AI 解决方案信息
        ai_info = get_ai_solution_info(target_title)
        opp['ai_solution'] = ai_info['ai_solution']
        opp['ai_description'] = ai_info['ai_description']
        opp['ai_keywords'] = ai_info['ai_keywords']
        opp['user_voice'] = ai_info['user_voice']
        
        new_opportunities.append(opp)
    
    # 按提及数排序
    new_opportunities.sort(key=lambda x: x.get('mention_count', 0), reverse=True)
    
    # 更新数据
    new_data = data.copy()
    new_data['ai_opportunities'] = new_opportunities
    new_data['consolidation_stats'] = {
        'original_count': len(opportunities),
        'consolidated_count': len(new_opportunities),
        'merged_groups': len([g for g in merged_groups.values() if len(g) > 1]),
    }
    
    return new_data


def merge_opportunities(title: str, group: List[Dict]) -> Dict:
    """合并多个痛点为一个"""
    # 以第一个为基础
    merged = group[0].copy()
    merged['title'] = title
    merged['id'] = f"{merged['id'].split('_')[0]}_{title.replace(' ', '_')[:20]}"
    
    # 合并所有样本
    all_samples = []
    all_products = set()
    all_sources = set()
    
    for opp in group:
        all_samples.extend(opp.get('evidence_samples', []))
        stats = opp.get('source_stats', {})
        all_products.update(stats.get('products_mentioned', []))
        all_sources.update(stats.get('sources', []))
    
    merged['evidence_samples'] = all_samples
    merged['source_stats'] = {
        'products_mentioned': list(all_products)[:10],
        'sources': list(all_sources),
    }
    
    return merged


def select_best_samples(samples: List[Dict], max_count: int = 5, pain_title: str = None) -> List[Dict]:
    """选择最佳样本，优先选择与痛点高度相关的"""
    if not samples:
        return []
    
    # 评分并排序，传入痛点标题用于相关性评估
    scored = [(sample, score_sample(sample, pain_title)) for sample in samples]
    scored.sort(key=lambda x: x[1], reverse=True)
    
    # 去重（避免内容太相似的样本）
    selected = []
    seen_texts = set()
    
    for sample, score in scored:
        text = sample.get('original_text', '').strip()
        if not text:
            continue
        
        # 用前50字符做去重key
        text_key = text[:50]
        
        # 检查是否和已选的样本太相似
        is_duplicate = False
        for seen in seen_texts:
            # 计算相似度（简单的字符重叠）
            overlap = sum(1 for c in text_key if c in seen)
            if overlap > len(text_key) * 0.6:
                is_duplicate = True
                break
        
        if not is_duplicate and score > 0:
            selected.append(sample)
            seen_texts.add(text_key)
            
            if len(selected) >= max_count:
                break
    
    return selected


def process_category(category: str):
    """处理单个类目"""
    input_path = f'data/processed/{category}_ai_opportunities.json'
    output_path = f'data/processed/{category}_ai_opportunities_consolidated.json'
    
    if not os.path.exists(input_path):
        print(f"  ⚠️ {input_path} 不存在")
        return None
    
    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    original_count = len(data.get('ai_opportunities', []))
    consolidated = consolidate_opportunities(data, category)  # 传入类目
    new_count = len(consolidated.get('ai_opportunities', []))
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(consolidated, f, ensure_ascii=False, indent=2)
    
    print(f"  {category}: {original_count} → {new_count} 个痛点")
    return consolidated


def main():
    """主函数"""
    print("=" * 50)
    print("需求整合脚本")
    print("=" * 50)
    
    os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    categories = ['wechat', 'social', 'ai', 'more']
    
    for cat in categories:
        result = process_category(cat)
        if result:
            stats = result.get('consolidation_stats', {})
            print(f"    合并了 {stats.get('merged_groups', 0)} 组相似需求")
    
    print("\n✅ 整合完成")
    print("输出文件：data/processed/*_ai_opportunities_consolidated.json")


if __name__ == '__main__':
    main()
