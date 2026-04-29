#!/usr/bin/env python3
"""
从所有数据源提取需求点 - V2 版本
整合 App Store + HackerNews 数据
支持更细粒度的痛点识别，允许差异化的小众需求
"""
import json
import os
import re
from collections import defaultdict, Counter
from datetime import datetime
import hashlib

# 数据源配置
DATA_SOURCES = {
    'appstore': {
        'path': 'data/raw/appstore',
        'content_key': 'reviews',
        'text_field': 'content',
        'rating_field': 'rating',
        'app_field': 'app_name',
        'source_name': 'App Store'
    },
    'hackernews': {
        'path': 'data/raw/hackernews',
        'content_key': 'comments',
        'text_field': 'content',  # HN 用 content 字段
        'rating_field': None,  # HN 没有评分
        'app_field': 'story_title',
        'source_name': 'Hacker News'
    }
}

# 更细粒度的痛点关键词（支持中英文）
PAIN_PATTERNS = {
    # ===== 性能稳定性 =====
    'crash_startup': {'keywords': ['打不开', '启动', '闪退', '黑屏', '白屏', "won't open", 'crash on start', 'black screen'], 'category': '启动崩溃'},
    'crash_feature': {'keywords': ['崩溃', '闪', '死机', '卡死', 'crash', 'freeze', 'hang', 'stuck'], 'category': '功能崩溃'},
    'lag_general': {'keywords': ['卡顿', '卡', '慢', '延迟', 'slow', 'lag', 'latency', 'delay'], 'category': '卡顿延迟'},
    'lag_video': {'keywords': ['视频卡', '播放卡', '加载慢', 'video lag', 'buffering', 'loading'], 'category': '视频卡顿'},
    'lag_scroll': {'keywords': ['滑动卡', '刷新慢', '翻页', 'scroll lag', 'janky'], 'category': '滚动卡顿'},
    'battery': {'keywords': ['耗电', '发热', '发烫', '电量', 'battery', 'drain', 'hot', 'overheating'], 'category': '耗电发热'},
    
    # ===== 广告骚扰 =====
    'ads_splash': {'keywords': ['开屏', '启动广告', '开机广告', 'splash ad', 'startup ad'], 'category': '开屏广告'},
    'ads_popup': {'keywords': ['弹窗', '弹出', '强制', '关不掉', 'popup', 'intrusive', "can't close"], 'category': '弹窗广告'},
    'ads_mistouch': {'keywords': ['误触', '误点', '跳转', '摇一摇', 'accidental click', 'misclick', 'redirect'], 'category': '广告误触'},
    'ads_frequency': {'keywords': ['广告太多', '全是广告', '到处广告', 'too many ads', 'ads everywhere', 'ad overload'], 'category': '广告过多'},
    'ads_video': {'keywords': ['中插', '视频广告', '看广告', 'video ad', 'pre-roll', 'mid-roll'], 'category': '视频广告'},
    
    # ===== 收费问题 =====
    'pay_subscription': {'keywords': ['自动续费', '扣费', '订阅', '取消不了', 'auto-renew', 'subscription', "can't cancel", 'charged'], 'category': '订阅扣费'},
    'pay_vip': {'keywords': ['会员', 'VIP', '付费', '收费', 'premium', 'paywall', 'paid feature'], 'category': '会员付费'},
    'pay_hidden': {'keywords': ['隐藏收费', '套路', '诱导', '不透明', 'hidden fee', 'dark pattern', 'misleading'], 'category': '隐性收费'},
    'pay_refund': {'keywords': ['退款', '退钱', '充错', '误充', 'refund', 'money back', 'wrong purchase'], 'category': '退款困难'},
    'pay_worth': {'keywords': ['不值', '缩水', '虚假', '骗钱', 'not worth', 'scam', 'ripoff', 'waste of money'], 'category': '付费不值'},
    
    # ===== 账号封禁 =====
    'ban_account': {'keywords': ['封号', '封禁', '账号被封', '永久封', 'banned', 'suspended', 'account disabled', 'terminated'], 'category': '账号封禁'},
    'ban_mute': {'keywords': ['禁言', '限制', '违规', 'muted', 'restricted', 'violation', 'shadow ban'], 'category': '禁言限制'},
    'ban_appeal': {'keywords': ['申诉', '解封', '找回', '无门', 'appeal', 'unban', 'no response', 'ignored'], 'category': '申诉困难'},
    'ban_device': {'keywords': ['设备封', '换手机', '新设备', 'device ban', 'hardware ban'], 'category': '设备封禁'},
    
    # ===== 客服支持 =====
    'support_unreachable': {'keywords': ['客服', '联系不上', '找不到', '没人', 'support', 'contact', 'no response', 'unreachable'], 'category': '客服难联系'},
    'support_bot': {'keywords': ['机器人', '自动回复', '智能客服', '不是人', 'bot', 'automated', 'not human', 'canned response'], 'category': '机器人客服'},
    'support_slow': {'keywords': ['回复慢', '没回应', '不处理', '推诿', 'slow response', 'no reply', 'ignored'], 'category': '响应缓慢'},
    'support_useless': {'keywords': ['没用', '不解决', '敷衍', '踢皮球', 'useless', 'unhelpful', "doesn't fix"], 'category': '问题未解决'},
    
    # ===== 隐私安全 =====
    'privacy_permission': {'keywords': ['权限', '要权限', '强制授权', 'permission', 'access', 'require'], 'category': '权限滥用'},
    'privacy_data': {'keywords': ['隐私', '泄露', '个人信息', '信息安全', 'privacy', 'data leak', 'personal data', 'tracking'], 'category': '隐私泄露'},
    'privacy_track': {'keywords': ['追踪', '监控', '定位', '偷听', 'tracking', 'surveillance', 'location', 'listening'], 'category': '行为追踪'},
    'scam_fake': {'keywords': ['诈骗', '骗子', '假', '托', 'scam', 'fake', 'fraud', 'phishing'], 'category': '虚假诈骗'},
    'scam_harass': {'keywords': ['骚扰', '垃圾', '推销', '私信', 'spam', 'harass', 'unwanted', 'dm'], 'category': '骚扰信息'},
    
    # ===== 推荐算法 =====
    'recommend_irrelevant': {'keywords': ['推荐', '不感兴趣', '乱推', '垃圾推荐', 'recommendation', 'not interested', 'irrelevant', 'bad suggestion'], 'category': '推荐不准'},
    'recommend_repeat': {'keywords': ['重复', '老是', '一直推', '刷不出新', 'repetitive', 'same content', 'stale'], 'category': '内容重复'},
    'recommend_addictive': {'keywords': ['沉迷', '上瘾', '停不下来', '时间', 'addictive', 'time sink', 'doom scroll', 'waste time'], 'category': '算法成瘾'},
    'recommend_echo': {'keywords': ['信息茧房', '同质', '偏激', 'echo chamber', 'filter bubble', 'bias', 'polarizing'], 'category': '信息茧房'},
    
    # ===== 消息通知 =====
    'notif_delay': {'keywords': ['消息延迟', '收不到', '漏消息', '不及时', 'delayed', 'missed notification', 'late'], 'category': '消息延迟'},
    'notif_spam': {'keywords': ['通知太多', '推送', '骚扰', '关不掉', 'too many notifications', 'spam notification', 'annoying'], 'category': '通知过多'},
    'notif_missing': {'keywords': ['没通知', '静音', '漏掉', 'no notification', 'silent', 'missed'], 'category': '通知丢失'},
    
    # ===== 搜索功能 =====
    'search_poor': {'keywords': ['搜索', '找不到', '搜不到', '搜索功能', 'search', "can't find", 'poor search', 'search broken'], 'category': '搜索差'},
    'search_history': {'keywords': ['历史', '记录', '找聊天', '找消息', 'history', 'find message', 'old conversation'], 'category': '记录难找'},
    
    # ===== 存储空间 =====
    'storage_large': {'keywords': ['占空间', '内存', '存储', '太大', 'G', 'storage', 'space', 'bloated', 'large size'], 'category': '占用过大'},
    'storage_clean': {'keywords': ['清理', '缓存', '删不掉', '越来越大', 'cache', 'clear', "can't delete", 'growing'], 'category': '清理困难'},
    'storage_expire': {'keywords': ['过期', '失效', '打不开', '文件', 'expired', 'invalid', "can't open", 'file'], 'category': '文件过期'},
    
    # ===== 界面体验 =====
    'ui_complex': {'keywords': ['复杂', '难用', '不好用', '反人类', 'complex', 'hard to use', 'confusing', 'bad ux'], 'category': '操作复杂'},
    'ui_ugly': {'keywords': ['丑', '难看', '界面', '设计', 'ugly', 'bad design', 'outdated ui', 'looks bad'], 'category': '界面丑陋'},
    'ui_font': {'keywords': ['字体', '太小', '看不清', '字号', 'font', 'too small', "can't read", 'text size'], 'category': '字体问题'},
    'ui_dark': {'keywords': ['深色', '夜间', '护眼', '暗黑', 'dark mode', 'night mode', 'eye strain'], 'category': '暗色模式'},
    
    # ===== 语音功能 =====
    'voice_convert': {'keywords': ['语音转文字', '转写', '识别', '不准', 'speech to text', 'transcription', 'voice recognition', 'inaccurate'], 'category': '语音转文字'},
    'voice_long': {'keywords': ['长语音', '60秒', '语音太长', 'long voice', 'voice message'], 'category': '长语音'},
    'voice_control': {'keywords': ['快进', '倍速', '进度', '语音', 'fast forward', 'playback speed', 'scrub'], 'category': '语音控制'},
    
    # ===== 登录注册 =====
    'login_fail': {'keywords': ['登录不了', '登录失败', '进不去', "can't login", 'login failed', "can't sign in"], 'category': '登录失败'},
    'login_verify': {'keywords': ['验证', '验证码', '人机', '频繁', 'captcha', 'verification', 'too many attempts'], 'category': '验证繁琐'},
    'login_bind': {'keywords': ['绑定', '换绑', '手机号', '解绑', 'link account', 'phone number', 'unbind'], 'category': '账号绑定'},
    
    # ===== 内容质量 =====
    'content_low': {'keywords': ['低质', '垃圾内容', '无聊', '水', 'low quality', 'junk', 'boring', 'filler'], 'category': '内容低质'},
    'content_fake': {'keywords': ['假新闻', '谣言', '虚假', '标题党', 'fake news', 'misinformation', 'clickbait'], 'category': '虚假内容'},
    'content_missing': {'keywords': ['没内容', '内容少', '更新少', 'no content', 'empty', 'no updates'], 'category': '内容匮乏'},
    
    # ===== 社交功能 =====
    'social_match': {'keywords': ['匹配', '推荐人', '假人', '机器人', 'match', 'fake profile', 'bot', 'catfish'], 'category': '匹配问题'},
    'social_interact': {'keywords': ['互动', '回复', '私信', '聊天', 'interaction', 'reply', 'dm', 'chat'], 'category': '互动障碍'},
    'social_toxic': {'keywords': ['喷子', '骂', '戾气', '素质', 'toxic', 'hate', 'harassment', 'troll'], 'category': '社区氛围'},
    
    # ===== AI 相关 =====
    'ai_quota': {'keywords': ['限额', '次数', '配额', '用完', '上限', 'limit', 'quota', 'rate limit', 'usage cap', 'ran out'], 'category': 'AI使用限制'},
    'ai_quality': {'keywords': ['回答不准', '胡说', '瞎编', '不靠谱', '幻觉', 'hallucination', 'wrong answer', 'inaccurate', 'makes up', 'incorrect'], 'category': 'AI回答质量'},
    'ai_slow': {'keywords': ['回复慢', '生成慢', '等很久', '响应', 'slow response', 'takes forever', 'waiting', 'latency'], 'category': 'AI响应慢'},
    'ai_context': {'keywords': ['记不住', '上下文', '忘记', '断片', 'context', 'forgets', 'memory', 'lost context', "doesn't remember"], 'category': 'AI记忆差'},
    'ai_censor': {'keywords': ['敏感', '审核', '拒绝', '不能说', 'censored', 'refused', 'filtered', "won't answer", 'blocked'], 'category': 'AI过度审核'},
    'ai_network': {'keywords': ['联网', '实时', '过时', '最新', 'outdated', 'not real-time', 'old data', 'internet', 'offline'], 'category': 'AI信息过时'},
    'ai_cost': {'keywords': ['太贵', '价格', '费用', 'expensive', 'costly', 'pricing', 'price', 'overpriced'], 'category': 'AI定价贵'},
    # 注意：ai_code 只匹配 AI/ChatGPT/代码生成 相关的质量问题，不匹配产品 bug
    # 需要同时包含 AI 相关词 + 代码相关词才算匹配
    'ai_code': {
        'keywords': ['AI代码', 'ChatGPT代码', '代码生成', 'AI写的代码', '生成的代码', 'code wrong', 'bad code', 'syntax error', 'AI code'], 
        'category': 'AI代码质量',
        'require_context': ['AI', 'ChatGPT', '代码生成', 'code generation', 'language model']
    },
    'ai_safety': {'keywords': ['安全', '数据安全', '泄密', 'security', 'data breach', 'leak', 'confidential'], 'category': 'AI安全顾虑'},
    
    # ===== 更多细分 =====
    'update_forced': {'keywords': ['强制更新', '必须更新', '不更新不能用', 'forced update', 'must update', "can't use without update"], 'category': '强制更新'},
    'update_regression': {'keywords': ['更新后', '变差', '不如以前', '退步', 'after update', 'worse', 'regression', 'downgrade'], 'category': '更新变差'},
    'compatibility': {'keywords': ['不兼容', '适配', '系统', '版本', 'incompatible', 'not supported', 'version', 'compatibility'], 'category': '兼容性'},
    'offline': {'keywords': ['离线', '没网', '断网', '网络', 'offline', 'no internet', 'connectivity', 'network error'], 'category': '离线功能'},
}

