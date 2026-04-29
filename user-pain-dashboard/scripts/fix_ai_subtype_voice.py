#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复 AI 子类型需求（AI开头的标题）共用同一套文案的问题。
这些需求都被模糊匹配误判到了 'AI 回答质量' 方案。
"""
import json
from pathlib import Path

# 针对每个 AI 子类型的独立文案
AI_SUBTYPE_SOLUTIONS = {
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
    'AI回答质量': {
        'user_voice': 'AI 经常一本正经胡说八道，专业问题的回答根本不靠谱',
        'ai_solution': 'AI 回答增强',
        'ai_description': '引入实时信息检索确保时效性；增强专业领域知识库；明确标注不确定内容避免幻觉',
        'ai_keywords': ['实时检索', '专业增强', '幻觉标注'],
    },
    'AI 回答质量': {  # 兼容带空格的版本
        'user_voice': 'AI 经常一本正经胡说八道，专业问题的回答根本不靠谱',
        'ai_solution': 'AI 回答增强',
        'ai_description': '引入实时信息检索确保时效性；增强专业领域知识库；明确标注不确定内容避免幻觉',
        'ai_keywords': ['实时检索', '专业增强', '幻觉标注'],
    },
}


def fix_file(file_path: Path) -> int:
    """修复单个文件"""
    if not file_path.exists():
        return 0
    
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    fixed_count = 0
    for opp in data.get('ai_opportunities', []):
        title = opp.get('title', '').strip()
        if title in AI_SUBTYPE_SOLUTIONS:
            spec = AI_SUBTYPE_SOLUTIONS[title]
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
    total = 0
    for cat in ['wechat', 'social', 'ai', 'more']:
        file_path = base / f'{cat}_ai_opportunities_consolidated.json'
        fixed = fix_file(file_path)
        total += fixed
        print(f'[{cat}] 修复 {fixed} 个 AI 子类型需求')
    print(f'\n总计修复: {total} 个需求')


if __name__ == '__main__':
    main()
