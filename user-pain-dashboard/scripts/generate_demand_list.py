import json
import re
from collections import defaultdict

with open('data/raw/appstore/wechat_20260423.json', 'r') as f:
    data = json.load(f)

reviews = data.get('reviews', [])

def extract_semantic_keywords(text):
    keywords = []
    func_patterns = [
        (r'拍照|相机|摄像', '拍照/相机'),
        (r'视频通话|视频聊天|语音通话|语音聊天|打电话|通话', '通话功能'),
        (r'朋友圈', '朋友圈'),
        (r'转账|支付|扣钱|扣费|手续费|余额', '支付/转账'),
        (r'语音转文字|转文字', '语音转文字'),
        (r'存储|内存|占空间|缓存', '存储/内存'),
        (r'通知|提醒|消息.*延迟|收不到.*消息', '消息通知'),
        (r'聊天记录|记录.*删除|记录.*恢复', '聊天记录'),
        (r'封号|封禁|解封|限制', '账号封禁'),
        (r'登录|登陆|扫码', '登录'),
        (r'群聊|群.*管理|拉群', '群聊管理'),
        (r'好友.*删除|删.*好友|通讯录', '好友管理'),
        (r'小程序', '小程序'),
        (r'公众号|服务号', '公众号'),
        (r'表情|贴图', '表情/贴图'),
        (r'文件|文档|传输', '文件传输'),
        (r'键盘|输入法', '键盘/输入'),
        (r'画质|清晰度|模糊|压缩', '画质'),
        (r'已读|未读', '已读功能'),
        (r'双开|分身|多开', '多开/分身'),
        (r'铃声|提示音', '铃声/提示音'),
        (r'卡顿|卡死|黑屏|闪退|崩溃', '卡顿/崩溃'),
        (r'更新|版本|推送', '版本更新'),
        (r'适配|兼容', '系统适配'),
        (r'隐私|安全', '隐私/安全'),
        (r'客服|人工|投诉', '客服'),
        (r'广告', '广告'),
        (r'内测|灰度', '内测'),
        (r'折叠', '内容折叠'),
        (r'编辑.*圈|圈.*编辑', '朋友圈编辑'),
        (r'配乐|音乐|BGM', '配乐功能'),
        (r'待办|日程|提醒事项', '待办/日程'),
        (r'气泡|颜色|皮肤|主题', '外观定制'),
        (r'实名|认证|身份', '实名认证'),
    ]
    for pattern, keyword in func_patterns:
        if re.search(pattern, text):
            keywords.append(keyword)
    return keywords

# 收集样本
keyword_samples = defaultdict(list)
for r in reviews:
    content = r.get('content', '')
    rating = r.get('rating', 0)
    kws = extract_semantic_keywords(content)
    for kw in kws:
        keyword_samples[kw].append({'content': content, 'rating': rating})