# 类目特定的 AI 介入类型映射
AI_INTERVENTION_TYPES = {
    'crash': '深度介入',
    'lag': '深度介入',
    'ads': '轻量介入',
    'pay': '深度介入',
    'ban': '深度介入',
    'support': '深度介入',
    'privacy': '轻量介入',
    'scam': '深度介入',
    'recommend': '深度介入',
    'notif': '轻量介入',
    'search': '深度介入',
    'storage': '轻量介入',
    'ui': '轻量介入',
    'voice': '深度介入',
    'login': '深度介入',
    'content': '深度介入',
    'social': '深度介入',
    'ai': '深度介入',
    'update': '轻量介入',
    'compatibility': '轻量介入',
    'offline': '轻量介入',
    'battery': '轻量介入',
}


def load_all_data(category):
    """从所有数据源加载指定类目的数据"""
    all_items = []
    
    for source_id, config in DATA_SOURCES.items():
        source_path = config['path']
        
        # 查找该类目的数据文件
        if not os.path.exists(source_path):
            continue
            
        for f in os.listdir(source_path):
            if f.startswith(category) and f.endswith('.json'):
                filepath = os.path.join(source_path, f)
                with open(filepath, encoding='utf-8') as fp:
                    data = json.load(fp)
                
                items = data.get(config['content_key'], [])
                
                for item in items:
                    text = item.get(config['text_field'], '')
                    rating = item.get(config['rating_field']) if config['rating_field'] else None
                    app = item.get(config['app_field'], config['source_name'])
                    
                    # 对于 HackerNews，所有评论都保留（没有评分机制）
                    # 对于 App Store，只保留 3 星及以下的负面评论
                    if rating is None or rating <= 3:
                        all_items.append({
                            'text': text,
                            'rating': rating,
                            'app': app,
                            'source': config['source_name']
                        })
    
    return all_items


