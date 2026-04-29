#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复兜底 user_voice 过度泛化问题：
将 136 个使用 "希望产品能更懂我的需求" 的需求，替换为针对该具体痛点的独立文案。

每个痛点类型有独立的：
- user_voice：用户原声（基于真实评论场景的自然表达）
- ai_solution：AI 方案名称
- ai_description：方案描述
- ai_keywords：关键词标签
"""
import json
from pathlib import Path

# ============================================
# 针对每个痛点标题的独立文案
# ============================================
SPECIFIC_SOLUTIONS = {
    # ===== 性能与崩溃 =====
    '功能崩溃': {
        'user_voice': '经常用着用着就闪退，刚输入的内容全没了',
        'ai_solution': 'AI 稳定性守护',
        'ai_description': 'AI 实时监测异常状态并自动恢复上下文；闪退前智能保存未提交内容；预测性能瓶颈提前优化',
        'ai_keywords': ['异常恢复', '自动保存', '预测优化'],
    },
    '启动崩溃': {
        'user_voice': '每次点开图标要么白屏要么直接闪退，根本打不开',
        'ai_solution': 'AI 启动诊断',
        'ai_description': 'AI 自动诊断启动失败原因并尝试修复；智能清理冲突缓存；提供安全模式进入',
        'ai_keywords': ['启动诊断', '冲突修复', '安全模式'],
    },
    '兼容性': {
        'user_voice': '换了新手机就各种问题，老系统上根本跑不动',
        'ai_solution': 'AI 自适应兼容',
        'ai_description': 'AI 根据设备型号和系统版本动态调整功能；老设备自动切换轻量模式；兼容性问题智能降级',
        'ai_keywords': ['设备适配', '轻量模式', '智能降级'],
    },
    '视频卡顿': {
        'user_voice': '视频一播放就开始转圈，画质还被压得很糟糕',
        'ai_solution': 'AI 智能播放优化',
        'ai_description': 'AI 根据网络状况智能切换码率；预测网络波动预加载；画质增强算法补偿压缩损失',
        'ai_keywords': ['码率切换', '智能预加载', '画质增强'],
    },
    '响应缓慢': {
        'user_voice': '点个按钮要等半天才有反应，急用的时候特别崩溃',
        'ai_solution': 'AI 响应加速',
        'ai_description': 'AI 预测用户下一步操作预加载；后台任务智能调度避免阻塞；操作热点优先响应',
        'ai_keywords': ['操作预测', '调度优化', '热点优先'],
    },
    
    # ===== 搜索与记录 =====
    '搜索差': {
        'user_voice': '记得自己看过但怎么搜都搜不到，搜索功能跟摆设一样',
        'ai_solution': 'AI 语义搜索',
        'ai_description': 'AI 理解搜索意图，支持模糊描述和自然语言；跨类型全文索引；智能排序最相关结果',
        'ai_keywords': ['语义理解', '全文索引', '意图识别'],
    },
    '记录难找': {
        'user_voice': '几个月前的聊天记录翻半天都找不到，时间线根本没法定位',
        'ai_solution': 'AI 历史记录助手',
        'ai_description': 'AI 按主题/时间/人物智能归档；自然语言定位"上周那条消息"；自动生成记录摘要',
        'ai_keywords': ['智能归档', '自然语言', '自动摘要'],
    },
    '文件过期': {
        'user_voice': '聊天里的文件过期打不开了，也没人提前提醒我',
        'ai_solution': 'AI 文件管家',
        'ai_description': '重要文件 AI 识别自动云端长存；即将过期主动提醒；一键批量续存',
        'ai_keywords': ['重要识别', '到期提醒', '批量续存'],
    },
    '清理困难': {
        'user_voice': '存储爆满想清理又不敢乱删，生怕误删掉重要东西',
        'ai_solution': 'AI 智能清理',
        'ai_description': 'AI 识别可安全清理的内容并分类展示；重要文件自动保护；清理前可预览还原',
        'ai_keywords': ['安全识别', '智能分类', '还原保护'],
    },

    # ===== 匹配与推荐 =====
    '匹配问题': {
        'user_voice': '推的人根本不是我的菜，算法好像完全不懂我喜欢什么',
        'ai_solution': 'AI 深度匹配',
        'ai_description': 'AI 从多维度提取真实兴趣和价值观；打破相似回音壁适度引入差异化；持续学习修正偏好',
        'ai_keywords': ['深度兴趣', '差异引入', '动态学习'],
    },
    '推荐不准': {
        'user_voice': '推的东西跟我毫无关系，用得越久反而越不准',
        'ai_solution': 'AI 推荐纠偏',
        'ai_description': 'AI 支持用户主动反馈调教推荐；识别偶然行为避免过度跟随；定期多样化注入',
        'ai_keywords': ['主动调教', '偶然识别', '多样注入'],
    },
    '内容重复': {
        'user_voice': '首页翻来翻去都是那几条，刷半天没新东西',
        'ai_solution': 'AI 去重推荐',
        'ai_description': 'AI 识别同质化内容自动去重；扩展兴趣边界引入新鲜素材；跨领域关联推荐',
        'ai_keywords': ['同质去重', '边界扩展', '跨域关联'],
    },
    '内容匮乏': {
        'user_voice': '想看的类型一直刷不到，平台感觉啥都没有',
        'ai_solution': 'AI 内容发掘',
        'ai_description': 'AI 跨平台整合稀缺内容；长尾兴趣精准触达；小众创作者智能推荐',
        'ai_keywords': ['跨域整合', '长尾触达', '小众发掘'],
    },
    '内容低质': {
        'user_voice': '刷到的都是水文搬运，找个有深度的内容太难了',
        'ai_solution': 'AI 内容质检',
        'ai_description': 'AI 识别原创度和信息密度；低质内容自动降权；优质创作者优先触达',
        'ai_keywords': ['原创识别', '质量评分', '优质优先'],
    },
    '信息茧房': {
        'user_voice': '算法只推我已经看过的同类，视野越来越窄',
        'ai_solution': 'AI 破茧推荐',
        'ai_description': 'AI 主动注入跨领域优质内容；识别兴趣固化并柔性引导；支持用户自主探索模式',
        'ai_keywords': ['主动破茧', '柔性引导', '探索模式'],
    },
    '算法成瘾': {
        'user_voice': '一刷就停不下来，抬头一看两三个小时过去了',
        'ai_solution': 'AI 使用时长守护',
        'ai_description': 'AI 识别沉浸状态适时提醒；提供"足够了"的自然断点；帮助用户设定理性目标',
        'ai_keywords': ['沉浸识别', '自然断点', '理性使用'],
    },

    # ===== 消息与通知 =====
    '消息延迟': {
        'user_voice': '消息明明显示送达了对方却没收到，错过重要事情',
        'ai_solution': 'AI 送达保障',
        'ai_description': 'AI 识别送达异常并主动补发；关键消息多通道冗余；延迟情况实时可视化',
        'ai_keywords': ['送达校验', '多通道', '实时可视'],
    },
    '通知过多': {
        'user_voice': '一打开手机几十条通知，真正重要的反而被淹没',
        'ai_solution': 'AI 通知分级',
        'ai_description': 'AI 识别消息紧急度动态分级；学习用户节奏智能免打扰；紧急消息才打破沉默',
        'ai_keywords': ['紧急识别', '节奏学习', '智能免扰'],
    },
    '通知丢失': {
        'user_voice': '重要消息没响，等看到时已经错过了时机',
        'ai_solution': 'AI 关键消息守护',
        'ai_description': 'AI 识别重要消息多次重试推送；系统层级权限异常主动提醒；关键联系人白名单',
        'ai_keywords': ['重试推送', '权限检测', '关键白名单'],
    },
    '骚扰信息': {
        'user_voice': '陌生人私信和垃圾营销信息一大堆，删都删不完',
        'ai_solution': 'AI 骚扰拦截',
        'ai_description': 'AI 识别营销/骚扰/诈骗消息自动归档；陌生联系人行为评分；一键批量清理',
        'ai_keywords': ['智能识别', '行为评分', '批量清理'],
    },
    '互动障碍': {
        'user_voice': '想加个好友或者发个消息各种限制，操作跟走迷宫似的',
        'ai_solution': 'AI 互动简化',
        'ai_description': 'AI 简化社交操作路径；识别合理互动减少限制拦截；异常行为精准识别而非一刀切',
        'ai_keywords': ['路径简化', '精准识别', '减少误伤'],
    },

    # ===== 安全与隐私 =====
    '虚假诈骗': {
        'user_voice': '平台上骗子一大堆，被骗了维权都没门',
        'ai_solution': 'AI 反诈守护',
        'ai_description': 'AI 识别诈骗话术和异常交易主动预警；骗子账号多维度画像自动封禁；受害者快速救助通道',
        'ai_keywords': ['话术识别', '主动预警', '快速救助'],
    },
    '虚假内容': {
        'user_voice': '平台上假消息满天飞，真假根本分不清',
        'ai_solution': 'AI 内容核实',
        'ai_description': 'AI 交叉验证信息来源标注可信度；识别 AI 生成内容主动标记；异常传播快速拦截',
        'ai_keywords': ['来源核实', 'AI 标记', '传播拦截'],
    },
    '隐私泄露': {
        'user_voice': '刚聊完什么就被精准推广告，隐私完全没保障',
        'ai_solution': 'AI 隐私守护',
        'ai_description': 'AI 审计数据使用链路；识别越权采集并拦截；提供隐私沙盒模式',
        'ai_keywords': ['链路审计', '越权拦截', '隐私沙盒'],
    },
    '行为追踪': {
        'user_voice': 'App 后台一直在记录我的行为，想关又找不到开关',
        'ai_solution': 'AI 追踪阻断',
        'ai_description': 'AI 识别后台追踪行为自动拦截；一键关闭非必要数据采集；追踪记录透明可见',
        'ai_keywords': ['追踪识别', '一键关闭', '透明展示'],
    },
    '权限滥用': {
        'user_voice': 'App 要通讯录、定位、相册的权限，不给就不让用',
        'ai_solution': 'AI 权限最小化',
        'ai_description': 'AI 判断功能真实所需权限并提示；模拟授权避免真实泄露；权限使用全程可审计',
        'ai_keywords': ['最小授权', '模拟权限', '使用审计'],
    },
    '设备封禁': {
        'user_voice': '什么都没干就被封了设备，连申诉入口都找不到',
        'ai_solution': 'AI 精准风控',
        'ai_description': 'AI 行为分析减少一刀切封禁；封禁原因透明告知；申诉快速通道自动流转',
        'ai_keywords': ['精准风控', '原因透明', '快速申诉'],
    },

    # ===== 账号与客服 =====
    '客服难联系': {
        'user_voice': '想找人工客服隐藏得比宝藏还深，绕一大圈都找不到',
        'ai_solution': 'AI 客服直达',
        'ai_description': 'AI 快速识别复杂问题直转人工；多渠道统一入口；排队等待时间透明可见',
        'ai_keywords': ['快速转人工', '统一入口', '透明排队'],
    },
    '机器人客服': {
        'user_voice': '问题复杂一点机器人根本听不懂，答非所问',
        'ai_solution': 'AI 深度理解客服',
        'ai_description': '基于大模型的客服可理解复杂表达；识别机器人无法解决时自动转人工；上下文连贯不丢失',
        'ai_keywords': ['深度理解', '智能转接', '上下文连贯'],
    },
    '问题未解决': {
        'user_voice': '客服回复一堆官话，问题一个都没解决',
        'ai_solution': 'AI 问题闭环',
        'ai_description': 'AI 追踪问题解决进度直到关闭；未解决问题自动升级；用户满意度实时评估',
        'ai_keywords': ['进度追踪', '自动升级', '满意度评估'],
    },
    '申诉困难': {
        'user_voice': '申诉提交上去石沉大海，也不告诉我被拒的理由',
        'ai_solution': 'AI 申诉助手',
        'ai_description': 'AI 协助用户整理申诉材料提高通过率；申诉进度透明可见；拒绝原因详细说明',
        'ai_keywords': ['材料整理', '进度透明', '详细说明'],
    },
    '禁言限制': {
        'user_voice': '好好说话突然就被禁言，理由模糊到离谱',
        'ai_solution': 'AI 精准管理',
        'ai_description': 'AI 精准识别违规内容减少误判；禁言理由具体到语句；快速申诉解除通道',
        'ai_keywords': ['精准识别', '具体告知', '快速解除'],
    },
    '验证繁琐': {
        'user_voice': '登录要人脸还要短信再来个拼图，麻烦得不想用了',
        'ai_solution': 'AI 无感验证',
        'ai_description': 'AI 行为分析实现无感身份验证；风险低时免验证；风险高时才加强验证',
        'ai_keywords': ['无感验证', '风险自适应', '流程简化'],
    },

    # ===== 付费问题 =====
    '订阅扣费': {
        'user_voice': '自动续费悄悄扣钱，取消入口藏得跟找针似的',
        'ai_solution': 'AI 订阅透明',
        'ai_description': 'AI 主动识别到期订阅并提醒；取消入口一键直达；历史扣费清晰可查',
        'ai_keywords': ['到期提醒', '一键取消', '扣费透明'],
    },
    '退款困难': {
        'user_voice': '申请退款被各种推诿拖延，钱就是不退给我',
        'ai_solution': 'AI 退款助手',
        'ai_description': 'AI 判定退款合理性快速响应；处理进度实时可见；超时未处理自动升级',
        'ai_keywords': ['合理性判定', '进度可视', '超时升级'],
    },
    '隐性收费': {
        'user_voice': '说好的免费，用着用着发现一堆功能要收费',
        'ai_solution': 'AI 收费透明',
        'ai_description': 'AI 识别隐性付费点主动提示；使用前明确告知成本；推荐最划算的付费方案',
        'ai_keywords': ['付费识别', '成本告知', '方案推荐'],
    },
    '强制更新': {
        'user_voice': '不更新就不让用，更新完功能反而变差了',
        'ai_solution': 'AI 更新自主',
        'ai_description': 'AI 识别关键安全更新与非必要更新；用户自主选择版本；旧版本提供降级回退',
        'ai_keywords': ['关键识别', '自主选择', '降级回退'],
    },
    '更新变差': {
        'user_voice': '更新以后反而越来越难用，老功能都被改没了',
        'ai_solution': 'AI 体验守护',
        'ai_description': 'AI 识别用户依赖的经典功能持续保留；更新前 A/B 测试减少负反馈；支持用户反馈快速回滚',
        'ai_keywords': ['功能保留', 'A/B 测试', '快速回滚'],
    },

    # ===== 界面与操作 =====
    '界面丑陋': {
        'user_voice': '界面设计又土又挤，看着就不想用',
        'ai_solution': 'AI 界面个性化',
        'ai_description': 'AI 根据用户偏好推荐主题配色；智能布局适配不同使用场景；支持一键换肤',
        'ai_keywords': ['偏好推荐', '智能布局', '一键换肤'],
    },
    '操作复杂': {
        'user_voice': '想做件简单的事要点好多步，入口藏得又深',
        'ai_solution': 'AI 操作简化',
        'ai_description': 'AI 学习用户常用路径生成快捷方式；语音一句话完成操作；新手引导精准到点',
        'ai_keywords': ['路径学习', '语音操作', '精准引导'],
    },
    '字体问题': {
        'user_voice': '字太小了眼睛都看花了，调大又把布局撑乱了',
        'ai_solution': 'AI 自适应排版',
        'ai_description': 'AI 根据字号动态重排界面保持美观；护眼模式智能识别环境；无障碍支持老年人模式',
        'ai_keywords': ['动态重排', '护眼识别', '无障碍'],
    },
    '暗色模式': {
        'user_voice': '晚上看屏幕刺眼，想要真正的深色模式',
        'ai_solution': 'AI 智能显示',
        'ai_description': 'AI 根据环境光和时间自动切换；深色模式全界面一致覆盖；OLED 屏幕纯黑省电',
        'ai_keywords': ['环境感知', '一致切换', 'OLED 优化'],
    },
    '离线功能': {
        'user_voice': '没网的时候几乎什么都做不了，基础功能也要联网',
        'ai_solution': 'AI 离线增强',
        'ai_description': 'AI 智能预缓存常用内容；核心功能支持完全离线运行；联网后自动同步',
        'ai_keywords': ['预缓存', '离线运行', '自动同步'],
    },
    '语音控制': {
        'user_voice': '开车做饭时想用语音操作，结果识别错一大堆',
        'ai_solution': 'AI 语音交互',
        'ai_description': 'AI 支持自然语言完成复杂操作；方言口音智能适配；噪声环境准确识别',
        'ai_keywords': ['自然语言', '方言适配', '抗噪识别'],
    },
    '语音转文字': {
        'user_voice': '语音转文字识别错字一大堆，还要一句句改',
        'ai_solution': 'AI 精准转写',
        'ai_description': 'AI 结合上下文智能纠错；专业术语和人名智能识别；支持多语言和方言混合',
        'ai_keywords': ['上下文纠错', '术语识别', '多语言支持'],
    },
}


def fix_file(file_path: Path) -> int:
    """修复单个文件中的兜底 user_voice"""
    if not file_path.exists():
        return 0
    
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    opps = data.get('ai_opportunities', [])
    fixed_count = 0
    
    for opp in opps:
        title = opp.get('title', '')
        # 只修复兜底方案的需求
        if opp.get('user_voice') != '希望产品能更懂我的需求':
            continue
        
        if title in SPECIFIC_SOLUTIONS:
            spec = SPECIFIC_SOLUTIONS[title]
            opp['user_voice'] = spec['user_voice']
            opp['ai_solution'] = spec['ai_solution']
            opp['ai_description'] = spec['ai_description']
            opp['ai_keywords'] = spec['ai_keywords']
            fixed_count += 1
    
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    return fixed_count


def main():
    base = Path('data/processed')
    total_fixed = 0
    total_remaining = 0
    
    for cat in ['wechat', 'social', 'ai', 'more']:
        file_path = base / f'{cat}_ai_opportunities_consolidated.json'
        fixed = fix_file(file_path)
        total_fixed += fixed
        
        # 统计还有多少没修复
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        remaining = [
            opp['title'] for opp in data.get('ai_opportunities', [])
            if opp.get('user_voice') == '希望产品能更懂我的需求'
        ]
        total_remaining += len(remaining)
        
        print(f'[{cat}] 修复 {fixed} 个需求', end='')
        if remaining:
            print(f'，仍有 {len(remaining)} 个未覆盖: {remaining[:5]}')
        else:
            print()
    
    print(f'\n总计修复: {total_fixed} 个需求')
    if total_remaining > 0:
        print(f'仍有 {total_remaining} 个标题未在 SPECIFIC_SOLUTIONS 中定义')


if __name__ == '__main__':
    main()