# 需求点定义：用户需求描述 + 类型标签 + AI分数
demand_definitions = {
    # ===== 功能需求 (AI可解) =====
    '朋友圈': {
        'demand': '希望朋友圈发布和管理体验更好',
        'type': '功能需求',
        'ai_score': 7,
        'ai_reason': '智能排序、内容推荐、AI编辑'
    },
    '内容折叠': {
        'demand': '希望内容折叠更智能/可自定义',
        'type': '功能需求',
        'ai_score': 8,
        'ai_reason': '智能判定折叠规则、用户可选控制'
    },
    '画质': {
        'demand': '希望发送图片/视频画质不被压缩',
        'type': '功能需求',
        'ai_score': 9,
        'ai_reason': 'AI超分辨率、智能压缩优化'
    },
    '语音转文字': {
        'demand': '希望语音转文字更准确',
        'type': '功能需求',
        'ai_score': 9,
        'ai_reason': 'ASR已成熟，准确率可优化'
    },
    '客服': {
        'demand': '希望能找到人工客服解决问题',
        'type': '功能需求',
        'ai_score': 6,
        'ai_reason': '智能客服辅助、意图理解'
    },
    '公众号': {
        'demand': '希望公众号/服务号消息不被折叠',
        'type': '功能需求',
        'ai_score': 5,
        'ai_reason': '智能消息分类、重要性排序'
    },
    '消息通知': {
        'demand': '希望消息通知更及时准确',
        'type': '功能需求',
        'ai_score': 6,
        'ai_reason': '智能优先级、降噪推送'
    },
    '聊天记录': {
        'demand': '希望聊天记录更容易搜索和管理',
        'type': '功能需求',
        'ai_score': 7,
        'ai_reason': '智能搜索、摘要、重要信息提取'
    },
    '通话功能': {
        'demand': '希望语音/视频通话质量更好',
        'type': '功能需求',
        'ai_score': 5,
        'ai_reason': 'AI降噪、实时翻译'
    },
    '表情/贴图': {
        'demand': '希望有更多表情包和贴图选择',
        'type': '功能需求',
        'ai_score': 7,
        'ai_reason': 'AI表情生成、情绪识别推荐'
    },
    '外观定制': {
        'demand': '希望能自定义聊天气泡/主题颜色',
        'type': '功能需求',
        'ai_score': 6,
        'ai_reason': 'AI配色、个性化主题生成'
    },
    '朋友圈编辑': {
        'demand': '希望能编辑已发布的朋友圈',
        'type': '功能需求',
        'ai_score': 8,
        'ai_reason': 'AI辅助排版、配文建议'
    },
    '群聊管理': {
        'demand': '希望群聊管理功能更完善',
        'type': '功能需求',
        'ai_score': 6,
        'ai_reason': '智能消息摘要、@提醒优化'
    },
    '配乐功能': {
        'demand': '希望朋友圈图片能配背景音乐',
        'type': '功能需求',
        'ai_score': 8,
        'ai_reason': 'AI配乐推荐、情绪匹配'
    },
    '待办/日程': {
        'demand': '希望有更好的待办/日程提醒功能',
        'type': '功能需求',
        'ai_score': 7,
        'ai_reason': '智能提醒、日程解析'
    },
    '好友管理': {
        'demand': '希望好友分组和清理功能更好用',
        'type': '功能需求',
        'ai_score': 5,
        'ai_reason': '关系强度分析、分组建议'
    },
    '键盘/输入': {
        'demand': '希望输入法/键盘适配更好',
        'type': '功能需求',
        'ai_score': 6,
        'ai_reason': '智能纠错、预测输入'
    },
    '小程序': {
        'demand': '希望小程序体验更流畅',
        'type': '功能需求',
        'ai_score': 5,
        'ai_reason': '智能搜索、推荐'
    },
    '铃声/提示音': {
        'demand': '想要自定义消息提示音',
        'type': '功能需求',
        'ai_score': 4,
        'ai_reason': 'AI生成音效可行但需求小'
    },
    
    # ===== 问题反馈 (Bug/稳定性) =====
    '拍照/相机': {
        'demand': '微信拍照时经常卡死/黑屏',
        'type': '问题反馈',
        'ai_score': 2,
        'ai_reason': '工程问题，非AI问题'
    },
    '卡顿/崩溃': {
        'demand': '微信整体卡顿/闪退/崩溃',
        'type': '问题反馈',
        'ai_score': 2,
        'ai_reason': '工程优化问题'
    },
    '版本更新': {
        'demand': '更新后出现新问题/功能倒退',
        'type': '问题反馈',
        'ai_score': 2,
        'ai_reason': '产品策略问题'
    },
    '系统适配': {
        'demand': '新系统/新设备适配有问题',
        'type': '问题反馈',
        'ai_score': 2,
        'ai_reason': '适配工程问题'
    },
    '登录': {
        'demand': '登录/扫码遇到问题',
        'type': '问题反馈',
        'ai_score': 4,
        'ai_reason': '人脸识别已应用，空间有限'
    },
    
    # ===== 平台策略/合规 (非AI问题) =====
    '账号封禁': {
        'demand': '账号被封/限制，申诉无门',
        'type': '平台策略',
        'ai_score': 3,
        'ai_reason': '平台策略问题'
    },
    '广告': {
        'demand': '广告太多影响体验',
        'type': '平台策略',
        'ai_score': 2,
        'ai_reason': '商业模式问题'
    },
    '支付/转账': {
        'demand': '支付/转账问题或手续费',
        'type': '平台策略',
        'ai_score': 3,
        'ai_reason': '金融合规问题'
    },
    '隐私/安全': {
        'demand': '担心隐私泄露/安全问题',
        'type': '平台策略',
        'ai_score': 3,
        'ai_reason': '合规问题为主'
    },
    '实名认证': {
        'demand': '频繁要求实名认证',
        'type': '平台策略',
        'ai_score': 3,
        'ai_reason': '合规要求'
    },
    '存储/内存': {
        'demand': '微信占用存储空间太大',
        'type': '平台策略',
        'ai_score': 4,
        'ai_reason': '架构问题，AI空间小'
    },
    '文件传输': {
        'demand': '文件传输慢/大小限制',
        'type': '平台策略',
        'ai_score': 4,
        'ai_reason': '带宽问题为主'
    },
    '已读功能': {
        'demand': '希望有/没有已读功能',
        'type': '平台策略',
        'ai_score': 4,
        'ai_reason': '产品策略问题'
    },
    '内测': {
        'demand': '想要获得内测资格/新功能',
        'type': '平台策略',
        'ai_score': 1,
        'ai_reason': '产品策略问题'
    },
    '多开/分身': {
        'demand': '希望支持微信多开/分身',
        'type': '平台策略',
        'ai_score': 2,
        'ai_reason': '产品策略问题'
    },
}