def calculate_relevance_score(text: str, keywords: list, category_name: str, require_context: list = None) -> float:
    """
    计算文本与痛点的相关性分数
    分数越高，相关性越强
    
    require_context: 如果提供，文本中必须至少包含一个上下文词才能匹配
    """
    score = 0.0
    text_lower = text.lower()
    
    # 0. 上下文验证（如果配置了 require_context）
    if require_context:
        has_context = any(ctx.lower() in text_lower for ctx in require_context)
        if not has_context:
            return 0.0  # 完全没有上下文，直接返回 0 分
    
    # 1. 关键词匹配数量（每匹配一个关键词 +2 分）
    matched_keywords = []
    for kw in keywords:
        if kw.lower() in text_lower:
            matched_keywords.append(kw)
            score += 2.0
    
    # 2. 关键词密度（关键词出现次数 / 文本长度）
    if len(text) > 10:
        total_matches = sum(text_lower.count(kw.lower()) for kw in matched_keywords)
        density = total_matches / (len(text) / 50)  # 每 50 字出现一次算标准
        score += min(density * 2, 4)  # 最多 +4 分
    
    # 3. 负面情感词共现（说明是在抱怨而非其他语境）
    negative_markers = ['不', '没', '无法', '失败', '出错', '问题', '差', '烂', '坑', 
                       '难', '慢', '卡', '崩', '闪', '死', '废', '坏', '糟', '恶心',
                       "can't", "won't", "doesn't", "failed", "error", "bug", "slow", "bad"]
    for marker in negative_markers:
        if marker in text_lower:
            score += 1.0
            break  # 只加一次
    
    # 4. 具体场景描述（加分）
    scenario_words = ['每次', '经常', '总是', '一直', '好几次', '刚才', '今天', '昨天',
                     'every time', 'always', 'often', 'keeps', 'again']
    for word in scenario_words:
        if word in text_lower:
            score += 1.5
            break
    
    # 5. 文本长度适中（20-200 字为佳）
    if 20 <= len(text) <= 200:
        score += 1.0
    elif len(text) < 10:
        score -= 2.0  # 太短的惩罚
    
    # 6. 避免误匹配：如果文本太通用/模糊，降分
    # 例如只是提到关键词但不是在抱怨
    positive_context = ['喜欢', '好用', '不错', '推荐', '支持', '感谢', 'love', 'great', 'good', 'nice', 'thanks']
    for word in positive_context:
        if word in text_lower:
            score -= 2.0
            break
    
    return max(score, 0)  # 不能为负


