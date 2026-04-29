#!/usr/bin/env python3
"""
需求点 + 典型样本生成（V2版）
选择标准：与需求描述逻辑最相关的样本，而非单纯低分优先
"""

import json
import re
from collections import defaultdict

# 加载数据
with open('data/raw/appstore/wechat_20260423.json', 'r') as f:
    data = json.load(f)

reviews = data.get('reviews', [])

# 需求点定义 + 精确匹配规则
# 每个需求点包含：demand(需求描述)、type(类型)、patterns(匹配正则)、relevance_keywords(相关性关键词)
demand_definitions = {
    '朋友圈体验': {
        'demand': '希望朋友圈发布和管理体验更好',
        'type': '功能需求',
        'ai_score': 7,
        'ai_reason': '智能排序、内容推荐、AI编辑',
        'patterns': [r'朋友圈'],
        'relevance_keywords': ['发布', '管理', '刷新', '排序', '推荐', '显示', '看不到', '刷到', '动态'],
        'exclude_keywords': ['折叠', '编辑已发']  # 排除属于其他需求的
    },
    '内容折叠': {
        'demand': '希望内容折叠更智能/可自定义',
        'type': '功能需求',
        'ai_score': 8,
        'ai_reason': '智能判定折叠规则、用户可选控制',
        'patterns': [r'折叠'],
        'relevance_keywords': ['折叠', '展开', '收起', '显示全部', '查看全部'],
        'exclude_keywords': []
    },
    '画质压缩': {
        'demand': '希望发送图片/视频画质不被压缩',
        'type': '功能需求',
        'ai_score': 9,
        'ai_reason': 'AI超分辨率、智能压缩优化',
        'patterns': [r'画质|清晰度|模糊|压缩'],
        'relevance_keywords': ['画质', '清晰', '模糊', '压缩', '原图', '像素', '分辨率'],
        'exclude_keywords': []
    },
    '语音转文字': {
        'demand': '希望语音转文字更准确',
        'type': '功能需求',
        'ai_score': 9,
        'ai_reason': 'ASR已成熟，准确率可优化',
        'patterns': [r'语音转文字|转文字'],
        'relevance_keywords': ['转文字', '识别', '准确', '错误', '语音'],
        'exclude_keywords': []
    },
    '客服问题': {
        'demand': '希望能找到人工客服解决问题',
        'type': '功能需求',
        'ai_score': 6,
        'ai_reason': '智能客服辅助、意图理解',
        'patterns': [r'客服|人工|投诉'],
        'relevance_keywords': ['客服', '人工', '投诉', '反馈', '解决', '回复', '联系'],
        'exclude_keywords': []
    },
    '公众号折叠': {
        'demand': '希望公众号/服务号消息不被折叠',
        'type': '功能需求',
        'ai_score': 5,
        'ai_reason': '智能消息分类、重要性排序',
        'patterns': [r'公众号|服务号'],
        'relevance_keywords': ['折叠', '消息', '通知', '订阅', '推送'],
        'exclude_keywords': []
    },
    '消息通知': {
        'demand': '希望消息通知更及时准确',
        'type': '功能需求',
        'ai_score': 6,
        'ai_reason': '智能优先级、降噪推送',
        'patterns': [r'通知|提醒|消息.*延迟|收不到.*消息'],
        'relevance_keywords': ['通知', '提醒', '延迟', '收不到', '推送', '及时'],
        'exclude_keywords': ['公众号', '服务号']
    },
    '聊天记录': {
        'demand': '希望聊天记录更容易搜索和管理',
        'type': '功能需求',
        'ai_score': 7,
        'ai_reason': '智能搜索、摘要、重要信息提取',
        'patterns': [r'聊天记录|记录.*删除|记录.*恢复'],
        'relevance_keywords': ['记录', '搜索', '查找', '备份', '恢复', '删除'],
        'exclude_keywords': []
    },
    '通话功能': {
        'demand': '希望语音/视频通话质量更好',
        'type': '功能需求',
        'ai_score': 5,
        'ai_reason': 'AI降噪、实时翻译',
        'patterns': [r'视频通话|视频聊天|语音通话|语音聊天|打电话|通话'],
        'relevance_keywords': ['通话', '视频', '语音', '质量', '卡顿', '断线', '声音'],
        'exclude_keywords': []
    },
    '表情贴图': {
        'demand': '希望表情包/贴图功能更好用',
        'type': '功能需求',
        'ai_score': 7,
        'ai_reason': 'AI表情生成、情绪识别推荐',
        'patterns': [r'表情|贴图'],
        'relevance_keywords': ['表情', '贴图', '表情包', '斗图', '发送'],
        'exclude_keywords': []
    },
    '外观定制': {
        'demand': '希望能自定义聊天气泡/主题颜色',
        'type': '功能需求',
        'ai_score': 6,
        'ai_reason': 'AI配色、个性化主题生成',
        'patterns': [r'气泡|颜色|皮肤|主题'],
        'relevance_keywords': ['气泡', '颜色', '主题', '皮肤', '背景', '自定义'],
        'exclude_keywords': []
    },
    '朋友圈编辑': {
        'demand': '希望能编辑已发布的朋友圈',
        'type': '功能需求',
        'ai_score': 8,
        'ai_reason': 'AI辅助排版、配文建议',
        'patterns': [r'编辑.*圈|圈.*编辑|修改.*朋友圈|朋友圈.*修改'],
        'relevance_keywords': ['编辑', '修改', '已发', '发布后'],
        'exclude_keywords': []
    },
    '群聊管理': {
        'demand': '希望群聊管理功能更完善',
        'type': '功能需求',
        'ai_score': 6,
        'ai_reason': '智能消息摘要、@提醒优化',
        'patterns': [r'群聊|群.*管理|拉群'],
        'relevance_keywords': ['群', '管理', '@', '消息', '成员'],
        'exclude_keywords': []
    },
    '配乐功能': {
        'demand': '希望朋友圈图片能配背景音乐',
        'type': '功能需求',
        'ai_score': 8,
        'ai_reason': 'AI配乐推荐、情绪匹配',
        'patterns': [r'配乐|音乐|BGM'],
        'relevance_keywords': ['配乐', '音乐', 'BGM', '背景音乐'],
        'exclude_keywords': []
    },
    '待办日程': {
        'demand': '希望有更好的待办/日程提醒功能',
        'type': '功能需求',
        'ai_score': 7,
        'ai_reason': '智能提醒、日程解析',
        'patterns': [r'待办|日程|提醒事项'],
        'relevance_keywords': ['待办', '日程', '提醒', '日历'],
        'exclude_keywords': []
    },
    '好友管理': {
        'demand': '希望好友分组和清理功能更好用',
        'type': '功能需求',
        'ai_score': 5,
        'ai_reason': '关系强度分析、分组建议',
        'patterns': [r'好友.*删除|删.*好友|通讯录'],
        'relevance_keywords': ['好友', '删除', '分组', '清理', '通讯录'],
        'exclude_keywords': []
    },
    '键盘输入': {
        'demand': '希望输入法/键盘适配更好',
        'type': '功能需求',
        'ai_score': 6,
        'ai_reason': '智能纠错、预测输入',
        'patterns': [r'键盘|输入法'],
        'relevance_keywords': ['键盘', '输入法', '打字', '输入'],
        'exclude_keywords': []
    },
    '小程序': {
        'demand': '希望小程序体验更流畅',
        'type': '功能需求',
        'ai_score': 5,
        'ai_reason': '智能搜索、推荐',
        'patterns': [r'小程序'],
        'relevance_keywords': ['小程序', '加载', '打开'],
        'exclude_keywords': []
    },
    '铃声提示音': {
        'demand': '想要自定义消息提示音',
        'type': '功能需求',
        'ai_score': 4,
        'ai_reason': 'AI生成音效可行但需求小',
        'patterns': [r'铃声|提示音'],
        'relevance_keywords': ['铃声', '提示音', '声音', '自定义'],
        'exclude_keywords': []
    },
    
    # ===== 问题反馈 =====
    '拍照相机': {
        'demand': '微信拍照时经常卡死/黑屏',
        'type': '问题反馈',
        'ai_score': 2,
        'ai_reason': '工程问题，非AI问题',
        'patterns': [r'拍照|相机|摄像'],
        'relevance_keywords': ['卡', '黑屏', '闪退', '崩溃', '无法', '打不开'],
        'exclude_keywords': []
    },
    '卡顿崩溃': {
        'demand': '微信整体卡顿/闪退/崩溃',
        'type': '问题反馈',
        'ai_score': 2,
        'ai_reason': '工程优化问题',
        'patterns': [r'卡顿|卡死|黑屏|闪退|崩溃'],
        'relevance_keywords': ['卡', '闪退', '崩溃', '黑屏', '卡死'],
        'exclude_keywords': ['拍照', '相机']
    },
    '版本更新': {
        'demand': '更新后出现新问题/功能倒退',
        'type': '问题反馈',
        'ai_score': 2,
        'ai_reason': '产品策略问题',
        'patterns': [r'更新|版本|推送'],
        'relevance_keywords': ['更新', '版本', '升级', '倒退', '以前', '之前'],
        'exclude_keywords': []
    },
    '系统适配': {
        'demand': '新系统/新设备适配有问题',
        'type': '问题反馈',
        'ai_score': 2,
        'ai_reason': '适配工程问题',
        'patterns': [r'适配|兼容'],
        'relevance_keywords': ['适配', '兼容', 'iOS', '系统', '设备'],
        'exclude_keywords': []
    },
    '登录问题': {
        'demand': '登录/扫码遇到问题',
        'type': '问题反馈',
        'ai_score': 4,
        'ai_reason': '人脸识别已应用，空间有限',
        'patterns': [r'登录|登陆|扫码'],
        'relevance_keywords': ['登录', '登陆', '扫码', '无法', '失败'],
        'exclude_keywords': []
    },
    
    # ===== 平台策略 =====
    '账号封禁': {
        'demand': '账号被封/限制，申诉无门',
        'type': '平台策略',
        'ai_score': 3,
        'ai_reason': '平台策略问题',
        'patterns': [r'封号|封禁|解封|限制'],
        'relevance_keywords': ['封', '限制', '申诉', '解封'],
        'exclude_keywords': []
    },
    '广告问题': {
        'demand': '广告太多影响体验',
        'type': '平台策略',
        'ai_score': 2,
        'ai_reason': '商业模式问题',
        'patterns': [r'广告'],
        'relevance_keywords': ['广告', '推广', '骚扰'],
        'exclude_keywords': []
    },
    '支付转账': {
        'demand': '支付/转账问题或手续费',
        'type': '平台策略',
        'ai_score': 3,
        'ai_reason': '金融合规问题',
        'patterns': [r'转账|支付|扣钱|扣费|手续费|余额'],
        'relevance_keywords': ['转账', '支付', '手续费', '余额', '扣'],
        'exclude_keywords': []
    },
    '隐私安全': {
        'demand': '担心隐私泄露/安全问题',
        'type': '平台策略',
        'ai_score': 3,
        'ai_reason': '合规问题为主',
        'patterns': [r'隐私|安全'],
        'relevance_keywords': ['隐私', '安全', '泄露', '监控'],
        'exclude_keywords': []
    },
    '实名认证': {
        'demand': '频繁要求实名认证',
        'type': '平台策略',
        'ai_score': 3,
        'ai_reason': '合规要求',
        'patterns': [r'实名|认证|身份'],
        'relevance_keywords': ['实名', '认证', '身份', '验证'],
        'exclude_keywords': []
    },
    '存储内存': {
        'demand': '微信占用存储空间太大',
        'type': '平台策略',
        'ai_score': 4,
        'ai_reason': '架构问题，AI空间小',
        'patterns': [r'存储|内存|占空间|缓存'],
        'relevance_keywords': ['存储', '内存', '空间', '缓存', '占用', 'G'],
        'exclude_keywords': []
    },
    '文件传输': {
        'demand': '文件传输慢/大小限制',
        'type': '平台策略',
        'ai_score': 4,
        'ai_reason': '带宽问题为主',
        'patterns': [r'文件|文档|传输'],
        'relevance_keywords': ['文件', '传输', '大小', '限制', '慢'],
        'exclude_keywords': []
    },
    '已读功能': {
        'demand': '希望有/没有已读功能',
        'type': '平台策略',
        'ai_score': 4,
        'ai_reason': '产品策略问题',
        'patterns': [r'已读|未读'],
        'relevance_keywords': ['已读', '未读', '是否看过'],
        'exclude_keywords': []
    },
    '内测资格': {
        'demand': '想要获得内测资格/新功能',
        'type': '平台策略',
        'ai_score': 1,
        'ai_reason': '产品策略问题',
        'patterns': [r'内测|灰度'],
        'relevance_keywords': ['内测', '灰度', '新功能', '资格'],
        'exclude_keywords': []
    },
    '多开分身': {
        'demand': '希望支持微信多开/分身',
        'type': '平台策略',
        'ai_score': 2,
        'ai_reason': '产品策略问题',
        'patterns': [r'双开|分身|多开'],
        'relevance_keywords': ['双开', '分身', '多开', '两个'],
        'exclude_keywords': []
    },
}

