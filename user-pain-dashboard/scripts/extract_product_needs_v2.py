#!/usr/bin/env python3
"""
产品需求提取器 V2
专为 AI 产品经理设计：
1. 从用户反馈中提取「用户需求场景」而非「技术问题」
2. 分析每个需求场景中 AI 的介入机会
3. 按产品价值（而非技术难度）排序
"""

import json
import os
import re
import hashlib
from datetime import datetime
from typing import List, Dict, Any, Tuple
from collections import defaultdict

# 需求场景模型（从用户视角定义）
NEED_SCENARIOS = {
    # ========== 社交互动需求 ==========
    'relationship_maintenance': {
        'name': '关系维护',
        'description': '用户希望更好地维护与亲友的关系',
        'keywords': ['联系', '聊天', '沟通', '关系', '朋友', '家人', '亲人', '想念', '问候', '祝福', '生日', '纪念日'],
        'ai_opportunities': [
            {'type': '智能提醒', 'desc': 'AI 识别重要关系并提醒用户保持联系'},
            {'type': '话题建议', 'desc': 'AI 根据共同兴趣推荐聊天话题'},
            {'type': '仪式感增强', 'desc': 'AI 在特殊日子生成个性化祝福内容'},
        ],
        'product_value': 'high',
    },
    'emotional_expression': {
        'name': '情感表达',
        'description': '用户想更好地表达情感，但找不到合适的方式',
        'keywords': ['表达', '说不出', '不知道怎么', '尴尬', '表情', '文字', '语音', '视频', '感谢', '道歉', '安慰', '鼓励'],
        'ai_opportunities': [
            {'type': '表达助手', 'desc': 'AI 帮助用户将想法转化为合适的文字'},
            {'type': '情绪识别', 'desc': 'AI 感知对方情绪并建议回应方式'},
            {'type': '创意表达', 'desc': 'AI 生成个性化表情/贴纸/小视频'},
        ],
        'product_value': 'high',
    },
    'group_coordination': {
        'name': '群体协调',
        'description': '用户需要在群组中协调多人活动',
        'keywords': ['群', '聚会', '活动', '时间', '投票', '通知', '报名', '统计', '接龙', 'AA', '分摊'],
        'ai_opportunities': [
            {'type': '智能协调', 'desc': 'AI 自动整合各方时间/意向，提出最优方案'},
            {'type': '任务追踪', 'desc': 'AI 追踪群内待办事项完成情况'},
            {'type': '信息摘要', 'desc': 'AI 总结群聊重点，@未读重要消息'},
        ],
        'product_value': 'high',
    },
    
    # ========== 信息管理需求 ==========
    'info_overload': {
        'name': '信息过载',
        'description': '用户被海量信息淹没，找不到重要内容',
        'keywords': ['消息太多', '找不到', '刷不完', '错过', '重要', '未读', '红点', '通知', '打扰', '骚扰'],
        'ai_opportunities': [
            {'type': '优先级排序', 'desc': 'AI 识别并置顶重要消息'},
            {'type': '智能摘要', 'desc': 'AI 生成聊天记录/群消息摘要'},
            {'type': '免打扰优化', 'desc': 'AI 学习用户习惯，智能管理通知'},
        ],
        'product_value': 'high',
    },
    'memory_retrieval': {
        'name': '记忆检索',
        'description': '用户想找回过去的聊天内容、图片、文件',
        'keywords': ['找不到', '搜索', '聊天记录', '图片', '文件', '链接', '之前', '以前', '删了', '丢了', '恢复'],
        'ai_opportunities': [
            {'type': '语义搜索', 'desc': 'AI 理解用户模糊描述，精准定位内容'},
            {'type': '智能归档', 'desc': 'AI 自动整理图片/文件/链接'},
            {'type': '回忆助手', 'desc': 'AI 生成与某人/某时期的互动回顾'},
        ],
        'product_value': 'medium',
    },
    
    # ========== 身份与隐私需求 ==========
    'privacy_control': {
        'name': '隐私控制',
        'description': '用户对个人信息暴露感到不安',
        'keywords': ['隐私', '泄露', '看到', '被发现', '不想', '屏蔽', '黑名单', '可见', '权限', '陌生人'],
        'ai_opportunities': [
            {'type': '隐私检测', 'desc': 'AI 提醒可能的隐私风险'},
            {'type': '智能分组', 'desc': 'AI 自动管理好友分组和可见范围'},
            {'type': '匿名模式', 'desc': 'AI 辅助的匿名社交场景'},
        ],
        'product_value': 'medium',
    },
    'digital_identity': {
        'name': '数字身份',
        'description': '用户希望在数字世界中有更好的自我呈现',
        'keywords': ['头像', '昵称', '个性签名', '朋友圈', '状态', '形象', '展示', '标签'],
        'ai_opportunities': [
            {'type': 'AI头像', 'desc': 'AI 生成个性化虚拟形象'},
            {'type': '内容美化', 'desc': 'AI 优化用户发布的图片/文字'},
            {'type': '兴趣展示', 'desc': 'AI 帮助用户更好地展示兴趣爱好'},
        ],
        'product_value': 'medium',
    },
    
    # ========== 效率需求 ==========
    'work_life_balance': {
        'name': '工作生活边界',
        'description': '用户希望区分工作和私人社交',
        'keywords': ['工作', '私人', '老板', '同事', '领导', '下班', '周末', '加班', '打扰', '已读'],
        'ai_opportunities': [
            {'type': '场景切换', 'desc': 'AI 根据时间/地点自动切换工作/生活模式'},
            {'type': '延迟回复', 'desc': 'AI 代为管理非工作时间的工作消息'},
            {'type': '边界守护', 'desc': 'AI 帮助用户委婉拒绝不合理要求'},
        ],
        'product_value': 'high',
    },
    'quick_reply': {
        'name': '快速回复',
        'description': '用户需要快速处理大量消息',
        'keywords': ['忙', '没时间', '快速', '回复', '处理', '未读', '太多', '积压'],
        'ai_opportunities': [
            {'type': '智能回复', 'desc': 'AI 根据上下文生成回复建议'},
            {'type': '批量处理', 'desc': 'AI 帮助用户批量处理同类消息'},
            {'type': '代理模式', 'desc': 'AI 在用户授权下自动处理简单消息'},
        ],
        'product_value': 'high',
    },
    
    # ========== 创意与娱乐需求 ==========
    'content_creation': {
        'name': '内容创作',
        'description': '用户想创作有趣的内容但缺乏灵感或技能',
        'keywords': ['发什么', '不知道写', '没灵感', '文案', '配图', '滤镜', '视频', '创意', '有趣'],
        'ai_opportunities': [
            {'type': '创意生成', 'desc': 'AI 根据场景生成创意内容'},
            {'type': '素材推荐', 'desc': 'AI 推荐合适的配图/音乐/模板'},
            {'type': '风格迁移', 'desc': 'AI 将用户内容转化为特定风格'},
        ],
        'product_value': 'medium',
    },
    'social_entertainment': {
        'name': '社交娱乐',
        'description': '用户希望与朋友一起玩耍互动',
        'keywords': ['游戏', '一起', '互动', '玩', '无聊', '打发时间', '挑战', '比赛', 'PK'],
        'ai_opportunities': [
            {'type': '互动游戏', 'desc': 'AI 驱动的社交小游戏'},
            {'type': '智能匹配', 'desc': 'AI 匹配兴趣相投的玩伴'},
            {'type': '氛围营造', 'desc': 'AI 在群聊中增添趣味元素'},
        ],
        'product_value': 'medium',
    },
    
    # ========== 安全与信任需求 ==========
    'fraud_protection': {
        'name': '防诈防骗',
        'description': '用户担心被骗或遇到不安全的内容',
        'keywords': ['诈骗', '骗子', '骗钱', '假的', '不信任', '可疑', '安全', '风险', '警告'],
        'ai_opportunities': [
            {'type': '风险识别', 'desc': 'AI 识别可疑消息/链接/转账'},
            {'type': '身份验证', 'desc': 'AI 辅助验证对方真实身份'},
            {'type': '安全提醒', 'desc': 'AI 在风险场景主动提醒'},
        ],
        'product_value': 'high',
    },
    'content_moderation': {
        'name': '内容治理',
        'description': '用户遇到不良内容或骚扰',
        'keywords': ['骚扰', '广告', '垃圾', '低俗', '暴力', '举报', '屏蔽', '拉黑'],
        'ai_opportunities': [
            {'type': '智能过滤', 'desc': 'AI 自动识别并过滤不良内容'},
            {'type': '行为分析', 'desc': 'AI 识别异常行为模式'},
            {'type': '社区守护', 'desc': 'AI 辅助维护群组健康氛围'},
        ],
        'product_value': 'medium',
    },
}