def extract_pain_points(items, category):
    """从评论中提取痛点，增强相关性判断"""
    pain_stats = defaultdict(lambda: {
        'count': 0,
        'samples': [],  # 改为存储 (text, score, metadata) 元组
        'apps': set(),
        'sources': set(),
        'ratings': []
    })
    
    # 相关性阈值：低于此分数的不计入
    RELEVANCE_THRESHOLD = 3.0
    
    for item in items:
        text = item['text']
        if not text or len(text) < 10:
            continue
            
        # 匹配所有痛点模式
        for pattern_id, config in PAIN_PATTERNS.items():
            keywords = config['keywords']
            category_name = config.get('category', pattern_id)
            
            # 先做快速过滤：至少包含一个关键词
            has_keyword = False
            for keyword in keywords:
                if keyword.lower() in text.lower():
                    has_keyword = True
                    break
            
            # 如果配置了 require_context，还需要检查上下文
            if not has_keyword:
                continue
            require_ctx = config.get('require_context')
            if require_ctx:
                has_context = any(ctx.lower() in text.lower() for ctx in require_ctx)
                if not has_context:
                    continue
            
            # 计算相关性分数
            relevance_score = calculate_relevance_score(text, keywords, category_name, config.get('require_context'))
            
            # 只有超过阈值才计入
            if relevance_score < RELEVANCE_THRESHOLD:
                continue
            
            stats = pain_stats[pattern_id]
            stats['count'] += 1
            stats['apps'].add(item['app'])
            stats['sources'].add(item['source'])
            if item['rating']:
                stats['ratings'].append(item['rating'])
            
            # 存储样本及其相关性分数（保留更多候选样本）
            if len(stats['samples']) < 50:  # 先保留 50 条候选
                stats['samples'].append({
                    'text': text[:300],  # 保留更多文本用于展示
                    'app': item['app'],
                    'source': item['source'],
                    'rating': item['rating'],
                    'relevance_score': relevance_score
                })
    
    # 对每个痛点的样本按相关性排序，只保留最相关的 10 条
    for pattern_id, stats in pain_stats.items():
        stats['samples'].sort(key=lambda x: x.get('relevance_score', 0), reverse=True)
        stats['samples'] = stats['samples'][:10]
    
    return pain_stats


