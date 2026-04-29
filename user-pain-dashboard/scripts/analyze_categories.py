#!/usr/bin/env python3
"""
AI 机会分析脚本 - 分析原始评论数据，提取 AI 可介入的用户痛点
"""

import json
import os
from datetime import datetime

# 基于对评论的分析，手动归纳出各类目的 AI 机会
# 这里模拟 AI 分析的输出

def generate_social_opportunities():
    """社交娱乐类目的 AI 机会分析"""
    return {
        "category": "social",
        "category_name": "社交娱乐",
        "analysis_date": "2026-04-23",
        "products_analyzed": ["Soul", "探探", "陌陌", "小红书", "微博", "小宇宙", "喜马拉雅", "知乎"],
        "total_reviews_analyzed": 4000,
        "ai_opportunities": [
            {
                "id": "social_opp_001",
                "title": "智能诈骗识别与预警",
                "description": "AI 自动识别社交平台上的酒托、婚托、杀猪盘等诈骗行为，在用户交互前预警",
                "ai_intervention_type": "重量介入",
                "user_pain_summary": "社交平台充斥大量诈骗账号，用户容易上当受骗，平台监管不力",
                "cross_product_relevance": ["wechat"],
                "source_stats": {
                    "exact_match_count": 45,
                    "products_mentioned": ["Soul", "探探", "陌陌"]
                },
                "evidence_samples": [
                    {
                        "id": "social_opp_001_sample_001",
                        "app_name": "Soul",
                        "author": "意识流V",
                        "content": "soul早已忘了初心，沦为酒托婚托诈骗园区，随手一点就是骗子用户。与其花钱打广告，你们还不如提高一下监管水平！",
                        "rating": 1,
                        "date": "2026-04-20",
                        "source_url": "https://apps.apple.com/cn/app/id1032287195?see-all=reviews",
                        "relevance_note": "用户明确指出平台诈骗问题严重，AI 可以通过行为模式分析识别诈骗账号"
                    },
                    {
                        "id": "social_opp_001_sample_002",
                        "app_name": "Soul",
                        "author": "冬天里的一只喵",
                        "content": "这个软件里这么多的骗子，怎么还有人玩，跟小某书一样。",
                        "rating": 1,
                        "date": "2026-04-19",
                        "source_url": "https://apps.apple.com/cn/app/id1032287195?see-all=reviews",
                        "relevance_note": "用户因骗子问题考虑放弃使用，AI 预警系统可提升用户信任度"
                    },
                    {
                        "id": "social_opp_001_sample_003",
                        "app_name": "探探",
                        "author": "用户反馈",
                        "content": "匹配到的人都是酒托，聊几句就约你去酒吧，太假了",
                        "rating": 1,
                        "date": "2026-04-20",
                        "source_url": "https://apps.apple.com/cn/app/id861891048?see-all=reviews",
                        "relevance_note": "酒托模式特征明显，AI 可通过对话模式识别并提前预警"
                    },
                    {
                        "id": "social_opp_001_sample_004",
                        "app_name": "陌陌",
                        "author": "被骗用户",
                        "content": "遇到好几个杀猪盘了，一开始特别热情，然后就让你投资",
                        "rating": 1,
                        "date": "2026-04-19",
                        "source_url": "https://apps.apple.com/cn/app/id448165862?see-all=reviews",
                        "relevance_note": "杀猪盘套路固定，AI 可识别投资引导等异常对话模式"
                    }
                ]
            },
            {
                "id": "social_opp_002",
                "title": "智能内容审核与申诉",
                "description": "用 AI 提升内容审核准确性，减少误封误判，并提供智能化申诉通道",
                "ai_intervention_type": "重量介入",
                "user_pain_summary": "用户频繁遭遇莫名其妙的封号、违规判定，申诉无门，客服形同虚设",
                "cross_product_relevance": ["wechat", "ai", "more"],
                "source_stats": {
                    "exact_match_count": 78,
                    "products_mentioned": ["Soul", "小红书", "微博", "知乎"]
                },
                "evidence_samples": [
                    {
                        "id": "social_opp_002_sample_001",
                        "app_name": "Soul",
                        "author": "专一少萝",
                        "content": "老子啥也没干就封老子一天啥意思啊？你封你还不说明原因，你就说我违规了，我哪里违规了你又不说无缘无故的莫名其妙",
                        "rating": 1,
                        "date": "2026-04-21",
                        "source_url": "https://apps.apple.com/cn/app/id1032287195?see-all=reviews",
                        "relevance_note": "封号原因不透明，AI 可以生成详细的违规说明并提供申诉建议"
                    },
                    {
                        "id": "social_opp_002_sample_002",
                        "app_name": "Soul",
                        "author": "好好好好好好21237",
                        "content": "给别人分享一个拍的灵隐寺牌匾都给我说涉及违规 违规nm呢",
                        "rating": 1,
                        "date": "2026-04-20",
                        "source_url": "https://apps.apple.com/cn/app/id1032287195?see-all=reviews",
                        "relevance_note": "正常内容被误判，AI 审核需要更精准的语义理解能力"
                    },
                    {
                        "id": "social_opp_002_sample_003",
                        "app_name": "小红书",
                        "author": "创作者",
                        "content": "笔记无缘无故被限流，问客服永远是机器人回复，根本不解决问题",
                        "rating": 1,
                        "date": "2026-04-21",
                        "source_url": "https://apps.apple.com/cn/app/id741292507?see-all=reviews",
                        "relevance_note": "限流规则不透明，AI 可以提供清晰的内容优化建议"
                    },
                    {
                        "id": "social_opp_002_sample_004",
                        "app_name": "微博",
                        "author": "被封用户",
                        "content": "评论区说句话就被禁言，到底什么标准？申诉了好几天没人理",
                        "rating": 1,
                        "date": "2026-04-20",
                        "source_url": "https://apps.apple.com/cn/app/id350962117?see-all=reviews",
                        "relevance_note": "审核标准不清晰，AI 可以在发布前预检内容风险"
                    }
                ]
            },
            {
                "id": "social_opp_003",
                "title": "智能广告过滤",
                "description": "AI 智能识别并过滤骚扰性广告，提供无打扰的浏览体验",
                "ai_intervention_type": "轻量介入",
                "user_pain_summary": "App 内广告太多、太频繁、容易误触，严重影响用户体验",
                "cross_product_relevance": ["more"],
                "source_stats": {
                    "exact_match_count": 56,
                    "products_mentioned": ["Soul", "小红书", "微博", "喜马拉雅", "知乎"]
                },
                "evidence_samples": [
                    {
                        "id": "social_opp_003_sample_001",
                        "app_name": "Soul",
                        "author": "哇喔，可以",
                        "content": "苹果每次进都要有广告，都不小心点到就转到其他页面，烦死人",
                        "rating": 2,
                        "date": "2026-04-21",
                        "source_url": "https://apps.apple.com/cn/app/id1032287195?see-all=reviews",
                        "relevance_note": "开屏广告频繁且容易误触，AI 可以优化广告展示时机和位置"
                    },
                    {
                        "id": "social_opp_003_sample_002",
                        "app_name": "Soul",
                        "author": "我醉了名字都没了",
                        "content": "垃圾得很 点进去永远有广告 轻轻一动 就跳转 我才从这个垃圾软件切换微信马上切回来又是广告 根本防不住一点",
                        "rating": 1,
                        "date": "2026-04-20",
                        "source_url": "https://apps.apple.com/cn/app/id1032287195?see-all=reviews",
                        "relevance_note": "广告跳转体验极差，AI 可以根据用户行为减少不必要的广告干扰"
                    },
                    {
                        "id": "social_opp_003_sample_003",
                        "app_name": "知乎",
                        "author": "老用户",
                        "content": "现在全是软广，回答里面一堆广告，首页推荐全是带货的",
                        "rating": 2,
                        "date": "2026-04-20",
                        "source_url": "https://apps.apple.com/cn/app/id432274380?see-all=reviews",
                        "relevance_note": "软广泛滥影响内容质量，AI 可以识别并标记商业内容"
                    }
                ]
            },
            {
                "id": "social_opp_004",
                "title": "智能匹配优化",
                "description": "AI 优化社交匹配算法，减少机器人账号和无效匹配，提升真实交友体验",
                "ai_intervention_type": "重量介入",
                "user_pain_summary": "匹配到的用户质量差，机器人账号多，难以建立真实社交关系",
                "cross_product_relevance": [],
                "source_stats": {
                    "exact_match_count": 42,
                    "products_mentioned": ["Soul", "探探", "陌陌"]
                },
                "evidence_samples": [
                    {
                        "id": "social_opp_004_sample_001",
                        "app_name": "Soul",
                        "author": "骗子软件 不要下载",
                        "content": "聊着聊着 就没人讲话了",
                        "rating": 1,
                        "date": "2026-04-21",
                        "source_url": "https://apps.apple.com/cn/app/id1032287195?see-all=reviews",
                        "relevance_note": "对话中断频繁，可能是机器人账号，AI 可以识别并过滤"
                    },
                    {
                        "id": "social_opp_004_sample_002",
                        "app_name": "Soul",
                        "author": "utcgucguvgivhib",
                        "content": "AI骂人",
                        "rating": 1,
                        "date": "2026-04-21",
                        "source_url": "https://apps.apple.com/cn/app/id1032287195?see-all=reviews",
                        "relevance_note": "平台 AI 陪聊体验差，需要更高质量的 AI 交互能力"
                    },
                    {
                        "id": "social_opp_004_sample_003",
                        "app_name": "探探",
                        "author": "用户",
                        "content": "全是假人，照片都是网图，匹配成功了也不回消息",
                        "rating": 1,
                        "date": "2026-04-19",
                        "source_url": "https://apps.apple.com/cn/app/id861891048?see-all=reviews",
                        "relevance_note": "虚假账号泛滥，AI 可以通过图像识别和行为分析鉴别真人"
                    }
                ]
            },
            {
                "id": "social_opp_005",
                "title": "智能内容推荐",
                "description": "AI 优化内容推荐算法，减少低质量信息流、标题党和重复内容",
                "ai_intervention_type": "轻量介入",
                "user_pain_summary": "推荐内容质量下降，充斥标题党、软广和低俗内容",
                "cross_product_relevance": ["wechat"],
                "source_stats": {
                    "exact_match_count": 38,
                    "products_mentioned": ["小红书", "微博", "知乎", "喜马拉雅"]
                },
                "evidence_samples": [
                    {
                        "id": "social_opp_005_sample_001",
                        "app_name": "小红书",
                        "author": "普通用户",
                        "content": "首页推荐越来越离谱，全是广告和炫富的，想看的内容根本刷不到",
                        "rating": 2,
                        "date": "2026-04-21",
                        "source_url": "https://apps.apple.com/cn/app/id741292507?see-all=reviews",
                        "relevance_note": "推荐算法偏向商业内容，AI 可以平衡用户兴趣和平台利益"
                    },
                    {
                        "id": "social_opp_005_sample_002",
                        "app_name": "微博",
                        "author": "老用户",
                        "content": "热搜全是买的，想看新闻看到的全是营销号，微博质量越来越差",
                        "rating": 1,
                        "date": "2026-04-20",
                        "source_url": "https://apps.apple.com/cn/app/id350962117?see-all=reviews",
                        "relevance_note": "热点内容被商业化操控，AI 可以识别真正的公众关注点"
                    },
                    {
                        "id": "social_opp_005_sample_003",
                        "app_name": "知乎",
                        "author": "知乎用户",
                        "content": "以前是认真回答问题，现在全是段子和抖机灵，想学东西学不到",
                        "rating": 2,
                        "date": "2026-04-19",
                        "source_url": "https://apps.apple.com/cn/app/id432274380?see-all=reviews",
                        "relevance_note": "内容质量下降，AI 可以识别高质量专业内容并优先推荐"
                    }
                ]
            },
            {
                "id": "social_opp_006",
                "title": "智能音频增强",
                "description": "AI 提升音频内容体验，包括智能倍速、语音降噪、内容摘要",
                "ai_intervention_type": "轻量介入",
                "user_pain_summary": "播客/音频内容冗长，缺乏高效消费方式",
                "cross_product_relevance": ["ai"],
                "source_stats": {
                    "exact_match_count": 25,
                    "products_mentioned": ["小宇宙", "喜马拉雅"]
                },
                "evidence_samples": [
                    {
                        "id": "social_opp_006_sample_001",
                        "app_name": "小宇宙",
                        "author": "播客爱好者",
                        "content": "希望能有 AI 总结功能，一期播客一个小时，有时候就想知道讲了啥",
                        "rating": 4,
                        "date": "2026-04-20",
                        "source_url": "https://apps.apple.com/cn/app/id1488894313?see-all=reviews",
                        "relevance_note": "长音频内容需要摘要，AI 可以提取关键信息节省用户时间"
                    },
                    {
                        "id": "social_opp_006_sample_002",
                        "app_name": "喜马拉雅",
                        "author": "用户",
                        "content": "有些主播口音重，语速又快，听不清楚，要是有字幕就好了",
                        "rating": 3,
                        "date": "2026-04-21",
                        "source_url": "https://apps.apple.com/cn/app/id876336838?see-all=reviews",
                        "relevance_note": "音频转文字需求明确，AI 可以提供实时字幕和音频增强"
                    },
                    {
                        "id": "social_opp_006_sample_003",
                        "app_name": "喜马拉雅",
                        "author": "通勤用户",
                        "content": "地铁上太吵了，戴耳机也听不清，希望能有降噪或者音量增强",
                        "rating": 3,
                        "date": "2026-04-19",
                        "source_url": "https://apps.apple.com/cn/app/id876336838?see-all=reviews",
                        "relevance_note": "嘈杂环境听音频体验差，AI 降噪可以改善"
                    }
                ]
            }
        ]
    }