def match_demand(content, demand_key, demand_info):
    """判断评论是否匹配特定需求，并计算相关性分数"""
    # 基础匹配
    base_match = False
    for pattern in demand_info['patterns']:
        if re.search(pattern, content):
            base_match = True
            break
    
    if not base_match:
        return False, 0
    
    # 排除检查
    for exclude in demand_info.get('exclude_keywords', []):
        if exclude in content:
            return False, 0
    
    # 计算相关性分数
    relevance_score = 0
    for kw in demand_info.get('relevance_keywords', []):
        if kw in content:
            relevance_score += 1
    
    return True, relevance_score

# 收集每个需求点的样本
demand_samples = defaultdict(list)

for r in reviews:
    content = r.get('content', '')
    rating = r.get('rating', 0)
    review_id = r.get('id', '')
    
    for demand_key, demand_info in demand_definitions.items():
        matched, relevance_score = match_demand(content, demand_key, demand_info)
        if matched:
            demand_samples[demand_key].append({
                'content': content,
                'rating': rating,
                'review_id': review_id,
                'relevance_score': relevance_score
            })

# 选择最相关的样本
def select_best_samples(samples, count=3):
    """选择最相关的样本（按相关性分数排序，相同分数则优先低评分）"""
    sorted_samples = sorted(samples, key=lambda x: (-x['relevance_score'], x['rating']))
    return sorted_samples[:count]