def calculate_priority(count, avg_rating, num_sources):
    """根据统计数据计算优先级"""
    # 基础分数
    score = 0
    
    # 提及数量权重（最多 40 分）
    if count >= 100:
        score += 40
    elif count >= 50:
        score += 30
    elif count >= 20:
        score += 20
    elif count >= 10:
        score += 15
    elif count >= 5:
        score += 10
    else:
        score += 5
    
    # 平均评分权重（最多 30 分）- 评分越低越重要
    if avg_rating is not None:
        if avg_rating <= 1.5:
            score += 30
        elif avg_rating <= 2:
            score += 25
        elif avg_rating <= 2.5:
            score += 20
        elif avg_rating <= 3:
            score += 15
    else:
        score += 15  # HackerNews 没有评分，给中等分
    
    # 多数据源权重（最多 20 分）
    score += min(num_sources * 10, 20)
    
    # 转换为优先级
    if score >= 70:
        return 'P0'
    elif score >= 50:
        return 'P1'
    elif score >= 30:
        return 'P2'
    else:
        return 'P3'


def generate_opportunities(category, pain_stats, min_count=3):
    """生成 AI 机会列表"""
    opportunities = []
    
    for pattern_id, stats in pain_stats.items():
        # 放宽限制：只要有 3 条以上提及就保留
        if stats['count'] < min_count:
            continue
        
        config = PAIN_PATTERNS.get(pattern_id, {})
        category_name = config.get('category', pattern_id)
        
        # 计算平均评分
        avg_rating = sum(stats['ratings']) / len(stats['ratings']) if stats['ratings'] else None
        
        # 计算优先级
        priority = calculate_priority(
            stats['count'],
            avg_rating,
            len(stats['sources'])
        )
        
        # 确定 AI 介入类型
        pain_type = pattern_id.split('_')[0]
        ai_type = AI_INTERVENTION_TYPES.get(pain_type, '轻量介入')
        
        # 生成唯一 ID
        opp_id = f"{category}_{pattern_id}_{hashlib.md5(category_name.encode()).hexdigest()[:6]}"
        
        opportunity = {
            'id': opp_id,
            'title': category_name,
            'description': f"用户反馈{category_name}相关问题，共 {stats['count']} 条提及",
            'ai_intervention_type': ai_type,
            'user_pain_summary': f"用户在使用过程中遇到{category_name}问题",
            'priority': priority,
            'cross_product_relevance': [category],
            'source_stats': {
                'exact_match_count': stats['count'],
                'products_mentioned': list(stats['apps'])[:10],
                'sources': list(stats['sources']),
                'avg_rating': round(avg_rating, 1) if avg_rating else None
            },
            'evidence_samples': [
                {
                    'original_text': s['text'],
                    'source': f"{s['source']} - {s['app']}",
                    'pain_point_extracted': category_name,
                    'sentiment_score': (s['rating'] or 3) / 5,
                    'relevance_score': s.get('relevance_score', 0)
                }
                for s in stats['samples'][:5]
            ]
        }
        
        opportunities.append(opportunity)
    
    # 按优先级和提及数量排序
    priority_order = {'P0': 0, 'P1': 1, 'P2': 2, 'P3': 3}
    opportunities.sort(key=lambda x: (
        priority_order.get(x['priority'], 9),
        -x['source_stats']['exact_match_count']
    ))
    
    return opportunities