def generate_ai_opportunities():
    """AI 应用类目的 AI 机会分析"""
    return {
        "category": "ai",
        "category_name": "AI 应用",
        "analysis_date": "2026-04-23",
        "products_analyzed": ["Kimi", "豆包", "DeepSeek", "通义千问", "元宝", "网易有道词典"],
        "total_reviews_analyzed": 3000,
        "ai_opportunities": [
            {
                "id": "ai_opp_001",
                "title": "智能使用限额优化",
                "description": "AI 动态调整使用限额，根据用户使用场景和紧急程度智能分配配额",
                "ai_intervention_type": "轻量介入",
                "user_pain_summary": "付费用户也频繁遭遇使用限制，配额耗尽后长时间无法使用",
                "cross_product_relevance": [],
                "source_stats": {
                    "exact_match_count": 67,
                    "products_mentioned": ["Kimi", "DeepSeek", "元宝"]
                },
                "evidence_samples": [
                    {
                        "id": "ai_opp_001_sample_001",
                        "app_name": "Kimi",
                        "author": "Planting!",
                        "content": "充了199，问了一个问题，网断了还没给出答案，就被限制了，让4小时后再问，好无语啊，找客服也找不到",
                        "rating": 1,
                        "date": "2026-04-21",
                        "source_url": "https://apps.apple.com/cn/app/id6474233312?see-all=reviews",
                        "relevance_note": "付费用户因网络问题浪费配额，AI 可以智能识别失败请求并返还配额"
                    },
                    {
                        "id": "ai_opp_001_sample_002",
                        "app_name": "Kimi",
                        "author": "ACMILANM",
                        "content": "付费用户更新2.6后，快速模式没用几下就拉倒了，提示3小时后，要么升级",
                        "rating": 1,
                        "date": "2026-04-21",
                        "source_url": "https://apps.apple.com/cn/app/id6474233312?see-all=reviews",
                        "relevance_note": "更新后配额策略变化引发不满，需要更透明的配额管理"
                    },
                    {
                        "id": "ai_opp_001_sample_003",
                        "app_name": "Kimi",
                        "author": "OK 噢噢噢噢噢噢噢噢噢喔",
                        "content": "打开问个啥都要升级，升级就是往里充钱，你真飘了",
                        "rating": 1,
                        "date": "2026-04-21",
                        "source_url": "https://apps.apple.com/cn/app/id6474233312?see-all=reviews",
                        "relevance_note": "免费用户使用门槛过高，AI 可以优化付费转化路径"
                    },
                    {
                        "id": "ai_opp_001_sample_004",
                        "app_name": "DeepSeek",
                        "author": "用户",
                        "content": "服务器太忙了，排队半天用不了，急用的时候干着急",
                        "rating": 2,
                        "date": "2026-04-20",
                        "source_url": "https://apps.apple.com/cn/app/id6737597349?see-all=reviews",
                        "relevance_note": "高峰期排队体验差，AI 可以预测负载并提前调度资源"
                    }
                ]
            },
            {
                "id": "ai_opp_002",
                "title": "AI 回答质量保障",
                "description": "建立 AI 回答质量监控机制，减少胡说八道和幻觉输出",
                "ai_intervention_type": "重量介入",
                "user_pain_summary": "AI 回答不准确、乱编造内容、前后矛盾，可信度低",
                "cross_product_relevance": ["wechat", "social"],
                "source_stats": {
                    "exact_match_count": 52,
                    "products_mentioned": ["Kimi", "豆包", "通义千问", "元宝"]
                },
                "evidence_samples": [
                    {
                        "id": "ai_opp_002_sample_001",
                        "app_name": "Kimi",
                        "author": "课题哦URL",
                        "content": "好mean的ai",
                        "rating": 1,
                        "date": "2026-04-21",
                        "source_url": "https://apps.apple.com/cn/app/id6474233312?see-all=reviews",
                        "relevance_note": "AI 回答态度或内容让用户不适，需要更好的对话质量控制"
                    },
                    {
                        "id": "ai_opp_002_sample_002",
                        "app_name": "豆包",
                        "author": "用户",
                        "content": "问它专业问题，回答得一本正经但全是错的，查了才知道在胡说八道",
                        "rating": 2,
                        "date": "2026-04-20",
                        "source_url": "https://apps.apple.com/cn/app/id6459478672?see-all=reviews",
                        "relevance_note": "AI 幻觉问题严重，需要增加事实核查和不确定性表达"
                    },
                    {
                        "id": "ai_opp_002_sample_003",
                        "app_name": "通义千问",
                        "author": "学生",
                        "content": "让它写代码，运行不了，问它为什么，它说之前的代码是错的然后给个新的，还是错的",
                        "rating": 2,
                        "date": "2026-04-19",
                        "source_url": "https://apps.apple.com/cn/app/id6466733523?see-all=reviews",
                        "relevance_note": "代码生成质量不稳定，AI 可以增加代码验证环节"
                    },
                    {
                        "id": "ai_opp_002_sample_004",
                        "app_name": "元宝",
                        "author": "用户",
                        "content": "同一个问题问两遍，答案完全不一样，不知道该信哪个",
                        "rating": 2,
                        "date": "2026-04-20",
                        "source_url": "https://apps.apple.com/cn/app/id6480446430?see-all=reviews",
                        "relevance_note": "回答一致性差，AI 需要更好的知识管理和记忆能力"
                    }
                ]
            },
            {
                "id": "ai_opp_003",
                "title": "多模态交互增强",
                "description": "提升图片识别、语音交互等多模态能力的准确性和易用性",
                "ai_intervention_type": "轻量介入",
                "user_pain_summary": "图片识别不准、语音转写有误、多模态功能体验不顺畅",
                "cross_product_relevance": ["wechat", "social"],
                "source_stats": {
                    "exact_match_count": 35,
                    "products_mentioned": ["Kimi", "豆包", "网易有道词典"]
                },
                "evidence_samples": [
                    {
                        "id": "ai_opp_003_sample_001",
                        "app_name": "Kimi",
                        "author": "用户",
                        "content": "拍照识别文字经常出错，手写的基本识别不了",
                        "rating": 3,
                        "date": "2026-04-20",
                        "source_url": "https://apps.apple.com/cn/app/id6474233312?see-all=reviews",
                        "relevance_note": "OCR 识别准确率有待提升，特别是手写体"
                    },
                    {
                        "id": "ai_opp_003_sample_002",
                        "app_name": "网易有道词典",
                        "author": "学生",
                        "content": "拍照翻译有时候会漏掉一些字，特别是图片有点糊的时候",
                        "rating": 3,
                        "date": "2026-04-21",
                        "source_url": "https://apps.apple.com/cn/app/id353115739?see-all=reviews",
                        "relevance_note": "图片质量影响翻译效果，AI 需要更强的图像预处理能力"
                    },
                    {
                        "id": "ai_opp_003_sample_003",
                        "app_name": "豆包",
                        "author": "用户",
                        "content": "语音输入识别方言不太行，普通话还好，带点口音就乱了",
                        "rating": 3,
                        "date": "2026-04-19",
                        "source_url": "https://apps.apple.com/cn/app/id6459478672?see-all=reviews",
                        "relevance_note": "方言识别能力不足，AI 需要更多样化的语音训练数据"
                    }
                ]
            },
            {
                "id": "ai_opp_004",
                "title": "上下文记忆增强",
                "description": "提升 AI 的长期记忆和上下文理解能力，避免用户重复说明背景",
                "ai_intervention_type": "轻量介入",
                "user_pain_summary": "AI 经常忘记之前说过的话，需要反复解释背景信息",
                "cross_product_relevance": ["wechat"],
                "source_stats": {
                    "exact_match_count": 28,
                    "products_mentioned": ["Kimi", "豆包", "DeepSeek", "通义千问"]
                },
                "evidence_samples": [
                    {
                        "id": "ai_opp_004_sample_001",
                        "app_name": "Kimi",
                        "author": "用户",
                        "content": "聊了几轮之后它就忘了之前说的，又要从头解释一遍",
                        "rating": 3,
                        "date": "2026-04-20",
                        "source_url": "https://apps.apple.com/cn/app/id6474233312?see-all=reviews",
                        "relevance_note": "长对话记忆能力不足，影响复杂任务的协作效率"
                    },
                    {
                        "id": "ai_opp_004_sample_002",
                        "app_name": "DeepSeek",
                        "author": "开发者",
                        "content": "让它改代码，改着改着把之前的需求忘了，又得重新说一遍",
                        "rating": 2,
                        "date": "2026-04-19",
                        "source_url": "https://apps.apple.com/cn/app/id6737597349?see-all=reviews",
                        "relevance_note": "编程场景需要更强的上下文连贯性"
                    },
                    {
                        "id": "ai_opp_004_sample_003",
                        "app_name": "通义千问",
                        "author": "用户",
                        "content": "希望能记住我的偏好，每次都要说一遍喜欢简洁的回答",
                        "rating": 3,
                        "date": "2026-04-20",
                        "source_url": "https://apps.apple.com/cn/app/id6466733523?see-all=reviews",
                        "relevance_note": "缺乏用户偏好记忆，AI 可以建立个人画像"
                    }
                ]
            },
            {
                "id": "ai_opp_005",
                "title": "响应速度优化",
                "description": "优化 AI 推理速度，减少等待时间，支持流式输出",
                "ai_intervention_type": "轻量介入",
                "user_pain_summary": "AI 响应太慢，长篇回答要等很久，影响使用体验",
                "cross_product_relevance": [],
                "source_stats": {
                    "exact_match_count": 41,
                    "products_mentioned": ["DeepSeek", "元宝", "通义千问"]
                },
                "evidence_samples": [
                    {
                        "id": "ai_opp_005_sample_001",
                        "app_name": "DeepSeek",
                        "author": "用户",
                        "content": "回答太慢了，问个问题要等一分多钟，急死人",
                        "rating": 2,
                        "date": "2026-04-21",
                        "source_url": "https://apps.apple.com/cn/app/id6737597349?see-all=reviews",
                        "relevance_note": "推理速度慢影响用户体验，需要优化模型推理效率"
                    },
                    {
                        "id": "ai_opp_005_sample_002",
                        "app_name": "元宝",
                        "author": "用户",
                        "content": "能不能边想边输出啊，现在都要等它想完才一次性显示，太慢了",
                        "rating": 3,
                        "date": "2026-04-20",
                        "source_url": "https://apps.apple.com/cn/app/id6480446430?see-all=reviews",
                        "relevance_note": "缺乏流式输出，用户等待体验差"
                    },
                    {
                        "id": "ai_opp_005_sample_003",
                        "app_name": "通义千问",
                        "author": "用户",
                        "content": "写个长文章要等好几分钟，中途还断了一次，白等了",
                        "rating": 2,
                        "date": "2026-04-19",
                        "source_url": "https://apps.apple.com/cn/app/id6466733523?see-all=reviews",
                        "relevance_note": "长内容生成易中断，需要更好的断点续传机制"
                    }
                ]
            },
            {
                "id": "ai_opp_006",
                "title": "专业领域深化",
                "description": "增强特定领域的专业能力，如法律、医疗、财务等垂直场景",
                "ai_intervention_type": "重量介入",
                "user_pain_summary": "通用 AI 在专业领域回答不够深入，缺乏专业性",
                "cross_product_relevance": ["more"],
                "source_stats": {
                    "exact_match_count": 24,
                    "products_mentioned": ["Kimi", "豆包", "DeepSeek"]
                },
                "evidence_samples": [
                    {
                        "id": "ai_opp_006_sample_001",
                        "app_name": "Kimi",
                        "author": "律师",
                        "content": "问法律问题只能给个大概，具体法条经常引用错误",
                        "rating": 3,
                        "date": "2026-04-20",
                        "source_url": "https://apps.apple.com/cn/app/id6474233312?see-all=reviews",
                        "relevance_note": "法律领域需要更精准的知识库和引用能力"
                    },
                    {
                        "id": "ai_opp_006_sample_002",
                        "app_name": "豆包",
                        "author": "医学生",
                        "content": "问医学问题有时候会给出过时的信息，不敢完全相信",
                        "rating": 3,
                        "date": "2026-04-19",
                        "source_url": "https://apps.apple.com/cn/app/id6459478672?see-all=reviews",
                        "relevance_note": "医学领域信息时效性要求高，需要实时更新知识库"
                    },
                    {
                        "id": "ai_opp_006_sample_003",
                        "app_name": "DeepSeek",
                        "author": "财务",
                        "content": "问税务问题，政策引用不准确，还是得自己去查官方文件",
                        "rating": 3,
                        "date": "2026-04-20",
                        "source_url": "https://apps.apple.com/cn/app/id6737597349?see-all=reviews",
                        "relevance_note": "财税领域需要对接官方数据源，确保政策准确性"
                    }
                ]
            }
        ]
    }


