#!/usr/bin/env python3
"""
从原始数据中提取更多需求点，每个类目扩展到 30+ 个
基于真实用户评论的痛点分析
"""
import json
import os
import re
from collections import defaultdict, Counter
from datetime import datetime

# 痛点分类配置
PAIN_CATEGORIES = {
    # 微信类目痛点模板
    'wechat': [
        # 性能稳定性
        {'id': 'wechat_perf_001', 'title': '相机拍照卡顿', 'pain_type': 'lag', 'keywords': ['拍照', '卡', '相机'], 'priority': 'P0'},
        {'id': 'wechat_perf_002', 'title': '视频通话黑屏', 'pain_type': 'crash', 'keywords': ['视频', '黑屏', '通话'], 'priority': 'P0'},
        {'id': 'wechat_perf_003', 'title': '小程序加载慢', 'pain_type': 'lag', 'keywords': ['小程序', '慢', '加载'], 'priority': 'P1'},
        {'id': 'wechat_perf_004', 'title': '朋友圈视频卡顿', 'pain_type': 'lag', 'keywords': ['朋友圈', '视频', '卡'], 'priority': 'P1'},
        {'id': 'wechat_perf_005', 'title': '语音消息发送失败', 'pain_type': 'crash', 'keywords': ['语音', '发送', '失败'], 'priority': 'P1'},
        
        # 消息通知
        {'id': 'wechat_notif_001', 'title': '消息延迟收取', 'pain_type': 'notification', 'keywords': ['消息', '延迟', '收不到'], 'priority': 'P0'},
        {'id': 'wechat_notif_002', 'title': '公众号消息被折叠', 'pain_type': 'notification', 'keywords': ['公众号', '折叠', '消息'], 'priority': 'P1'},
        {'id': 'wechat_notif_003', 'title': '群消息通知混乱', 'pain_type': 'notification', 'keywords': ['群', '通知', '消息'], 'priority': 'P2'},
        {'id': 'wechat_notif_004', 'title': '服务号重要信息遗漏', 'pain_type': 'notification', 'keywords': ['服务号', '银行', '通知'], 'priority': 'P1'},
        
        # 客服与账号
        {'id': 'wechat_support_001', 'title': '人工客服无法联系', 'pain_type': 'support', 'keywords': ['客服', '人工', '机器人'], 'priority': 'P0'},
        {'id': 'wechat_support_002', 'title': '账号被误封申诉难', 'pain_type': 'ban', 'keywords': ['封号', '申诉', '解封'], 'priority': 'P0'},
        {'id': 'wechat_support_003', 'title': '实名认证流程繁琐', 'pain_type': 'account', 'keywords': ['实名', '认证', '绑定'], 'priority': 'P2'},
        {'id': 'wechat_support_004', 'title': '问题反馈无回应', 'pain_type': 'support', 'keywords': ['反馈', '回复', '投诉'], 'priority': 'P1'},
        
        # 语音与文字
        {'id': 'wechat_voice_001', 'title': '语音转文字不准确', 'pain_type': 'voice', 'keywords': ['语音', '转文字', '繁体'], 'priority': 'P1'},
        {'id': 'wechat_voice_002', 'title': '长语音难以收听', 'pain_type': 'voice', 'keywords': ['语音', '60秒', '长'], 'priority': 'P2'},
        {'id': 'wechat_voice_003', 'title': '语音消息无法快进', 'pain_type': 'voice', 'keywords': ['语音', '快进', '倍速'], 'priority': 'P2'},
        
        # 存储管理
        {'id': 'wechat_storage_001', 'title': '存储空间占用过大', 'pain_type': 'storage', 'keywords': ['内存', '存储', '占用', 'G'], 'priority': 'P1'},
        {'id': 'wechat_storage_002', 'title': '文件过期无法打开', 'pain_type': 'storage', 'keywords': ['文件', '过期', '打开'], 'priority': 'P1'},
        {'id': 'wechat_storage_003', 'title': '聊天记录清理困难', 'pain_type': 'storage', 'keywords': ['清理', '记录', '删除'], 'priority': 'P2'},
        
        # 朋友圈与社交
        {'id': 'wechat_social_001', 'title': '朋友圈无法编辑', 'pain_type': 'ui', 'keywords': ['朋友圈', '编辑', '修改'], 'priority': 'P2'},
        {'id': 'wechat_social_002', 'title': '朋友圈搜索功能弱', 'pain_type': 'search', 'keywords': ['朋友圈', '搜索', '找'], 'priority': 'P2'},
        {'id': 'wechat_social_003', 'title': '群聊管理功能不足', 'pain_type': 'ui', 'keywords': ['群', '管理', '踢人'], 'priority': 'P2'},
        
        # 隐私安全
        {'id': 'wechat_privacy_001', 'title': '隐私设置不够细化', 'pain_type': 'privacy', 'keywords': ['隐私', '设置', '可见'], 'priority': 'P2'},
        {'id': 'wechat_privacy_002', 'title': '诈骗信息防护不足', 'pain_type': 'scam', 'keywords': ['诈骗', '骗子', '举报'], 'priority': 'P1'},
        
        # 支付与小程序
        {'id': 'wechat_pay_001', 'title': '小程序支付卡死', 'pain_type': 'crash', 'keywords': ['小程序', '支付', '卡'], 'priority': 'P0'},
        {'id': 'wechat_pay_002', 'title': '广告弹窗频繁', 'pain_type': 'ads', 'keywords': ['广告', '弹窗', '误触'], 'priority': 'P1'},
        
        # 输入与界面
        {'id': 'wechat_ui_001', 'title': '输入法切换不便', 'pain_type': 'ui', 'keywords': ['输入法', '切换', '键盘'], 'priority': 'P3'},
        {'id': 'wechat_ui_002', 'title': '界面字体太小', 'pain_type': 'ui', 'keywords': ['字体', '太小', '看不清'], 'priority': 'P2'},
        {'id': 'wechat_ui_003', 'title': '深色模式体验差', 'pain_type': 'ui', 'keywords': ['深色', '夜间', '模式'], 'priority': 'P3'},
        {'id': 'wechat_ui_004', 'title': '消息已读状态缺失', 'pain_type': 'ui', 'keywords': ['已读', '状态', '回复'], 'priority': 'P3'},
    ],
    
    # 社交类目痛点模板
    'social': [
        # 账号安全与封禁
        {'id': 'social_ban_001', 'title': '无故封号无解释', 'pain_type': 'ban', 'keywords': ['封号', '封禁', '无故'], 'priority': 'P0'},
        {'id': 'social_ban_002', 'title': '申诉渠道形同虚设', 'pain_type': 'ban', 'keywords': ['申诉', '解封', '审核'], 'priority': 'P0'},
        {'id': 'social_ban_003', 'title': '禁言规则不透明', 'pain_type': 'ban', 'keywords': ['禁言', '违规', '规则'], 'priority': 'P1'},
        {'id': 'social_ban_004', 'title': '设备封禁无法使用', 'pain_type': 'ban', 'keywords': ['设备', '封禁', '换手机'], 'priority': 'P1'},
        
        # 广告骚扰
        {'id': 'social_ads_001', 'title': '开屏广告无法跳过', 'pain_type': 'ads', 'keywords': ['开屏', '广告', '跳过'], 'priority': 'P0'},
        {'id': 'social_ads_002', 'title': '信息流广告太多', 'pain_type': 'ads', 'keywords': ['广告', '推送', '刷'], 'priority': 'P1'},
        {'id': 'social_ads_003', 'title': '广告误触跳转', 'pain_type': 'ads', 'keywords': ['误触', '跳转', '广告'], 'priority': 'P1'},
        {'id': 'social_ads_004', 'title': '视频中插广告', 'pain_type': 'ads', 'keywords': ['视频', '中插', '广告'], 'priority': 'P2'},
        
        # 收费与会员
        {'id': 'social_pay_001', 'title': '会员权益缩水', 'pain_type': 'payment', 'keywords': ['会员', '权益', '缩水'], 'priority': 'P0'},
        {'id': 'social_pay_002', 'title': '自动续费难取消', 'pain_type': 'payment', 'keywords': ['自动续费', '取消', '扣费'], 'priority': 'P0'},
        {'id': 'social_pay_003', 'title': '诱导付费陷阱多', 'pain_type': 'payment', 'keywords': ['付费', '诱导', '充值'], 'priority': 'P1'},
        {'id': 'social_pay_004', 'title': '退款流程复杂', 'pain_type': 'payment', 'keywords': ['退款', '退费', '客服'], 'priority': 'P1'},
        {'id': 'social_pay_005', 'title': '功能过度收费', 'pain_type': 'payment', 'keywords': ['收费', 'VIP', '功能'], 'priority': 'P2'},
        
        # 诈骗与安全
        {'id': 'social_scam_001', 'title': '酒托婚托泛滥', 'pain_type': 'scam', 'keywords': ['酒托', '婚托', '托'], 'priority': 'P0'},
        {'id': 'social_scam_002', 'title': '杀猪盘骗局多', 'pain_type': 'scam', 'keywords': ['杀猪盘', '诈骗', '骗'], 'priority': 'P0'},
        {'id': 'social_scam_003', 'title': '虚假账号识别难', 'pain_type': 'scam', 'keywords': ['假', '虚假', '账号'], 'priority': 'P1'},
        {'id': 'social_scam_004', 'title': '举报处理不及时', 'pain_type': 'scam', 'keywords': ['举报', '处理', '骗子'], 'priority': 'P1'},
        
        # 客服体验
        {'id': 'social_support_001', 'title': '人工客服找不到', 'pain_type': 'support', 'keywords': ['客服', '人工', '联系'], 'priority': 'P0'},
        {'id': 'social_support_002', 'title': '反馈无人处理', 'pain_type': 'support', 'keywords': ['反馈', '处理', '回复'], 'priority': 'P1'},
        {'id': 'social_support_003', 'title': '投诉渠道不畅', 'pain_type': 'support', 'keywords': ['投诉', '渠道', '电话'], 'priority': 'P1'},
        
        # 推荐算法
        {'id': 'social_algo_001', 'title': '推荐内容重复', 'pain_type': 'recommend', 'keywords': ['推荐', '重复', '刷'], 'priority': 'P1'},
        {'id': 'social_algo_002', 'title': '推荐内容低俗', 'pain_type': 'recommend', 'keywords': ['推荐', '低俗', '擦边'], 'priority': 'P1'},
        {'id': 'social_algo_003', 'title': '兴趣标签不准', 'pain_type': 'recommend', 'keywords': ['标签', '兴趣', '不准'], 'priority': 'P2'},
        {'id': 'social_algo_004', 'title': '信息茧房严重', 'pain_type': 'recommend', 'keywords': ['茧房', '推荐', '同质'], 'priority': 'P2'},
        
        # 匹配与社交
        {'id': 'social_match_001', 'title': '匹配机器人账号多', 'pain_type': 'scam', 'keywords': ['机器人', '匹配', '假'], 'priority': 'P1'},
        {'id': 'social_match_002', 'title': '匹配算法不精准', 'pain_type': 'recommend', 'keywords': ['匹配', '不准', '算法'], 'priority': 'P2'},
        {'id': 'social_match_003', 'title': '同城匹配范围窄', 'pain_type': 'search', 'keywords': ['同城', '附近', '匹配'], 'priority': 'P3'},
        
        # 内容审核
        {'id': 'social_review_001', 'title': '审核标准不一致', 'pain_type': 'review', 'keywords': ['审核', '标准', '违规'], 'priority': 'P1'},
        {'id': 'social_review_002', 'title': '正常内容被误删', 'pain_type': 'review', 'keywords': ['删除', '误判', '内容'], 'priority': 'P1'},
        {'id': 'social_review_003', 'title': '违规内容举报无效', 'pain_type': 'review', 'keywords': ['举报', '违规', '处理'], 'priority': 'P2'},
        
        # 性能问题
        {'id': 'social_perf_001', 'title': '应用频繁闪退', 'pain_type': 'crash', 'keywords': ['闪退', '崩溃', '打不开'], 'priority': 'P0'},
        {'id': 'social_perf_002', 'title': '页面加载卡顿', 'pain_type': 'lag', 'keywords': ['卡', '慢', '加载'], 'priority': 'P1'},
        {'id': 'social_perf_003', 'title': '视频播放不流畅', 'pain_type': 'lag', 'keywords': ['视频', '卡顿', '播放'], 'priority': 'P2'},
        
        # 隐私保护
        {'id': 'social_privacy_001', 'title': '个人信息泄露风险', 'pain_type': 'privacy', 'keywords': ['隐私', '泄露', '信息'], 'priority': 'P1'},
        {'id': 'social_privacy_002', 'title': '位置权限滥用', 'pain_type': 'privacy', 'keywords': ['位置', '定位', '权限'], 'priority': 'P2'},
    ],
    
    # AI 应用类目痛点模板
    'ai': [
        # 使用限制
        {'id': 'ai_quota_001', 'title': '对话次数限制严格', 'pain_type': 'quota', 'keywords': ['次数', '限制', '上限'], 'priority': 'P0'},
        {'id': 'ai_quota_002', 'title': '付费后仍有限制', 'pain_type': 'quota', 'keywords': ['会员', '限制', '付费'], 'priority': 'P0'},
        {'id': 'ai_quota_003', 'title': '高峰期无法使用', 'pain_type': 'quota', 'keywords': ['高峰', '繁忙', '等待'], 'priority': 'P0'},
        {'id': 'ai_quota_004', 'title': '配额恢复时间长', 'pain_type': 'quota', 'keywords': ['恢复', '小时', '等'], 'priority': 'P1'},
        
        # 回答质量
        {'id': 'ai_quality_001', 'title': '回答内容不准确', 'pain_type': 'ai_quality', 'keywords': ['错', '不准', '错误'], 'priority': 'P0'},
        {'id': 'ai_quality_002', 'title': '编造虚假信息', 'pain_type': 'ai_quality', 'keywords': ['编', '瞎编', '胡说'], 'priority': 'P0'},
        {'id': 'ai_quality_003', 'title': '回答前后矛盾', 'pain_type': 'ai_quality', 'keywords': ['矛盾', '前后', '不一致'], 'priority': 'P1'},
        {'id': 'ai_quality_004', 'title': '无法承认错误', 'pain_type': 'ai_quality', 'keywords': ['承认', '错误', '狡辩'], 'priority': 'P1'},
        {'id': 'ai_quality_005', 'title': '回答过于敷衍', 'pain_type': 'ai_quality', 'keywords': ['敷衍', '简单', '不详细'], 'priority': 'P2'},
        {'id': 'ai_quality_006', 'title': '专业问题回答浅', 'pain_type': 'ai_quality', 'keywords': ['专业', '深度', '浅'], 'priority': 'P2'},
        
        # 联网与时效
        {'id': 'ai_connect_001', 'title': '信息过时不准确', 'pain_type': 'connectivity', 'keywords': ['过时', '实时', '最新'], 'priority': 'P1'},
        {'id': 'ai_connect_002', 'title': '无法获取实时信息', 'pain_type': 'connectivity', 'keywords': ['联网', '搜索', '实时'], 'priority': 'P1'},
        {'id': 'ai_connect_003', 'title': '网页解析能力弱', 'pain_type': 'connectivity', 'keywords': ['网页', '链接', '解析'], 'priority': 'P2'},
        
        # 收费问题
        {'id': 'ai_pay_001', 'title': '订阅价格过高', 'pain_type': 'payment', 'keywords': ['价格', '贵', '订阅'], 'priority': 'P1'},
        {'id': 'ai_pay_002', 'title': '付费后体验无提升', 'pain_type': 'payment', 'keywords': ['付费', '没用', '一样'], 'priority': 'P1'},
        {'id': 'ai_pay_003', 'title': '自动续费不提醒', 'pain_type': 'payment', 'keywords': ['续费', '扣款', '自动'], 'priority': 'P1'},
        {'id': 'ai_pay_004', 'title': '退款申请被拒', 'pain_type': 'payment', 'keywords': ['退款', '退费', '拒绝'], 'priority': 'P2'},
        
        # 功能限制
        {'id': 'ai_func_001', 'title': '长文本处理中断', 'pain_type': 'crash', 'keywords': ['太长', '中断', '截断'], 'priority': 'P1'},
        {'id': 'ai_func_002', 'title': '图片识别能力弱', 'pain_type': 'ai_quality', 'keywords': ['图片', '识别', '看图'], 'priority': 'P2'},
        {'id': 'ai_func_003', 'title': '代码执行不支持', 'pain_type': 'ai_quality', 'keywords': ['代码', '执行', '运行'], 'priority': 'P2'},
        {'id': 'ai_func_004', 'title': '文件上传限制多', 'pain_type': 'storage', 'keywords': ['文件', '上传', '限制'], 'priority': 'P2'},
        
        # 性能问题
        {'id': 'ai_perf_001', 'title': '回复速度太慢', 'pain_type': 'lag', 'keywords': ['慢', '等', '速度'], 'priority': 'P1'},
        {'id': 'ai_perf_002', 'title': '应用频繁闪退', 'pain_type': 'crash', 'keywords': ['闪退', '崩溃', '卡'], 'priority': 'P1'},
        {'id': 'ai_perf_003', 'title': '对话历史丢失', 'pain_type': 'crash', 'keywords': ['丢失', '历史', '记录'], 'priority': 'P1'},
        
        # 语音交互
        {'id': 'ai_voice_001', 'title': '语音识别不准', 'pain_type': 'voice', 'keywords': ['语音', '识别', '听'], 'priority': 'P2'},
        {'id': 'ai_voice_002', 'title': '语音播报卡顿', 'pain_type': 'voice', 'keywords': ['播报', '朗读', '卡'], 'priority': 'P2'},
        {'id': 'ai_voice_003', 'title': '语音对话中断', 'pain_type': 'voice', 'keywords': ['语音', '中断', '断开'], 'priority': 'P2'},
        
        # 广告与推广
        {'id': 'ai_ads_001', 'title': '回答夹带广告', 'pain_type': 'ads', 'keywords': ['广告', '推广', '带货'], 'priority': 'P1'},
        {'id': 'ai_ads_002', 'title': '强推付费升级', 'pain_type': 'ads', 'keywords': ['升级', '付费', '会员'], 'priority': 'P2'},
        
        # 客服支持
        {'id': 'ai_support_001', 'title': '客服无法联系', 'pain_type': 'support', 'keywords': ['客服', '联系', '反馈'], 'priority': 'P1'},
        {'id': 'ai_support_002', 'title': '问题反馈无回应', 'pain_type': 'support', 'keywords': ['反馈', '回复', '处理'], 'priority': 'P2'},
        
        # 隐私问题
        {'id': 'ai_privacy_001', 'title': '对话内容隐私担忧', 'pain_type': 'privacy', 'keywords': ['隐私', '对话', '数据'], 'priority': 'P2'},
    ],
    
    # 更多场景类目痛点模板
    'more': [
        # 性能稳定性
        {'id': 'more_perf_001', 'title': '应用卡顿严重', 'pain_type': 'lag', 'keywords': ['卡', '慢', '卡顿'], 'priority': 'P0'},
        {'id': 'more_perf_002', 'title': '频繁闪退崩溃', 'pain_type': 'crash', 'keywords': ['闪退', '崩溃', '打不开'], 'priority': 'P0'},
        {'id': 'more_perf_003', 'title': '视频会议掉线', 'pain_type': 'crash', 'keywords': ['掉线', '断开', '会议'], 'priority': 'P0'},
        {'id': 'more_perf_004', 'title': '屏幕共享失败', 'pain_type': 'crash', 'keywords': ['共享', '屏幕', '失败'], 'priority': 'P1'},
        
        # 收费问题
        {'id': 'more_pay_001', 'title': '基础功能收费', 'pain_type': 'payment', 'keywords': ['收费', '付费', '功能'], 'priority': 'P0'},
        {'id': 'more_pay_002', 'title': '会员价格过高', 'pain_type': 'payment', 'keywords': ['会员', '价格', '贵'], 'priority': 'P1'},
        {'id': 'more_pay_003', 'title': '多层会员体系混乱', 'pain_type': 'payment', 'keywords': ['会员', 'VIP', '套餐'], 'priority': 'P2'},
        {'id': 'more_pay_004', 'title': '自动续费陷阱', 'pain_type': 'payment', 'keywords': ['续费', '自动', '取消'], 'priority': 'P1'},
        
        # 客服问题
        {'id': 'more_support_001', 'title': '客服响应慢', 'pain_type': 'support', 'keywords': ['客服', '回复', '等'], 'priority': 'P1'},
        {'id': 'more_support_002', 'title': '问题解决不了', 'pain_type': 'support', 'keywords': ['客服', '解决', '处理'], 'priority': 'P1'},
        {'id': 'more_support_003', 'title': '反馈渠道不畅', 'pain_type': 'support', 'keywords': ['反馈', '联系', '投诉'], 'priority': 'P2'},
        
        # 账号问题
        {'id': 'more_account_001', 'title': '登录验证繁琐', 'pain_type': 'login', 'keywords': ['登录', '验证', '认证'], 'priority': 'P1'},
        {'id': 'more_account_002', 'title': '账号被误封', 'pain_type': 'ban', 'keywords': ['封号', '封禁', '限制'], 'priority': 'P0'},
        {'id': 'more_account_003', 'title': '多设备登录限制', 'pain_type': 'login', 'keywords': ['设备', '登录', '限制'], 'priority': 'P2'},
        {'id': 'more_account_004', 'title': '注销账号困难', 'pain_type': 'account', 'keywords': ['注销', '删除', '账号'], 'priority': 'P2'},
        
        # 通知问题
        {'id': 'more_notif_001', 'title': '消息通知延迟', 'pain_type': 'notification', 'keywords': ['通知', '延迟', '消息'], 'priority': 'P0'},
        {'id': 'more_notif_002', 'title': '来电提醒失效', 'pain_type': 'notification', 'keywords': ['来电', '提醒', '通话'], 'priority': 'P0'},
        {'id': 'more_notif_003', 'title': '打卡提醒不准', 'pain_type': 'notification', 'keywords': ['打卡', '提醒', '通知'], 'priority': 'P1'},
        
        # 广告问题
        {'id': 'more_ads_001', 'title': '广告弹窗频繁', 'pain_type': 'ads', 'keywords': ['广告', '弹窗', '推送'], 'priority': 'P1'},
        {'id': 'more_ads_002', 'title': '开屏广告太长', 'pain_type': 'ads', 'keywords': ['开屏', '广告', '跳过'], 'priority': 'P2'},
        
        # 功能体验
        {'id': 'more_func_001', 'title': '搜索功能难用', 'pain_type': 'search', 'keywords': ['搜索', '找', '查'], 'priority': 'P1'},
        {'id': 'more_func_002', 'title': '界面操作复杂', 'pain_type': 'ui', 'keywords': ['复杂', '操作', '找不到'], 'priority': 'P2'},
        {'id': 'more_func_003', 'title': '定位功能不准', 'pain_type': 'privacy', 'keywords': ['定位', '位置', '不准'], 'priority': 'P1'},
        {'id': 'more_func_004', 'title': '文件同步失败', 'pain_type': 'crash', 'keywords': ['同步', '文件', '失败'], 'priority': 'P1'},
        
        # 存储问题
        {'id': 'more_storage_001', 'title': '应用体积臃肿', 'pain_type': 'storage', 'keywords': ['内存', '占用', '大'], 'priority': 'P2'},
        {'id': 'more_storage_002', 'title': '云存储空间不足', 'pain_type': 'storage', 'keywords': ['空间', '存储', '容量'], 'priority': 'P2'},
        
        # 语音问题
        {'id': 'more_voice_001', 'title': '语音通话质量差', 'pain_type': 'voice', 'keywords': ['语音', '通话', '声音'], 'priority': 'P1'},
        {'id': 'more_voice_002', 'title': '会议录制失败', 'pain_type': 'voice', 'keywords': ['录制', '录音', '会议'], 'priority': 'P2'},
        
        # 隐私安全
        {'id': 'more_privacy_001', 'title': '权限索取过多', 'pain_type': 'privacy', 'keywords': ['权限', '隐私', '授权'], 'priority': 'P2'},
        {'id': 'more_privacy_002', 'title': '数据安全担忧', 'pain_type': 'privacy', 'keywords': ['安全', '数据', '泄露'], 'priority': 'P2'},
    ],
}

