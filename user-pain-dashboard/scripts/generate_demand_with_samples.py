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

# 收集样本（包含完整信息）
keyword_samples = defaultdict(list)
for r in reviews:
    content = r.get('content', '')
    rating = r.get('rating', 0)
    review_id = r.get('id', '')
    kws = extract_semantic_keywords(content)
    for kw in kws:
        keyword_samples[kw].append({
            'content': content,
            'rating': rating,
            'review_id': review_id
        })

# 需求点定义
demand_definitions = {
    '朋友圈': {'demand': '希望朋友圈发布和管理体验更好', 'type': '功能需求', 'ai_score': 7},
    '内容折叠': {'demand': '希望内容折叠更智能/可自定义', 'type': '功能需求', 'ai_score': 8},
    '画质': {'demand': '希望发送图片/视频画质不被压缩', 'type': '功能需求', 'ai_score': 9},
    '语音转文字': {'demand': '希望语音转文字更准确', 'type': '功能需求', 'ai_score': 9},
    '客服': {'demand': '希望能找到人工客服解决问题', 'type': '功能需求', 'ai_score': 6},
    '公众号': {'demand': '希望公众号/服务号消息不被折叠', 'type': '功能需求', 'ai_score': 5},
    '消息通知': {'demand': '希望消息通知更及时准确', 'type': '功能需求', 'ai_score': 6},
    '聊天记录': {'demand': '希望聊天记录更容易搜索和管理', 'type': '功能需求', 'ai_score': 7},
    '通话功能': {'demand': '希望语音/视频通话质量更好', 'type': '功能需求', 'ai_score': 5},
    '表情/贴图': {'demand': '希望有更多表情包和贴图选择', 'type': '功能需求', 'ai_score': 7},
    '外观定制': {'demand': '希望能自定义聊天气泡/主题颜色', 'type': '功能需求', 'ai_score': 6},
    '朋友圈编辑': {'demand': '希望能编辑已发布的朋友圈', 'type': '功能需求', 'ai_score': 8},
    '群聊管理': {'demand': '希望群聊管理功能更完善', 'type': '功能需求', 'ai_score': 6},
    '配乐功能': {'demand': '希望朋友圈图片能配背景音乐', 'type': '功能需求', 'ai_score': 8},
    '待办/日程': {'demand': '希望有更好的待办/日程提醒功能', 'type': '功能需求', 'ai_score': 7},
    '好友管理': {'demand': '希望好友分组和清理功能更好用', 'type': '功能需求', 'ai_score': 5},
    '键盘/输入': {'demand': '希望输入法/键盘适配更好', 'type': '功能需求', 'ai_score': 6},
    '小程序': {'demand': '希望小程序体验更流畅', 'type': '功能需求', 'ai_score': 5},
    '铃声/提示音': {'demand': '想要自定义消息提示音', 'type': '功能需求', 'ai_score': 4},
    '拍照/相机': {'demand': '微信拍照时经常卡死/黑屏', 'type': '问题反馈', 'ai_score': 2},
    '卡顿/崩溃': {'demand': '微信整体卡顿/闪退/崩溃', 'type': '问题反馈', 'ai_score': 2},
    '版本更新': {'demand': '更新后出现新问题/功能倒退', 'type': '问题反馈', 'ai_score': 2},
    '系统适配': {'demand': '新系统/新设备适配有问题', 'type': '问题反馈', 'ai_score': 2},
    '登录': {'demand': '登录/扫码遇到问题', 'type': '问题反馈', 'ai_score': 4},
    '账号封禁': {'demand': '账号被封/限制，申诉无门', 'type': '平台策略', 'ai_score': 3},
    '广告': {'demand': '广告太多影响体验', 'type': '平台策略', 'ai_score': 2},
    '支付/转账': {'demand': '支付/转账问题或手续费', 'type': '平台策略', 'ai_score': 3},
    '隐私/安全': {'demand': '担心隐私泄露/安全问题', 'type': '平台策略', 'ai_score': 3},
    '实名认证': {'demand': '频繁要求实名认证', 'type': '平台策略', 'ai_score': 3},
    '存储/内存': {'demand': '微信占用存储空间太大', 'type': '平台策略', 'ai_score': 4},
    '文件传输': {'demand': '文件传输慢/大小限制', 'type': '平台策略', 'ai_score': 4},
    '已读功能': {'demand': '希望有/没有已读功能', 'type': '平台策略', 'ai_score': 4},
    '内测': {'demand': '想要获得内测资格/新功能', 'type': '平台策略', 'ai_score': 1},
    '多开/分身': {'demand': '希望支持微信多开/分身', 'type': '平台策略', 'ai_score': 2},
}

# 计算统计并排序
keyword_stats = []
for kw, samples in keyword_samples.items():
    if kw not in demand_definitions:
        continue
    count = len(samples)
    avg_rating = sum(s['rating'] for s in samples) / count if count > 0 else 0
    low_rating_pct = sum(1 for s in samples if s['rating'] <= 2) / count * 100 if count > 0 else 0
    
    info = demand_definitions[kw]
    count_score = min(count / 72 * 10, 10)
    pain_score = low_rating_pct / 10
    composite_score = info['ai_score'] * 0.4 + count_score * 0.3 + pain_score * 0.3
    
    keyword_stats.append({
        'keyword': kw,
        'demand': info['demand'],
        'type': info['type'],
        'count': count,
        'ai_score': info['ai_score'],
        'composite_score': composite_score,
        'samples': samples
    })

# 排序
type_order = {'功能需求': 0, '问题反馈': 1, '平台策略': 2}
keyword_stats.sort(key=lambda x: (type_order[x['type']], -x['composite_score']))

# 输出带样本的完整列表
print("=" * 120)
print("【方案A完整版】34个独立需求点 + 典型样本")
print("=" * 120)

current_type = None
rank = 0

for stat in keyword_stats:
    if stat['type'] != current_type:
        current_type = stat['type']
        print(f"\n{'═' * 120}")
        print(f"【{current_type}】")
        print(f"{'═' * 120}")
    
    rank += 1
    print(f"\n{'─' * 120}")
    print(f"#{rank} {stat['demand']}")
    print(f"    提及: {stat['count']}条 | AI介入分: {stat['ai_score']}/10")
    print(f"{'─' * 120}")
    print("典型样本：")
    
    # 选取最多3条典型样本（优先选低分的，更能体现痛点）
    sorted_samples = sorted(stat['samples'], key=lambda x: x['rating'])
    display_count = min(3, len(sorted_samples))
    
    for i, sample in enumerate(sorted_samples[:display_count], 1):
        content = sample['content'].replace('\n', ' ').strip()
        rating = sample['rating']
        print(f"  [{i}] ★{'★' * (rating-1) if rating > 0 else '☆'}{'☆' * (5-rating)} ({rating}星)")
        print(f"      「{content}」")
        print()

print(f"\n{'=' * 120}")
print("【统计汇总】")
func_req = [s for s in keyword_stats if s['type'] == '功能需求']
bug_req = [s for s in keyword_stats if s['type'] == '问题反馈']
policy_req = [s for s in keyword_stats if s['type'] == '平台策略']
print(f"  功能需求: {len(func_req)} 个需求点，{sum(s['count'] for s in func_req)} 条样本")
print(f"  问题反馈: {len(bug_req)} 个需求点，{sum(s['count'] for s in bug_req)} 条样本")
print(f"  平台策略: {len(policy_req)} 个需求点，{sum(s['count'] for s in policy_req)} 条样本")