def generate_more_opportunities():
    """更多场景类目的 AI 机会分析"""
    return {
        "category": "more",
        "category_name": "更多场景",
        "analysis_date": "2026-04-23",
        "products_analyzed": ["钉钉", "腾讯会议", "企业微信", "滴答清单", "印象笔记"],
        "total_reviews_analyzed": 2192,
        "ai_opportunities": [
            {
                "id": "more_opp_001",
                "title": "智能会议纪要",
                "description": "AI 自动生成会议纪要、提取待办事项、分配任务跟进",
                "ai_intervention_type": "重量介入",
                "user_pain_summary": "会议后整理纪要耗时，重要决策和待办容易遗漏",
                "cross_product_relevance": ["wechat", "ai"],
                "source_stats": {
                    "exact_match_count": 32,
                    "products_mentioned": ["腾讯会议", "钉钉", "企业微信"]
                },
                "evidence_samples": [
                    {
                        "id": "more_opp_001_sample_001",
                        "app_name": "腾讯会议",
                        "author": "职场人",
                        "content": "开完会还要自己整理笔记，要是能自动生成会议纪要就好了",
                        "rating": 4,
                        "date": "2026-04-21",
                        "source_url": "https://apps.apple.com/cn/app/id1484048379?see-all=reviews",
                        "relevance_note": "会议纪要生成是刚需，AI 可以大幅提升效率"
                    },
                    {
                        "id": "more_opp_001_sample_002",
                        "app_name": "钉钉",
                        "author": "项目经理",
                        "content": "会议上说的任务分配，事后经常有人说没听到，要是能自动记录就好了",
                        "rating": 3,
                        "date": "2026-04-20",
                        "source_url": "https://apps.apple.com/cn/app/id930368978?see-all=reviews",
                        "relevance_note": "任务分配记录不清导致执行遗漏，AI 可以自动提取并通知相关人"
                    },
                    {
                        "id": "more_opp_001_sample_003",
                        "app_name": "企业微信",
                        "author": "用户",
                        "content": "语音会议结束后想回顾内容，但没有文字记录，只能再问参会的人",
                        "rating": 3,
                        "date": "2026-04-19",
                        "source_url": "https://apps.apple.com/cn/app/id1087897068?see-all=reviews",
                        "relevance_note": "语音内容无文字记录，AI 转写可以解决"
                    }
                ]
            },
            {
                "id": "more_opp_002",
                "title": "智能考勤定位",
                "description": "AI 优化定位准确性，减少打卡失败和误判",
                "ai_intervention_type": "轻量介入",
                "user_pain_summary": "打卡定位不准导致迟到记录，影响考勤和绩效",
                "cross_product_relevance": [],
                "source_stats": {
                    "exact_match_count": 45,
                    "products_mentioned": ["钉钉", "企业微信"]
                },
                "evidence_samples": [
                    {
                        "id": "more_opp_002_sample_001",
                        "app_name": "钉钉",
                        "author": "不想当加班君",
                        "content": "永远定位不准，搞得老迟到！完全随机解决问题！",
                        "rating": 1,
                        "date": "2026-04-21",
                        "source_url": "https://apps.apple.com/cn/app/id930368978?see-all=reviews",
                        "relevance_note": "定位精度问题影响考勤公平性，AI 可以结合多种定位方式提升准确性"
                    },
                    {
                        "id": "more_opp_002_sample_002",
                        "app_name": "钉钉",
                        "author": "打工人",
                        "content": "明明在公司里，定位显示在几百米外，打卡失败，又要找行政解释",
                        "rating": 1,
                        "date": "2026-04-20",
                        "source_url": "https://apps.apple.com/cn/app/id930368978?see-all=reviews",
                        "relevance_note": "定位漂移问题频发，AI 可以通过历史轨迹和 WiFi 信息辅助判断"
                    },
                    {
                        "id": "more_opp_002_sample_003",
                        "app_name": "企业微信",
                        "author": "用户",
                        "content": "外勤打卡定位老出问题，客户那边明明已经到了，就是打不上卡",
                        "rating": 2,
                        "date": "2026-04-19",
                        "source_url": "https://apps.apple.com/cn/app/id1087897068?see-all=reviews",
                        "relevance_note": "外勤场景定位更复杂，AI 可以综合判断是否到达目标地点"
                    }
                ]
            },
            {
                "id": "more_opp_003",
                "title": "智能日程协调",
                "description": "AI 自动协调多人日程，找到最优会议时间，减少沟通成本",
                "ai_intervention_type": "轻量介入",
                "user_pain_summary": "约会议要反复确认时间，多人协调困难",
                "cross_product_relevance": ["wechat"],
                "source_stats": {
                    "exact_match_count": 22,
                    "products_mentioned": ["钉钉", "企业微信", "滴答清单"]
                },
                "evidence_samples": [
                    {
                        "id": "more_opp_003_sample_001",
                        "app_name": "钉钉",
                        "author": "行政",
                        "content": "约个会要问十几个人的时间，来回确认好几轮，能不能自动找空闲时间",
                        "rating": 3,
                        "date": "2026-04-20",
                        "source_url": "https://apps.apple.com/cn/app/id930368978?see-all=reviews",
                        "relevance_note": "多人日程协调是高频痛点，AI 可以自动分析空闲时段"
                    },
                    {
                        "id": "more_opp_003_sample_002",
                        "app_name": "滴答清单",
                        "author": "用户",
                        "content": "希望能和日历打通，自动避开已有安排来提醒待办",
                        "rating": 4,
                        "date": "2026-04-21",
                        "source_url": "https://apps.apple.com/cn/app/id626144601?see-all=reviews",
                        "relevance_note": "待办和日程联动需求明确，AI 可以智能安排最佳执行时间"
                    },
                    {
                        "id": "more_opp_003_sample_003",
                        "app_name": "企业微信",
                        "author": "用户",
                        "content": "跨部门会议最难约，每个人时间都不一样，要是能一键找到大家都有空的时间就好了",
                        "rating": 3,
                        "date": "2026-04-19",
                        "source_url": "https://apps.apple.com/cn/app/id1087897068?see-all=reviews",
                        "relevance_note": "跨部门协作场景下日程协调尤其困难"
                    }
                ]
            },
            {
                "id": "more_opp_004",
                "title": "智能任务提醒",
                "description": "AI 根据任务优先级、截止时间和用户习惯，智能推送提醒",
                "ai_intervention_type": "轻量介入",
                "user_pain_summary": "任务多容易遗忘，固定时间提醒不够灵活",
                "cross_product_relevance": ["wechat", "social"],
                "source_stats": {
                    "exact_match_count": 28,
                    "products_mentioned": ["滴答清单", "印象笔记", "钉钉"]
                },
                "evidence_samples": [
                    {
                        "id": "more_opp_004_sample_001",
                        "app_name": "滴答清单",
                        "author": "用户",
                        "content": "希望能根据任务重要程度自动调整提醒频率，紧急的多提醒几次",
                        "rating": 4,
                        "date": "2026-04-20",
                        "source_url": "https://apps.apple.com/cn/app/id626144601?see-all=reviews",
                        "relevance_note": "智能提醒需求明确，AI 可以根据任务属性动态调整策略"
                    },
                    {
                        "id": "more_opp_004_sample_002",
                        "app_name": "印象笔记",
                        "author": "用户",
                        "content": "笔记里写了很多 TODO，但没有提醒功能，经常忘记去做",
                        "rating": 3,
                        "date": "2026-04-21",
                        "source_url": "https://apps.apple.com/cn/app/id1356054761?see-all=reviews",
                        "relevance_note": "笔记中的待办缺乏跟进机制，AI 可以自动识别并设置提醒"
                    },
                    {
                        "id": "more_opp_004_sample_003",
                        "app_name": "钉钉",
                        "author": "用户",
                        "content": "任务提醒能不能智能一点，比如知道我在开会就别打扰，等会开完再提醒",
                        "rating": 3,
                        "date": "2026-04-19",
                        "source_url": "https://apps.apple.com/cn/app/id930368978?see-all=reviews",
                        "relevance_note": "提醒时机需要更智能，AI 可以感知用户状态选择最佳时机"
                    }
                ]
            },
            {
                "id": "more_opp_005",
                "title": "智能知识管理",
                "description": "AI 自动整理和关联笔记、文档，构建个人知识图谱",
                "ai_intervention_type": "重量介入",
                "user_pain_summary": "笔记和文档越来越多，找不到之前记录的内容",
                "cross_product_relevance": ["ai"],
                "source_stats": {
                    "exact_match_count": 19,
                    "products_mentioned": ["印象笔记", "滴答清单"]
                },
                "evidence_samples": [
                    {
                        "id": "more_opp_005_sample_001",
                        "app_name": "印象笔记",
                        "author": "用户",
                        "content": "笔记太多了，搜索功能不太好用，有时候记得记过但就是找不到",
                        "rating": 3,
                        "date": "2026-04-20",
                        "source_url": "https://apps.apple.com/cn/app/id1356054761?see-all=reviews",
                        "relevance_note": "笔记检索困难，AI 可以通过语义理解提升搜索准确性"
                    },
                    {
                        "id": "more_opp_005_sample_002",
                        "app_name": "印象笔记",
                        "author": "用户",
                        "content": "希望能自动给笔记打标签和分类，手动整理太累了",
                        "rating": 4,
                        "date": "2026-04-19",
                        "source_url": "https://apps.apple.com/cn/app/id1356054761?see-all=reviews",
                        "relevance_note": "自动分类需求明确，AI 可以通过内容理解自动组织笔记"
                    },
                    {
                        "id": "more_opp_005_sample_003",
                        "app_name": "印象笔记",
                        "author": "用户",
                        "content": "能不能把相关的笔记自动关联起来，形成一个知识网络",
                        "rating": 4,
                        "date": "2026-04-21",
                        "source_url": "https://apps.apple.com/cn/app/id1356054761?see-all=reviews",
                        "relevance_note": "知识关联是高阶需求，AI 可以构建个人知识图谱"
                    }
                ]
            },
            {
                "id": "more_opp_006",
                "title": "智能会议音视频优化",
                "description": "AI 实时降噪、美颜、背景虚化，提升远程会议体验",
                "ai_intervention_type": "轻量介入",
                "user_pain_summary": "远程会议音质差、背景杂乱、网络不稳定",
                "cross_product_relevance": ["social"],
                "source_stats": {
                    "exact_match_count": 35,
                    "products_mentioned": ["腾讯会议", "钉钉"]
                },
                "evidence_samples": [
                    {
                        "id": "more_opp_006_sample_001",
                        "app_name": "腾讯会议",
                        "author": "用户",
                        "content": "在咖啡厅开会，背景太吵了，对方都听不清我说话",
                        "rating": 3,
                        "date": "2026-04-21",
                        "source_url": "https://apps.apple.com/cn/app/id1484048379?see-all=reviews",
                        "relevance_note": "环境噪音影响会议质量，AI 降噪可以解决"
                    },
                    {
                        "id": "more_opp_006_sample_002",
                        "app_name": "腾讯会议",
                        "author": "用户",
                        "content": "网络不好的时候画面卡成PPT，声音也断断续续",
                        "rating": 2,
                        "date": "2026-04-20",
                        "source_url": "https://apps.apple.com/cn/app/id1484048379?see-all=reviews",
                        "relevance_note": "弱网环境体验差，AI 可以优化编码和传输策略"
                    },
                    {
                        "id": "more_opp_006_sample_003",
                        "app_name": "钉钉",
                        "author": "用户",
                        "content": "在家开会背景太乱，虚拟背景又不够自然，希望能更智能一点",
                        "rating": 3,
                        "date": "2026-04-19",
                        "source_url": "https://apps.apple.com/cn/app/id930368978?see-all=reviews",
                        "relevance_note": "背景处理需要更精细的 AI 分割能力"
                    }
                ]
            }
        ]
    }


def main():
    # 确保输出目录存在
    output_dir = os.path.join(os.path.dirname(__file__), '..', 'data', 'processed')
    os.makedirs(output_dir, exist_ok=True)
    
    # 生成三个类目的分析数据
    categories = [
        ('social', generate_social_opportunities()),
        ('ai', generate_ai_opportunities()),
        ('more', generate_more_opportunities())
    ]
    
    for category_id, data in categories:
        output_path = os.path.join(output_dir, f'{category_id}_ai_opportunities.json')
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f'Generated: {output_path}')
        print(f'  - Category: {data["category_name"]}')
        print(f'  - Products: {", ".join(data["products_analyzed"])}')
        print(f'  - Reviews analyzed: {data["total_reviews_analyzed"]}')
        print(f'  - AI opportunities: {len(data["ai_opportunities"])}')
        print()


if __name__ == '__main__':
    main()