def load_raw_data(category):
    """加载原始数据"""
    filepath = f"data/raw/appstore/{category}_20260423.json"
    if not os.path.exists(filepath):
        return None
    with open(filepath) as f:
        return json.load(f)

def match_reviews_to_pain(reviews, pain_config):
    """匹配评论到痛点"""
    matched = []
    keywords = pain_config['keywords']
    
    for review in reviews:
        content = review.get('content', '')
        rating = review.get('rating', 5)
        
        # 只匹配低分评论
        if rating > 3:
            continue
            
        # 检查关键词匹配
        match_count = sum(1 for kw in keywords if kw in content)
        if match_count > 0:
            matched.append({
                'review': review,
                'match_count': match_count
            })
    
    # 按匹配度排序
    matched.sort(key=lambda x: -x['match_count'])
    return matched

def create_opportunity(pain_config, matched_reviews, category):
    """创建 AI 介入机会"""
    samples = []
    apps_mentioned = set()
    
    for item in matched_reviews[:5]:  # 最多取 5 个样本
        review = item['review']
        apps_mentioned.add(review.get('app_name', ''))
        samples.append({
            'id': f"{category}-{pain_config['id']}-sample-{len(samples)+1}",
            'app_name': review.get('app_name', ''),
            'author': review.get('author', ''),
            'content': review.get('content', ''),
            'rating': review.get('rating', 1),
            'date': review.get('date', ''),
            'source_url': review.get('url', ''),
            'relevance_note': f"匹配关键词: {', '.join(pain_config['keywords'])}"
        })
    
    return {
        'id': pain_config['id'],
        'title': pain_config['title'],
        'description': f"基于用户评论分析，针对「{pain_config['title']}」问题的 AI 介入机会",
        'ai_intervention_type': '轻量介入' if pain_config['priority'] in ['P2', 'P3'] else '重量介入',
        'user_pain_summary': f"用户反馈中频繁出现关于「{pain_config['title']}」的抱怨",
        'priority': pain_config['priority'],
        'cross_product_relevance': [],
        'source_stats': {
            'exact_match_count': len(matched_reviews),
            'products_mentioned': list(apps_mentioned)
        },
        'evidence_samples': samples
    }