# 生成输出
print("=" * 120)
print("【需求点 + 典型样本】V2版 - 按逻辑相关性选择样本")
print("=" * 120)

type_order = {'功能需求': 0, '问题反馈': 1, '平台策略': 2}

# 统计并排序
demand_stats = []
for demand_key, samples in demand_samples.items():
    if demand_key not in demand_definitions:
        continue
    info = demand_definitions[demand_key]
    count = len(samples)
    
    # 计算综合分
    count_score = min(count / 72 * 10, 10)
    low_rating_pct = sum(1 for s in samples if s['rating'] <= 2) / count * 100 if count > 0 else 0
    pain_score = low_rating_pct / 10
    composite_score = info['ai_score'] * 0.4 + count_score * 0.3 + pain_score * 0.3
    
    demand_stats.append({
        'key': demand_key,
        'demand': info['demand'],
        'type': info['type'],
        'ai_score': info['ai_score'],
        'ai_reason': info['ai_reason'],
        'count': count,
        'composite_score': composite_score,
        'samples': samples
    })

# 排序
demand_stats.sort(key=lambda x: (type_order[x['type']], -x['composite_score']))

current_type = None
rank = 0
for stat in demand_stats:
    if stat['count'] == 0:
        continue
        
    if stat['type'] != current_type:
        current_type = stat['type']
        type_count = len([s for s in demand_stats if s['type'] == current_type and s['count'] > 0])
        type_samples = sum(s['count'] for s in demand_stats if s['type'] == current_type)
        print(f"\n{'═' * 120}")
        print(f"【{current_type}】（{type_count} 个需求点，共 {type_samples} 条样本）")
        print(f"{'═' * 120}")
    
    rank += 1
    print(f"\n{'─' * 120}")
    print(f"#{rank} {stat['demand']}")
    print(f"    提及: {stat['count']}条 | AI介入分: {stat['ai_score']}/10 | {stat['ai_reason']}")
    print(f"{'─' * 120}")
    
    best_samples = select_best_samples(stat['samples'], 3)
    print("典型样本（按逻辑相关性选择）：")
    for i, sample in enumerate(best_samples, 1):
        stars = '★' * sample['rating'] + '☆' * (5 - sample['rating'])
        content = sample['content'].replace('\n', ' ').strip()
        if len(content) > 200:
            content = content[:200] + '...'
        print(f"  [{i}] {stars} ({sample['rating']}星) 相关度:{sample['relevance_score']}")
        print(f"      「{content}」")
        print()

# 汇总
print(f"\n{'═' * 120}")
print("【汇总】")
func_req = [s for s in demand_stats if s['type'] == '功能需求' and s['count'] > 0]
bug_req = [s for s in demand_stats if s['type'] == '问题反馈' and s['count'] > 0]
policy_req = [s for s in demand_stats if s['type'] == '平台策略' and s['count'] > 0]
print(f"  功能需求: {len(func_req)} 个，{sum(s['count'] for s in func_req)} 条样本")
print(f"  问题反馈: {len(bug_req)} 个，{sum(s['count'] for s in bug_req)} 条样本")
print(f"  平台策略: {len(policy_req)} 个，{sum(s['count'] for s in policy_req)} 条样本")
print(f"{'═' * 120}")