def main():
    categories = ['wechat', 'social', 'ai', 'more']
    output_dir = 'data/processed'
    os.makedirs(output_dir, exist_ok=True)
    
    print("=" * 70)
    print("需求点提取 - V2（多数据源整合版）")
    print("=" * 70)
    
    total_opportunities = 0
    
    for cat in categories:
        print(f"\n处理类目: {cat}")
        print("-" * 40)
        
        # 加载所有数据源
        items = load_all_data(cat)
        print(f"  加载数据: {len(items)} 条")
        
        # 提取痛点
        pain_stats = extract_pain_points(items, cat)
        print(f"  识别痛点模式: {len(pain_stats)} 种")
        
        # 生成机会列表
        opportunities = generate_opportunities(cat, pain_stats, min_count=3)
        print(f"  生成需求点: {len(opportunities)} 个")
        
        # 优先级分布
        priority_dist = Counter(o['priority'] for o in opportunities)
        print(f"  优先级分布: P0={priority_dist.get('P0',0)}, P1={priority_dist.get('P1',0)}, P2={priority_dist.get('P2',0)}, P3={priority_dist.get('P3',0)}")
        
        # 保存结果
        output = {
            'category': cat,
            'generated_at': datetime.now().isoformat(),
            'data_sources': list(DATA_SOURCES.keys()),
            'total_items_analyzed': len(items),
            'ai_opportunities': opportunities
        }
        
        output_path = os.path.join(output_dir, f"{cat}_ai_opportunities.json")
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output, f, ensure_ascii=False, indent=2)
        
        total_opportunities += len(opportunities)
    
    print("\n" + "=" * 70)
    print(f"完成！总计生成 {total_opportunities} 个需求点")
    print("=" * 70)


if __name__ == '__main__':
    main()