def expand_category_opportunities(category):
    """扩展某个类目的需求点"""
    raw_data = load_raw_data(category)
    if not raw_data:
        print(f"  警告: {category} 无原始数据")
        return []
    
    reviews = raw_data.get('reviews', [])
    pain_configs = PAIN_CATEGORIES.get(category, [])
    
    opportunities = []
    for pain_config in pain_configs:
        matched = match_reviews_to_pain(reviews, pain_config)
        if len(matched) >= 2:  # 至少有 2 条匹配评论
            opp = create_opportunity(pain_config, matched, category)
            opportunities.append(opp)
    
    # 按优先级排序（P0 > P1 > P2 > P3）
    priority_order = {'P0': 0, 'P1': 1, 'P2': 2, 'P3': 3}
    opportunities.sort(key=lambda x: (priority_order.get(x['priority'], 9), -x['source_stats']['exact_match_count']))
    
    return opportunities

def main():
    """主函数"""
    os.chdir('/Users/doudou/WorkBuddy/20260421111045/user-pain-dashboard')
    
    category_names = {
        'wechat': '微信生态',
        'social': '社交娱乐',
        'ai': 'AI 应用',
        'more': '更多场景'
    }
    
    for category in ['wechat', 'social', 'ai', 'more']:
        print(f"\n处理类目: {category}")
        opportunities = expand_category_opportunities(category)
        print(f"  生成 {len(opportunities)} 个需求点")
        
        # 读取现有文件并更新
        filepath = f"data/processed/{category}_ai_opportunities.json"
        with open(filepath) as f:
            data = json.load(f)
        
        # 获取原始数据中的产品列表
        raw_data = load_raw_data(category)
        if raw_data:
            data['products_analyzed'] = [app['name'] for app in raw_data.get('apps_crawled', [])]
            data['total_reviews_analyzed'] = raw_data.get('total_reviews', 0)
        
        data['ai_opportunities'] = opportunities
        data['analysis_date'] = datetime.now().strftime('%Y-%m-%d')
        
        # 保存
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"  已保存到 {filepath}")
        
        # 输出统计
        priority_counts = Counter(o['priority'] for o in opportunities)
        print(f"  优先级分布: {dict(priority_counts)}")

if __name__ == '__main__':
    main()