# 计算统计数据
keyword_stats = []
for kw, samples in keyword_samples.items():
    if kw not in demand_definitions:
        continue
    count = len(samples)
    avg_rating = sum(s['rating'] for s in samples) / count if count > 0 else 0
    low_rating_pct = sum(1 for s in samples if s['rating'] <= 2) / count * 100 if count > 0 else 0
    
    info = demand_definitions[kw]
    # 综合得分
    count_score = min(count / 72 * 10, 10)
    pain_score = low_rating_pct / 10
    composite_score = info['ai_score'] * 0.4 + count_score * 0.3 + pain_score * 0.3
    
    keyword_stats.append({
        'keyword': kw,
        'demand': info['demand'],
        'type': info['type'],
        'count': count,
        'avg_rating': avg_rating,
        'low_rating_pct': low_rating_pct,
        'ai_score': info['ai_score'],
        'ai_reason': info['ai_reason'],
        'composite_score': composite_score
    })

# 排序规则：功能需求 > 问题反馈 > 平台策略，同类内按综合分排序
type_order = {'功能需求': 0, '问题反馈': 1, '平台策略': 2}
keyword_stats.sort(key=lambda x: (type_order[x['type']], -x['composite_score']))

print("=" * 110)
print("【方案A最终版】34个独立需求点 - 用户需求口吻 + 分类标签 + AI介入价值排序")
print("=" * 110)

current_type = None
rank = 0
for stat in keyword_stats:
    if stat['type'] != current_type:
        current_type = stat['type']
        type_count = len([s for s in keyword_stats if s['type'] == current_type])
        type_samples = sum(s['count'] for s in keyword_stats if s['type'] == current_type)
        print(f"\n{'─' * 110}")
        print(f"【{current_type}】({type_count} 个，{type_samples} 条样本)")
        print(f"{'─' * 110}")
        print(f"{'排名':<4} {'用户需求描述':<35} {'提及':<6} {'AI分':<6} {'AI介入方向'}")
        print("-" * 110)
    
    rank += 1
    print(f"{rank:<4} {stat['demand']:<35} {stat['count']:<6} {stat['ai_score']:<6} {stat['ai_reason']}")

print(f"\n{'=' * 110}")
print("【汇总】")
func_req = [s for s in keyword_stats if s['type'] == '功能需求']
bug_req = [s for s in keyword_stats if s['type'] == '问题反馈']
policy_req = [s for s in keyword_stats if s['type'] == '平台策略']
print(f"  功能需求: {len(func_req)} 个，{sum(s['count'] for s in func_req)} 条样本")
print(f"  问题反馈: {len(bug_req)} 个，{sum(s['count'] for s in bug_req)} 条样本")
print(f"  平台策略: {len(policy_req)} 个，{sum(s['count'] for s in policy_req)} 条样本")
