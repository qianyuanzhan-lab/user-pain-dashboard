#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
强制对齐所有需求的 title 与 user_voice/ai_solution。
遇到新增标题继续扩充这份权威映射即可。
"""
import json
from pathlib import Path

# 权威映射表：title → 方案
# 原则：voice 必须直接反映 title 描述的场景
AUTHORITATIVE_SOLUTIONS = {
    # ===== 存储 / 性能 / 崩溃 =====
    '存储与性能': {
        'user_voice': '占用几十G空间，清理功能又不敢用，怕删掉重要文件',
        'ai_solution': '智能存储优化',
        'ai_description': 'AI 分析文件使用频率和重要性，自动推荐清理方案；智能压缩不常用内容；后台资源智能调度降低耗电',
        'ai_keywords': ['智能清理', '自动压缩', '资源调度'],
    },
    '应用性能': {
        'user_voice': '用一会儿就发烫卡顿，电量也掉得飞快',
        'ai_solution': '智能性能优化',
        'ai_description': 'AI 根据使用场景动态调整性能策略；智能预加载常用内容；后台资源智能管理',
        'ai_keywords': ['动态优化', '预加载', '资源管理'],
    },
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
    '工具性能': {
        'user_voice': '软件越用越卡，占用空间也越来越大',
        'ai_solution': '智能性能调优',
        'ai_description': 'AI 分析使用模式优化资源分配；智能清理缓存；后台任务智能调度',
        'ai_keywords': ['资源优化', '智能清理', '任务调度'],
    },
    '清理困难': {
        'user_voice': '存储爆满想清理又不敢乱删，生怕误删掉重要东西',
        'ai_solution': 'AI 智能清理',
        'ai_description': 'AI 识别可安全清理的内容并分类展示；重要文件自动保护；清理前可预览还原',
        'ai_keywords': ['安全识别', '智能分类', '还原保护'],
    },

    # ===== 搜索 / 记录 / 文件 =====
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

    # ===== 匹配 / 推荐 / 内容 =====
    '匹配问题': {
        'user_voice': '推的人根本不是我的菜，算法好像完全不懂我喜欢什么',
        'ai_solution': 'AI 深度匹配',
        'ai_description': 'AI 从多维度提取真实兴趣和价值观；打破相似回音壁适度引入差异化；持续学习修正偏好',
        'ai_keywords': ['深度兴趣', '差异引入', '动态学习'],
    },
    '匹配与推荐': {
        'user_voice': '推荐的人都不合适，感觉算法根本不懂我',
        'ai_solution': '真实匹配算法',
        'ai_description': 'AI 多维度分析用户真实偏好；打破信息茧房引入新鲜内容；基于深度兴趣而非表面数据匹配',
        'ai_keywords': ['深度匹配', '兴趣挖掘', '茧房破解'],
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
    '内容质量': {
        'user_voice': '刷到的内容越来越水，找个有深度的内容太难了',
        'ai_solution': 'AI 内容优选',
        'ai_description': 'AI 识别优质原创内容优先推荐；过滤低质搬运内容；支持用户个性化品味学习',
        'ai_keywords': ['原创优先', '品味学习', '质量筛选'],
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

    # ===== 消息 / 通知 =====
    '消息与通知问题': {
        'user_voice': '群消息太多了，重要的信息经常被淹没',
        'ai_solution': '智能消息管理',
        'ai_description': 'AI 自动识别消息重要程度，智能分级提醒；学习用户习惯，在合适时机推送；自动归类群消息，提取关键信息摘要',
        'ai_keywords': ['消息分级', '智能提醒', '信息摘要'],
    },
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
    '通知打扰': {
        'user_voice': '工作群消息太多了，重要的总是漏看',
        'ai_solution': '智能勿扰模式',
        'ai_description': 'AI 识别消息重要程度智能分级；学习工作节奏自动调整通知时机；紧急消息才打扰',
        'ai_keywords': ['消息分级', '节奏学习', '智能打扰'],
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

    # ===== 安全 / 隐私 / 权限 =====
    '社交压力与隐私': {
        'user_voice': '不想让所有人看到我的朋友圈，分组又太麻烦',
        'ai_solution': 'AI 隐私助手',
        'ai_description': 'AI 帮助用户管理社交边界，智能分组可见范围；识别潜在隐私风险并提醒；提供"社交降压"模式',
        'ai_keywords': ['隐私保护', '社交边界', '智能分组'],
    },
    '真实性与安全': {
        'user_voice': '遇到好多假照片和骗子，浪费时间又担心被骗',
        'ai_solution': 'AI 真人验证',
        'ai_description': 'AI 图片鉴伪识别照骗；行为分析识别机器人和骗子；实时预警诈骗风险',
        'ai_keywords': ['图片鉴伪', '行为分析', '诈骗预警'],
    },
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
        'user_voice': 'App 动不动就要通讯录、定位、相册权限，不给就没法用',
        'ai_solution': 'AI 权限最小化',
        'ai_description': 'AI 判断功能真实所需权限并提示；模拟授权避免真实泄露；权限使用全程可审计',
        'ai_keywords': ['最小授权', '模拟权限', '使用审计'],
    },

    # ===== 账号 / 客服 / 申诉 =====
    '账号安全': {
        'user_voice': '账号突然就被盗登了，也没收到任何风险提醒',
        'ai_solution': 'AI 安全守护',
        'ai_description': 'AI 行为分析识别异常登录；异地登录主动预警推送；提供更便捷的身份验证方式',
        'ai_keywords': ['异常登录', '主动预警', '身份验证'],
    },
    '账号问题': {
        'user_voice': '莫名其妙就被封号，申诉也没人理',
        'ai_solution': 'AI 账号守护',
        'ai_description': 'AI 行为分析减少误封；智能身份验证替代繁琐流程；账号异常快速预警',
        'ai_keywords': ['误封减少', '智能验证', '异常预警'],
    },
    '账号绑定': {
        'user_voice': '想换绑手机号或邮箱特别麻烦，旧号不能用就彻底登不上',
        'ai_solution': 'AI 绑定简化',
        'ai_description': 'AI 多因子身份核验替代单一手机号依赖；支持多种可信凭证登录；紧急换绑快速通道',
        'ai_keywords': ['多因子核验', '多凭证登录', '快速换绑'],
    },
    '设备封禁': {
        'user_voice': '什么都没干就被封了设备，连申诉入口都找不到',
        'ai_solution': 'AI 精准风控',
        'ai_description': 'AI 行为分析减少一刀切封禁；封禁原因透明告知；申诉快速通道自动流转',
        'ai_keywords': ['精准风控', '原因透明', '快速申诉'],
    },
    '客服响应': {
        'user_voice': '客服永远是机器人回复，问题解决不了',
        'ai_solution': 'AI 客服升级',
        'ai_description': '更智能的 AI 客服理解复杂问题；快速转人工通道；问题追踪和进度提醒',
        'ai_keywords': ['智能客服', '问题追踪', '快速响应'],
    },
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

    # ===== 付费 / 会员 / 广告 =====
    '支付与转账': {
        'user_voice': '转错账了客服也不管，太难追回了',
        'ai_solution': '智能支付助手',
        'ai_description': 'AI 识别异常交易并提醒；智能推荐最优支付方式；自动记账和消费分析',
        'ai_keywords': ['风险识别', '智能推荐', '消费分析'],
    },
    '会员与付费': {
        'user_voice': '开了会员发现功能都用不上，感觉被坑了',
        'ai_solution': '智能权益推荐',
        'ai_description': 'AI 分析使用习惯推荐最适合的会员方案；透明化付费项说明；智能提醒避免忘记取消订阅',
        'ai_keywords': ['权益匹配', '透明消费', '订阅管理'],
    },
    '会员付费': {
        'user_voice': '开了会员发现功能都用不上，感觉被坑了',
        'ai_solution': '智能权益推荐',
        'ai_description': 'AI 分析使用习惯推荐最适合的会员方案；透明化付费项说明；智能提醒避免忘记取消订阅',
        'ai_keywords': ['权益匹配', '透明消费', '订阅管理'],
    },
    '付费不值': {
        'user_voice': '开了会员但很多功能用不上，感觉不值',
        'ai_solution': '智能订阅管理',
        'ai_description': 'AI 分析使用情况推荐最优方案；到期提醒和自动续费管理；权益使用透明展示',
        'ai_keywords': ['方案推荐', '续费管理', '权益透明'],
    },
    '付费问题': {
        'user_voice': '开了会员但很多功能用不上，感觉不值',
        'ai_solution': '智能订阅管理',
        'ai_description': 'AI 分析使用情况推荐最优方案；到期提醒和自动续费管理；权益使用透明展示',
        'ai_keywords': ['方案推荐', '续费管理', '权益透明'],
    },
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
    '广告干扰': {
        'user_voice': '广告又多又容易误点，体验太差了',
        'ai_solution': 'AI 广告优化',
        'ai_description': 'AI 学习用户偏好减少无关广告；智能规避误触设计；提供广告免打扰时段',
        'ai_keywords': ['精准投放', '防误触', '免打扰'],
    },
    '广告问题': {
        'user_voice': '广告太多影响使用，还总是容易误点',
        'ai_solution': 'AI 广告过滤',
        'ai_description': 'AI 学习用户偏好精准过滤无关广告；智能防误触机制；提供无广告专注模式',
        'ai_keywords': ['精准过滤', '防误触', '专注模式'],
    },
    '弹窗广告': {
        'user_voice': '弹窗广告防不胜防，关一个又来一个',
        'ai_solution': 'AI 弹窗拦截',
        'ai_description': 'AI 识别诱导性弹窗自动拦截；整合广告出现频率和位置学习；提供纯净使用模式',
        'ai_keywords': ['弹窗识别', '频率学习', '纯净模式'],
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

    # ===== 界面 / 操作 / 离线 =====
    '小程序体验': {
        'user_voice': '每次打开小程序都要等很久，体验太差了',
        'ai_solution': '小程序智能加速',
        'ai_description': 'AI 预测用户常用小程序并预加载；智能缓存管理；优化启动流程减少等待时间',
        'ai_keywords': ['预加载', '智能缓存', '启动优化'],
    },
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

    # ===== 社区氛围 =====
    '社区氛围': {
        'user_voice': '评论区全是水军和杠精，正常讨论都没法进行',
        'ai_solution': 'AI 社区净化',
        'ai_description': 'AI 识别水军和低质内容；维护健康讨论氛围；智能过滤引战和负面信息',
        'ai_keywords': ['内容过滤', '氛围维护', '水军识别'],
    },

    # ===== AI 应用子类 =====
    'AI 回答质量': {
        'user_voice': 'AI 经常一本正经胡说八道，专业问题的回答根本不靠谱',
        'ai_solution': 'AI 回答增强',
        'ai_description': '引入实时信息检索确保时效性；增强专业领域知识库；明确标注不确定内容避免幻觉',
        'ai_keywords': ['实时检索', '专业增强', '幻觉标注'],
    },
    'AI回答质量': {
        'user_voice': 'AI 经常一本正经胡说八道，专业问题的回答根本不靠谱',
        'ai_solution': 'AI 回答增强',
        'ai_description': '引入实时信息检索确保时效性；增强专业领域知识库；明确标注不确定内容避免幻觉',
        'ai_keywords': ['实时检索', '专业增强', '幻觉标注'],
    },
    'AI 记忆能力': {
        'user_voice': '每次对话都要重新说一遍背景，太麻烦了',
        'ai_solution': '长期记忆系统',
        'ai_description': '构建用户专属记忆库；支持跨对话上下文关联；重要信息永久保存',
        'ai_keywords': ['记忆库', '上下文关联', '永久记忆'],
    },
    '使用限制与成本': {
        'user_voice': '免费次数用完就要付费，价格还不便宜',
        'ai_solution': '智能用量管理',
        'ai_description': 'AI 优化问答效率减少无效消耗；提供更灵活的付费方案；智能推荐最优使用策略',
        'ai_keywords': ['效率优化', '灵活付费', '用量策略'],
    },
    '响应速度': {
        'user_voice': '等待回复的时间太长了，急用的时候很着急',
        'ai_solution': '加速响应',
        'ai_description': '边生成边输出减少等待；智能预测常见问题预生成；优化模型推理效率',
        'ai_keywords': ['流式输出', '预生成', '推理优化'],
    },
    '内容审核': {
        'user_voice': '正常创作内容也被审核拦截，创作空间太小了',
        'ai_solution': '智能审核优化',
        'ai_description': 'AI 理解创作意图减少误判；提供审核解释和修改建议；支持申诉快速响应',
        'ai_keywords': ['意图理解', '修改建议', '快速申诉'],
    },
    '交互体验': {
        'user_voice': '功能太多了找不到，操作也不够直观',
        'ai_solution': '自然交互升级',
        'ai_description': 'AI 学习用户习惯自动调整界面；智能功能推荐；提供个性化使用引导',
        'ai_keywords': ['习惯学习', '功能推荐', '个性化引导'],
    },
    'AI信息过时': {
        'user_voice': 'AI 回答的信息还是几年前的，问最新的事情完全不知道',
        'ai_solution': 'AI 实时知识注入',
        'ai_description': 'AI 接入实时搜索引擎和新闻源；回答自动标注信息时间；过时内容主动提示核实',
        'ai_keywords': ['实时检索', '时间标注', '主动提示'],
    },
    'AI定价贵': {
        'user_voice': '订阅一个月顶一顿大餐，用得不够多又不值回票价',
        'ai_solution': 'AI 灵活计费',
        'ai_description': 'AI 分析用户实际用量推荐最优套餐；按需付费避免浪费；高频用户自动升级优惠',
        'ai_keywords': ['用量分析', '按需付费', '自动优惠'],
    },
    'AI安全顾虑': {
        'user_voice': '担心聊天内容被拿去训练，敏感的事情都不敢问 AI',
        'ai_solution': 'AI 隐私保障',
        'ai_description': 'AI 对话数据本地加密存储；敏感内容自动识别不入训练集；提供隐私模式一键开启',
        'ai_keywords': ['本地加密', '训练隔离', '隐私模式'],
    },
    'AI使用限制': {
        'user_voice': '免费额度一下就用完了，想多问几个问题就要付费',
        'ai_solution': 'AI 智能配额',
        'ai_description': 'AI 优化问答效率降低单次消耗；识别简单问题用轻量模型；高价值问题才调用大模型',
        'ai_keywords': ['效率优化', '分层调度', '价值优先'],
    },
    'AI代码质量': {
        'user_voice': 'AI 写的代码看着像那么回事，跑起来一堆 bug',
        'ai_solution': 'AI 代码守护',
        'ai_description': 'AI 生成代码自动执行测试验证；结合项目上下文避免编造 API；bug 自动定位修复',
        'ai_keywords': ['测试验证', '上下文感知', '自动修复'],
    },
    'AI过度审核': {
        'user_voice': '正常问题也被判定违规，AI 变得什么都不敢回答',
        'ai_solution': 'AI 审核优化',
        'ai_description': 'AI 理解问题真实意图减少误判；审核原因透明告知；支持理由说明后重新回答',
        'ai_keywords': ['意图理解', '原因透明', '重试机制'],
    },
    'AI记忆差': {
        'user_voice': '每次对话都要重新介绍背景，聊过的事情 AI 转头就忘',
        'ai_solution': 'AI 长期记忆',
        'ai_description': '构建用户专属记忆库跨对话保留；重要偏好自动识别永久保存；历史对话可智能检索',
        'ai_keywords': ['专属记忆', '偏好保存', '历史检索'],
    },
    'AI响应慢': {
        'user_voice': '问一个问题等半天才出字，着急用的时候特别崩溃',
        'ai_solution': 'AI 响应加速',
        'ai_description': 'AI 边生成边流式输出减少首字等待；常见问题预计算结果；推理引擎智能调度提升吞吐',
        'ai_keywords': ['流式输出', '预计算', '推理优化'],
    },

    # ===== 更多场景 =====
    '协作效率': {
        'user_voice': '多人协作经常冲突，同步也老出问题',
        'ai_solution': 'AI 协作助手',
        'ai_description': 'AI 自动处理文档冲突；智能任务分配和进度追踪；自动生成会议纪要',
        'ai_keywords': ['冲突处理', '任务追踪', '纪要生成'],
    },
    '会议体验': {
        'user_voice': '会议经常听不清，网络一卡就跟不上了',
        'ai_solution': 'AI 会议增强',
        'ai_description': 'AI 实时降噪和回声消除；智能字幕和翻译；自动提取会议要点',
        'ai_keywords': ['智能降噪', '实时字幕', '要点提取'],
    },
    '学习功能': {
        'user_voice': '题目讲解不清楚，遇到问题找不到人问',
        'ai_solution': 'AI 学习助手',
        'ai_description': 'AI 个性化学习路径规划；智能答疑和错题分析；学习进度智能提醒',
        'ai_keywords': ['路径规划', '智能答疑', '进度提醒'],
    },
    '视频广告': {
        'user_voice': '看个视频前面十几秒广告，中间还插播，根本没法好好看',
        'ai_solution': 'AI 广告智选',
        'ai_description': 'AI 学习用户偏好推荐相关广告；识别低质素材提前跳过；为会员用户提供纯净观看模式',
        'ai_keywords': ['偏好推荐', '素材识别', '纯净观看'],
    },
    '广告误触': {
        'user_voice': '广告按钮跟功能键长得一样，手指稍微滑一下就点进去了',
        'ai_solution': 'AI 防误触',
        'ai_description': 'AI 识别广告与功能区域冲突设计；智能延迟判定区分误触和主动点击；学习用户操作习惯',
        'ai_keywords': ['冲突识别', '延迟判定', '习惯学习'],
    },
    '账号与付费': {
        'user_voice': '账号异常或付费出了问题，想找人工处理比登天还难',
        'ai_solution': 'AI 账户管家',
        'ai_description': 'AI 统一处理账号和付费异常；自动识别问题类型并分流；高优问题快速转人工',
        'ai_keywords': ['统一处理', '智能分流', '优先响应'],
    },
}


def fix_file(file_path: Path) -> tuple:
    """强制按 title 对齐 user_voice/ai_solution"""
    if not file_path.exists():
        return 0, []
    
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    fixed_count = 0
    unmapped = []
    
    for opp in data.get('ai_opportunities', []):
        title = opp.get('title', '').strip()
        
        if title in AUTHORITATIVE_SOLUTIONS:
            spec = AUTHORITATIVE_SOLUTIONS[title]
            opp['user_voice'] = spec['user_voice']
            opp['ai_solution'] = spec['ai_solution']
            opp['ai_description'] = spec['ai_description']
            opp['ai_keywords'] = spec['ai_keywords']
            fixed_count += 1
        else:
            unmapped.append(title)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    return fixed_count, unmapped


def main():
    base = Path('data/processed')
    total_fixed = 0
    all_unmapped = set()
    
    for cat in ['wechat', 'social', 'ai', 'more']:
        file_path = base / f'{cat}_ai_opportunities_consolidated.json'
        fixed, unmapped = fix_file(file_path)
        total_fixed += fixed
        all_unmapped.update(unmapped)
        print(f'[{cat}] 强制对齐 {fixed} 个需求')
        if unmapped:
            print(f'   未映射标题: {unmapped}')
    
    print(f'\n总计强制对齐: {total_fixed} 个需求')
    if all_unmapped:
        print(f'\n所有未映射标题（需继续补充映射表）:')
        for t in sorted(all_unmapped):
            print(f'  - {t}')


if __name__ == '__main__':
    main()