def load_all_reviews(data_dir: str) -> List[Dict]:
    """加载所有评论数据"""
    all_reviews = []
    raw_dir = os.path.join(data_dir, 'raw')
    
    for source_dir in os.listdir(raw_dir):
        source_path = os.path.join(raw_dir, source_dir)
        if not os.path.isdir(source_path):
            continue
            
        for filename in os.listdir(source_path):
            if not filename.endswith('.json'):
                continue
                
            filepath = os.path.join(source_path, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # 提取评论/投诉
                items = []
                if 'reviews' in data:
                    items = data['reviews']
                elif 'comments' in data:
                    items = data['comments']
                elif 'complaints' in data:
                    items = data['complaints']
                elif isinstance(data, list):
                    items = data
                
                for item in items:
                    # 统一字段
                    text = item.get('content') or item.get('text') or item.get('title') or item.get('summary') or ''
                    if not text or len(text) < 10:
                        continue
                    
                    all_reviews.append({
                        'text': text,
                        'source': item.get('source') or source_dir,
                        'source_id': source_dir,
                        'app_name': item.get('app_name') or item.get('company') or '',
                        'rating': item.get('rating') or item.get('score') or 0,
                        'date': item.get('date') or item.get('timestamp') or '',
                    })
                    
            except Exception as e:
                print(f"  加载 {filepath} 失败: {e}")
    
    return all_reviews


def match_scenario(text: str) -> List[Tuple[str, int]]:
    """匹配文本到需求场景，返回 (场景ID, 匹配关键词数)"""
    text_lower = text.lower()
    matches = []
    
    for scenario_id, scenario in NEED_SCENARIOS.items():
        match_count = 0
        for keyword in scenario['keywords']:
            if keyword in text_lower or keyword in text:
                match_count += 1
        
        if match_count > 0:
            matches.append((scenario_id, match_count))
    
    return sorted(matches, key=lambda x: -x[1])


def analyze_sentiment(text: str) -> str:
    """简单情感分析"""
    negative_words = ['差', '烂', '垃圾', '恶心', '失望', '难用', '坑', '骗', '慢', '卡', '崩', '闪退', '恨', '讨厌', '受不了', '问题', 'bug', '故障']
    positive_words = ['好', '棒', '赞', '喜欢', '方便', '快', '稳', '满意', '推荐', '感谢', '谢谢', '❤']
    
    neg_count = sum(1 for w in negative_words if w in text)
    pos_count = sum(1 for w in positive_words if w in text)
    
    if neg_count > pos_count:
        return 'negative'
    elif pos_count > neg_count:
        return 'positive'
    return 'neutral'


def extract_user_intent(text: str) -> str:
    """提取用户意图（需求描述）"""
    # 找出核心诉求
    intent_patterns = [
        (r'希望(.{5,30})', 'hope'),
        (r'想要(.{5,30})', 'want'),
        (r'想(.{5,30})', 'want'),
        (r'需要(.{5,30})', 'need'),
        (r'能不能(.{5,30})', 'request'),
        (r'为什么(.{5,30})', 'question'),
        (r'不能(.{5,30})', 'complaint'),
        (r'没有(.{5,30})', 'missing'),
        (r'建议(.{5,30})', 'suggestion'),
    ]
    
    for pattern, intent_type in intent_patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(1).strip()
    
    # 如果没有明确意图，返回前50字
    return text[:50] + ('...' if len(text) > 50 else '')


def process_reviews(reviews: List[Dict]) -> Dict[str, Any]:
    """处理评论，提取产品需求"""
    
    scenario_data = defaultdict(lambda: {
        'count': 0,
        'samples': [],
        'sources': defaultdict(int),
        'apps': defaultdict(int),
        'intents': [],
        'avg_rating': [],
    })
    
    for review in reviews:
        text = review['text']
        matches = match_scenario(text)
        
        if not matches:
            continue
        
        # 取最匹配的场景
        top_scenario, match_strength = matches[0]
        
        sd = scenario_data[top_scenario]
        sd['count'] += 1
        sd['sources'][review['source']] += 1
        if review['app_name']:
            sd['apps'][review['app_name']] += 1
        if review['rating']:
            sd['avg_rating'].append(review['rating'])
        
        # 提取用户意图
        intent = extract_user_intent(text)
        if intent and len(intent) > 10:
            sd['intents'].append(intent)
        
        # 保存样本（最多50个）
        if len(sd['samples']) < 50:
            sd['samples'].append({
                'text': text[:200],
                'source': review['source'],
                'app': review['app_name'],
                'sentiment': analyze_sentiment(text),
            })
    
    return scenario_data


def generate_opportunities(scenario_data: Dict[str, Any]) -> List[Dict]:
    """生成 AI 机会列表"""
    
    opportunities = []
    
    for scenario_id, data in scenario_data.items():
        if data['count'] < 5:  # 至少5条才算有效
            continue
        
        scenario = NEED_SCENARIOS[scenario_id]
        
        # 计算优先级
        count = data['count']
        value = scenario['product_value']
        
        if count >= 100 and value == 'high':
            priority = 'P0'
        elif count >= 50 or (count >= 20 and value == 'high'):
            priority = 'P1'
        else:
            priority = 'P2'
        
        # 提取代表性用户声音
        user_voices = []
        seen_intents = set()
        for intent in data['intents'][:30]:
            # 去重
            intent_hash = hashlib.md5(intent.encode()).hexdigest()[:8]
            if intent_hash not in seen_intents:
                seen_intents.add(intent_hash)
                user_voices.append(intent)
                if len(user_voices) >= 5:
                    break
        
        # 计算平均评分
        avg_rating = sum(data['avg_rating']) / len(data['avg_rating']) if data['avg_rating'] else 0
        
        opportunity = {
            'id': f"{scenario_id}_{hashlib.md5(scenario_id.encode()).hexdigest()[:6]}",
            'scenario_id': scenario_id,
            'title': scenario['name'],
            'description': scenario['description'],
            'priority': priority,
            'product_value': scenario['product_value'],
            
            # 用户数据
            'mention_count': count,
            'avg_rating': round(avg_rating, 1),
            'user_voices': user_voices,
            
            # AI 介入机会
            'ai_opportunities': scenario['ai_opportunities'],
            
            # 数据来源
            'data_sources': dict(data['sources']),
            'apps_mentioned': dict(sorted(data['apps'].items(), key=lambda x: -x[1])[:10]),
            
            # 样本
            'evidence_samples': data['samples'][:10],
        }
        
        opportunities.append(opportunity)
    
    # 按优先级和数量排序
    priority_order = {'P0': 0, 'P1': 1, 'P2': 2}
    opportunities.sort(key=lambda x: (priority_order[x['priority']], -x['mention_count']))
    
    return opportunities


def main():
    """主函数"""
    data_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
    
    print("=" * 60)
    print("产品需求提取器 V2")
    print("=" * 60)
    
    # 1. 加载所有评论
    print("\n📥 加载数据...")
    reviews = load_all_reviews(data_dir)
    print(f"  共加载 {len(reviews)} 条评论")
    
    # 2. 处理评论
    print("\n🔍 分析需求场景...")
    scenario_data = process_reviews(reviews)
    print(f"  识别到 {len(scenario_data)} 个需求场景")
    
    # 3. 生成机会
    print("\n✨ 生成 AI 介入机会...")
    opportunities = generate_opportunities(scenario_data)
    print(f"  生成 {len(opportunities)} 个产品机会")
    
    # 4. 保存结果
    output_dir = os.path.join(data_dir, 'processed')
    os.makedirs(output_dir, exist_ok=True)
    
    result = {
        'generated_at': datetime.now().isoformat(),
        'total_reviews_analyzed': len(reviews),
        'scenarios_identified': len(scenario_data),
        'opportunities': opportunities,
    }
    
    output_path = os.path.join(output_dir, 'product_opportunities_v2.json')
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 保存到: {output_path}")
    
    # 5. 打印摘要
    print("\n" + "=" * 60)
    print("产品机会摘要:")
    print("=" * 60)
    
    for i, opp in enumerate(opportunities[:10], 1):
        print(f"\n{i}. [{opp['priority']}] {opp['title']}")
        print(f"   {opp['description']}")
        print(f"   📊 提及 {opp['mention_count']} 次 | 来源: {', '.join(opp['data_sources'].keys())}")
        print(f"   🤖 AI 机会:")
        for ai in opp['ai_opportunities'][:2]:
            print(f"      - {ai['type']}: {ai['desc']}")
        if opp['user_voices']:
            print(f"   💬 用户声音: \"{opp['user_voices'][0]}\"")
    
    return result


if __name__ == '__main__':
    main()
