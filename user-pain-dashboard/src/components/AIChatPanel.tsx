import React, { useState, useRef, useEffect } from 'react';
import { UserNeed } from '../types';

// 消息类型
interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

// 预设的灵感引导问题
const INSPIRATION_PROMPTS = [
  '这个需求的商业价值有多大？',
  '有哪些现成的技术方案可以参考？',
  '竞品是怎么解决这个问题的？',
  '这个需求背后的深层动机是什么？',
  '如果做 MVP，最小可行方案是什么？',
];

interface AIChatPanelProps {
  need: UserNeed;
  onClose?: () => void;
}

export function AIChatPanel({ need, onClose }: AIChatPanelProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  // 自动滚动到底部
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // 自动调整输入框高度
  const adjustTextareaHeight = () => {
    const textarea = inputRef.current;
    if (textarea) {
      textarea.style.height = 'auto';
      textarea.style.height = Math.min(textarea.scrollHeight, 120) + 'px';
    }
  };

  // 生成 AI 回复（模拟）
  const generateAIResponse = async (userMessage: string): Promise<string> => {
    // 模拟网络延迟
    await new Promise(resolve => setTimeout(resolve, 800 + Math.random() * 800));
    
    // 基于上下文生成回复
    const context = {
      title: need.title,
      description: need.description,
      userVoice: need.userVoice,
      aiSolution: need.aiSolution,
      aiDescription: need.aiDescription,
      keywords: need.keywords,
      mentionCount: need.mentionCount,
    };

    // 根据问题类型生成不同回复
    if (userMessage.includes('商业价值') || userMessage.includes('市场')) {
      return `关于「${context.title}」的商业价值分析：

这个需求有 ${context.mentionCount} 人提及，说明存在真实的市场需求。

从商业角度看，几个关键点：
1. **用户基数**：涉及的产品用户量大，潜在付费意愿强
2. **痛点明确**：用户表达清晰，说明问题确实影响体验
3. **技术可行**：${context.aiSolution || 'AI 技术'}已相对成熟，实现门槛不高

建议的商业模式：
- 独立工具：面向 C 端用户的订阅制产品
- B 端方案：为企业提供 API 或 SDK
- 插件形式：作为现有平台的增值服务`;
    }

    if (userMessage.includes('技术方案') || userMessage.includes('实现')) {
      return `针对「${context.title}」的技术方案建议：

核心技术栈：
1. **AI 模型**：可考虑使用 GPT-4、Claude 或国产大模型（如 Kimi、DeepSeek）
2. **关键能力**：${(context.keywords || []).slice(0, 3).join('、')}

实现路径：
- **快速验证**：调用现有 AI API，3-5 天出 Demo
- **产品化**：Fine-tune 专属模型，提升垂直场景效果
- **规模化**：自建模型或混合方案，控制成本

参考开源项目：
- LangChain / LlamaIndex（AI 应用框架）
- Dify / FastGPT（低代码 AI 平台）`;
    }

    if (userMessage.includes('竞品') || userMessage.includes('竞争')) {
      return `「${context.title}」相关竞品分析：

目前市场上的解决方案主要有三类：

1. **大厂产品**
   - 微信/支付宝内置功能（覆盖面广但通用）
   - 各 App 自带的 AI 助手（深度不够）

2. **独立工具**
   - 专注单一场景的 AI 工具
   - 特点：功能聚焦，但获客成本高

3. **开源/社区方案**
   - GitHub 上有相关项目，但产品化程度低

竞争机会：
- 现有方案多是「大而全」，缺少「小而美」的垂直解决方案
- 用户原声「${context.userVoice?.slice(0, 30) || context.description.slice(0, 30)}...」说明现有产品未能满足`;
    }

    if (userMessage.includes('MVP') || userMessage.includes('最小')) {
      return `「${context.title}」的 MVP 方案建议：

**核心功能**（必须有）：
- ${context.aiSolution || '智能处理'}的基础能力
- 简单直观的用户界面

**MVP 范围**（2 周可完成）：
1. 单一入口，解决最核心的痛点
2. 调用现有 AI API，不自建模型
3. 简单的结果展示，无需复杂交互

**验证指标**：
- 用户完成率 > 60%
- NPS > 30
- 付费意愿调研

**技术选型**：
- 前端：React/Vue + TailwindCSS
- 后端：Node.js/Python + 现有 AI API
- 部署：Vercel/Railway 快速上线`;
    }

    if (userMessage.includes('动机') || userMessage.includes('本质') || userMessage.includes('为什么')) {
      return `深入分析「${context.title}」背后的用户动机：

**表层需求**：
${context.description}

**深层动机**（Jobs to be Done）：
用户真正想要的不是功能本身，而是：
1. **效率提升**：节省时间，减少重复劳动
2. **体验优化**：减少挫败感，获得掌控感
3. **情感满足**：被尊重、被理解的感觉

**用户原声揭示的痛点**：
「${context.userVoice || context.description}」

这说明用户在意的是：
- 产品是否真正理解他们的场景
- 解决方案是否足够简单直接
- 是否感受到产品团队的用心`;
    }

    // 通用回复
    return `关于「${context.title}」，这是一个很好的思考方向。

基于现有数据：
- ${context.mentionCount} 人提及这个需求
- 用户痛点：${context.userVoice || context.description}
- AI 方案方向：${context.aiSolution || '待探索'}

你可以从以下几个角度继续探索：
1. 这个需求的商业价值有多大？
2. 技术上有哪些现成方案？
3. 竞品是怎么解决的？
4. MVP 可以怎么做？

有什么具体想深入了解的吗？`;
  };

  // 发送消息
  const handleSend = async () => {
    const text = inputValue.trim();
    if (!text || isLoading) return;

    // 添加用户消息
    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: text,
      timestamp: new Date(),
    };
    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setIsLoading(true);

    // 重置输入框高度
    if (inputRef.current) {
      inputRef.current.style.height = 'auto';
    }

    try {
      // 生成 AI 回复
      const response = await generateAIResponse(text);
      const assistantMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: response,
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      console.error('AI response error:', error);
    } finally {
      setIsLoading(false);
    }
  };

  // 快捷问题点击
  const handleQuickPrompt = (prompt: string) => {
    setInputValue(prompt);
    inputRef.current?.focus();
  };

  // 键盘事件
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="border-t border-gray-100 bg-gradient-to-b from-gray-50/50 to-white">
      {/* 标题栏 */}
      <div className="px-4 py-3 flex items-center justify-between border-b border-gray-100">
        <div className="flex items-center gap-2">
          <div className="w-6 h-6 rounded-lg bg-gradient-to-br from-violet-500 to-purple-600 flex items-center justify-center">
            <svg className="w-3.5 h-3.5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
            </svg>
          </div>
          <span className="text-sm font-medium text-gray-700">AI 对话</span>
          <span className="text-xs text-gray-400">基于此需求展开讨论</span>
        </div>
        {onClose && (
          <button
            onClick={onClose}
            className="p-1 text-gray-400 hover:text-gray-600 rounded"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        )}
      </div>

      {/* 对话区域 */}
      <div className="h-64 overflow-y-auto px-4 py-3 space-y-3">
        {messages.length === 0 ? (
          // 空状态：显示引导问题
          <div className="h-full flex flex-col items-center justify-center text-center">
            <p className="text-sm text-gray-500 mb-4">
              选择一个话题开始，或输入你的问题
            </p>
            <div className="flex flex-wrap gap-2 justify-center max-w-md">
              {INSPIRATION_PROMPTS.map((prompt, idx) => (
                <button
                  key={idx}
                  onClick={() => handleQuickPrompt(prompt)}
                  className="text-xs px-3 py-1.5 bg-white border border-gray-200 rounded-full text-gray-600 hover:border-violet-300 hover:text-violet-600 hover:bg-violet-50 transition-colors"
                >
                  {prompt}
                </button>
              ))}
            </div>
          </div>
        ) : (
          // 消息列表
          <>
            {messages.map((msg) => (
              <div
                key={msg.id}
                className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-[85%] rounded-2xl px-4 py-2.5 ${
                    msg.role === 'user'
                      ? 'bg-violet-600 text-white'
                      : 'bg-white border border-gray-100 text-gray-700'
                  }`}
                >
                  <div className="text-sm whitespace-pre-wrap leading-relaxed">
                    {msg.content}
                  </div>
                </div>
              </div>
            ))}
            {isLoading && (
              <div className="flex justify-start">
                <div className="bg-white border border-gray-100 rounded-2xl px-4 py-2.5">
                  <div className="flex items-center gap-1">
                    <span className="w-2 h-2 bg-violet-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                    <span className="w-2 h-2 bg-violet-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                    <span className="w-2 h-2 bg-violet-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </>
        )}
      </div>

      {/* 快捷问题（有消息时显示在底部） */}
      {messages.length > 0 && (
        <div className="px-4 py-2 border-t border-gray-100 bg-gray-50/50">
          <div className="flex gap-2 overflow-x-auto pb-1 scrollbar-hide">
            {INSPIRATION_PROMPTS.slice(0, 3).map((prompt, idx) => (
              <button
                key={idx}
                onClick={() => handleQuickPrompt(prompt)}
                className="text-xs px-2.5 py-1 bg-white border border-gray-200 rounded-full text-gray-500 hover:border-violet-300 hover:text-violet-600 whitespace-nowrap flex-shrink-0 transition-colors"
              >
                {prompt}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* 输入区域 */}
      <div className="px-4 py-3 border-t border-gray-100">
        <div className="flex items-end gap-2">
          <div className="flex-1 relative">
            <textarea
              ref={inputRef}
              value={inputValue}
              onChange={(e) => {
                setInputValue(e.target.value);
                adjustTextareaHeight();
              }}
              onKeyDown={handleKeyDown}
              placeholder="输入你的问题，或选择上方话题..."
              className="w-full px-4 py-2.5 pr-12 bg-gray-100 border-0 rounded-2xl text-sm text-gray-700 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-violet-500/20 focus:bg-white resize-none overflow-hidden"
              rows={1}
              style={{ minHeight: '42px', maxHeight: '120px' }}
            />
          </div>
          <button
            onClick={handleSend}
            disabled={!inputValue.trim() || isLoading}
            className={`p-2.5 rounded-xl transition-all ${
              inputValue.trim() && !isLoading
                ? 'bg-violet-600 text-white hover:bg-violet-700'
                : 'bg-gray-200 text-gray-400 cursor-not-allowed'
            }`}
          >
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
            </svg>
          </button>
        </div>
        <p className="text-xs text-gray-400 mt-2 text-center">
          Shift+Enter 换行，Enter 发送
        </p>
      </div>
    </div>
  );
}
