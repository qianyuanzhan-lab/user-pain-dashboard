import React, { useState, useEffect } from 'react';
import { UserNeed, Reference, SubCategory, MentionSource } from './types';
import {
  DASHBOARD_DATA,
  CATEGORY_CONFIG,
  MORE_SUB_CATEGORIES,
  COMPLIANT_DATA_SOURCES,
  DATA_COLLECTION_PERIOD,
  getNeedsByCategory,
  getSubCategoriesWithNeeds,
} from './data/dashboardData';
import { MiningOverlay } from './components/MiningOverlay';
// import { AIChatPanel } from './components/AIChatPanel'; // 暂时隐藏对话功能

type CategoryTab = 'wechat' | 'social' | 'ai' | 'more';

// 类目挖掘状态类型
interface DigStatus {
  lastDigDate: string | null;  // 上次挖掘日期
  isDigging: boolean;
}

// 需求类型标签样式（与后端 demand_type 字段一一对应）
const TYPE_CONFIG: Record<string, { label: string; color: string }> = {
  '功能缺失': { label: '功能缺失', color: 'bg-blue-50 text-blue-700' },
  '体验问题': { label: '体验问题', color: 'bg-amber-50 text-amber-700' },
  '平台策略': { label: '平台策略', color: 'bg-purple-50 text-purple-700' },
  // 兼容旧数据
  feature: { label: '功能缺失', color: 'bg-blue-50 text-blue-700' },
  optimization: { label: '体验问题', color: 'bg-amber-50 text-amber-700' },
  new_product: { label: '平台策略', color: 'bg-purple-50 text-purple-700' },
};

// 优先级标签样式
const PRIORITY_CONFIG: Record<string, { label: string; color: string }> = {
  P0: { label: 'P0', color: 'bg-red-100 text-red-700 border border-red-200' },
  P1: { label: 'P1', color: 'bg-orange-50 text-orange-600' },
  P2: { label: 'P2', color: 'bg-gray-100 text-gray-500' },
  P3: { label: 'P3', color: 'bg-gray-50 text-gray-400' },
};

// AI 方案信息类型
interface AISolutionInfo {
  title: string;
  userVoice: string;
  userSummary: string;
  aiSolution: string;
  aiKeywords: string[];
  aiDescription: string;
}

/**
 * 把 LLM 生成的 need_statement 改成"用户建议"开头的客观表达。
 * 规则：识别"XX 应该/需要/希望/能够/可以/建议" 等模式，把句首主语+情态词
 *       替换为统一的"用户建议"，从而让每条要点读起来像外部第三方总结。
 * 例：
 *   "AI 应该支持多轮记忆" → "用户建议 支持多轮记忆"
 *   "希望 Soul 能按地区筛选" → "用户建议 Soul 按地区筛选"
 *   "微信群聊应该支持折叠" → "用户建议 微信群聊 支持折叠"
 *   "应该支持暗色模式" → "用户建议 支持暗色模式"
 *   "抖音的推荐算法不准" → "用户建议：抖音的推荐算法不准"（无明显模式时加冒号）
 */
function normalizeRelevanceNote(raw: string): string {
  if (!raw) return '';
  let s = raw.trim();
  let matched = false;

  // 模式 1: 句首"用户/作者/我 + 希望/建议/觉得..."
  const pat1 = /^(?:用户|作者|我|我们|评论者)?\s*(?:希望|建议|觉得|认为|反馈|反映|要求|表示|期望|期待|呼吁)(?:，|：|:|,)?\s*/;
  if (pat1.test(s)) {
    s = s.replace(pat1, '');
    matched = true;
  }

  // 模式 2: 无主语情态词开头（"应该 X"、"需要 X"）
  const pat2 = /^(?:应该|需要|能够|应当|得)\s*/;
  if (!matched && pat2.test(s)) {
    s = s.replace(pat2, '');
    matched = true;
  }

  // 模式 3: "主语 + 应该/需要/能/可以" 形式
  const pat3 = /^([A-Za-z\u4e00-\u9fa5][A-Za-z\u4e00-\u9fa5\s]{0,12}?)\s*(?:应该|需要|能够?|可以|应当|得)\s*/;
  if (!matched && pat3.test(s)) {
    s = s.replace(pat3, (_m, subj) => {
      const cleaned = subj.trim();
      // 宽泛主语（用户/平台/系统/产品/AI 等）丢掉
      const GENERIC_SUBJECTS = ['用户', '作者', '我', '我们', '评论者', '平台', '系统', '产品', '应用', 'App', 'app', 'AI', 'ai'];
      if (GENERIC_SUBJECTS.includes(cleaned)) return '';
      // 具体产品名保留
      return cleaned + ' ';
    });
    matched = true;
  }

  // 清理多余空格和标点
  s = s.replace(/\s+/g, ' ').trim();
  s = s.replace(/^[，,。：:、\s]+/, '');

  // 加"用户建议"前缀
  return matched ? `用户建议 ${s}` : `用户建议：${s || raw}`;
}

// Reference 集合页组件
function ReferencePanel({ 
  references,
  mentionCount,
  mentionSources,
  aiInfo,
  onClose 
}: { 
  references: Reference[];
  mentionCount: number;
  mentionSources: MentionSource[];
  aiInfo?: AISolutionInfo;
  onClose: () => void;
}) {
  // 从 source 中解析来源平台和 App 名称
  // 格式如 "App Store - 微信" → { platform: "App Store", app: "微信" }
  // Hacker News 格式如 "Hacker News - 文章标题" → { platform: "Hacker News", app: "文章标题" }
  const parseSource = (source: string) => {
    const parts = source.split(' - ');
    if (parts.length >= 2) {
      const platform = parts[0];
      const app = parts.slice(1).join(' - '); // 处理标题中可能有 - 的情况
      return { platform, app };
    }
    return { platform: source, app: '' };
  };
  
  // 格式化来源显示
  const formatSourceLabel = (source: string) => {
    const { platform, app } = parseSource(source);
    
    // Hacker News 特殊处理：只显示「来自 Hacker News」
    if (platform === 'Hacker News') {
      return '来自 Hacker News';
    }
    
    if (app) {
      return `来自 ${platform}`;
    }
    return `来自 ${platform}`;
  };
  
  // 获取产品/话题标签（用于显示在来源前面）
  const getProductLabel = (source: string) => {
    const { platform, app } = parseSource(source);
    
    // Hacker News：显示文章标题作为话题，过滤掉 [dead]
    if (platform === 'Hacker News') {
      if (app && app !== '[dead]') {
        return app;
      }
      return null; // [dead] 或空标题不显示
    }
    
    // 其他来源：显示 app 名称
    return app || null;
  };
  
  // 渲染星级
  const renderStars = (rating: number = 0) => {
    return (
      <span className="inline-flex items-center gap-0.5">
        {[1, 2, 3, 4, 5].map(star => (
          <svg 
            key={star} 
            className={`w-3 h-3 ${star <= rating ? 'text-yellow-400' : 'text-gray-200'}`} 
            fill="currentColor" 
            viewBox="0 0 20 20"
          >
            <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
          </svg>
        ))}
      </span>
    );
  };
  
  return (
    <div className="fixed inset-0 bg-black/40 z-50 flex items-center justify-center p-4" onClick={onClose}>
      <div 
        className="bg-white rounded-xl shadow-2xl max-w-2xl w-full max-h-[85vh] overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        {/* 头部 */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100">
          <div>
            <h3 className="text-lg font-semibold text-gray-900">{aiInfo?.title || '需求详情'}</h3>
          </div>
          <button 
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors p-1"
          >
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        
        {/* 样本标题 */}
        <div className="px-6 pt-4 pb-2">
          <div className="flex items-center justify-between">
            <h4 className="text-sm font-medium text-gray-700">典型用户反馈</h4>
            <p className="text-xs text-gray-400">
              约 {mentionCount.toLocaleString()} 条提及 · 展示 {Math.min(5, references.length)} 条
            </p>
          </div>
        </div>
        
        {/* 信源列表 - 完整评论 */}
        <div className="px-6 pb-4 overflow-y-auto max-h-[40vh]">
          <div className="space-y-4">
            {references.slice(0, 5).map((ref, idx) => (
              <div
                key={ref.id}
                className="rounded-lg border border-gray-100 bg-gray-50/50 overflow-hidden"
              >
                {/* 要点 - 整条高亮条横跨全宽，与原评论明确分隔 */}
                {ref.relevance_note && (
                  <div className="px-4 py-2.5 bg-blue-50/60 border-b border-blue-100">
                    <p className="text-xs text-gray-700 leading-relaxed">
                      <span className="font-medium text-blue-700 mr-1.5">要点</span>
                      {normalizeRelevanceNote(ref.relevance_note)}
                    </p>
                  </div>
                )}

                {/* 评论主体 */}
                <div className="p-4">

                {/* 评论头部：评论对象 + 来源 */}
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2 flex-wrap">
                    {/* 优先显示产品名，其次从 source 解析 */}
                    {(ref.product || getProductLabel(ref.source)) && (
                      <span className="text-xs font-medium text-gray-700 bg-gray-100 px-2 py-0.5 rounded max-w-[200px] truncate">
                        {ref.product || getProductLabel(ref.source)}
                      </span>
                    )}
                    <span className="text-xs text-gray-500">
                      {formatSourceLabel(ref.source)}
                    </span>
                  </div>
                  <span className="text-xs text-gray-400">#{idx + 1}</span>
                </div>
                
                {/* 用户信息行：作者 + 时间 + 评分 */}
                <div className="flex items-center gap-3 mb-2 text-xs text-gray-500">
                  {ref.author && (
                    <span className="flex items-center gap-1">
                      <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                      </svg>
                      {ref.author}
                    </span>
                  )}
                  {ref.date && (
                    <span className="text-gray-400">{ref.date}</span>
                  )}
                  {ref.rating && renderStars(ref.rating)}
                </div>
                
                {/* 评论内容 - Hacker News 显示翻译或清理后的原文 */}
                {ref.source.includes('Hacker News') ? (
                  ref.translation ? (
                    <>
                      <blockquote className="text-sm text-gray-700 leading-relaxed whitespace-pre-wrap mb-2">
                        {ref.translation}
                      </blockquote>
                      <details className="mb-2">
                        <summary className="text-xs text-gray-400 cursor-pointer hover:text-gray-500">
                          查看英文原文
                        </summary>
                        <blockquote className="mt-1 text-xs text-gray-500 leading-relaxed whitespace-pre-wrap pl-3 border-l-2 border-gray-200">
                          {ref.snippet}
                        </blockquote>
                      </details>
                    </>
                  ) : (
                    <>
                      <p className="text-xs text-gray-400 mb-1">英文原文：</p>
                      <blockquote className="text-sm text-gray-600 leading-relaxed whitespace-pre-wrap mb-2">
                        {ref.snippet
                          .replace(/&#x27;/g, "'")
                          .replace(/&gt;/g, ">")
                          .replace(/&lt;/g, "<")
                          .replace(/&#x2F;/g, "/")
                          .replace(/&amp;/g, "&")
                        }
                      </blockquote>
                    </>
                  )
                ) : (
                  <blockquote className="text-sm text-gray-700 leading-relaxed whitespace-pre-wrap mb-2">
                    {ref.snippet}
                  </blockquote>
                )}
                
                {/* 跳转链接 */}
                {ref.url && (
                  <div className="flex items-center gap-2 flex-wrap">
                    <a 
                      href={ref.url} 
                      target="_blank" 
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-1 text-xs text-blue-500 hover:text-blue-600 hover:underline"
                      onClick={(e) => e.stopPropagation()}
                    >
                      <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                      </svg>
                      查看原文
                    </a>
                    {ref.source === 'App Store' && (
                      <span className="text-xs text-gray-400">
                        (App Store 不支持单条评论跳转，将打开评论列表页)
                      </span>
                    )}
                  </div>
                )}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* 数据范围说明 - 简化 */}
        <div className="px-6 py-2 bg-gray-50 border-t border-gray-100">
          <p className="text-xs text-gray-400">
            数据范围：{DATA_COLLECTION_PERIOD.startDate} 至 {DATA_COLLECTION_PERIOD.endDate}
          </p>
        </div>
      </div>
    </div>
  );
}

// 需求卡片组件
function NeedCard({ 
  need, 
  index,
  onViewReferences,
}: { 
  need: UserNeed; 
  index: number;
  onViewReferences: (refs: Reference[], mentionCount: number, mentionSources: MentionSource[], aiInfo?: AISolutionInfo) => void;
}) {
  const [isExpanded, setIsExpanded] = useState(false);
  // 直接使用后端 demand_type（功能缺失/体验问题/平台策略），回退到 sentiment 旧映射
  const typeKey = (need as any).demandType
    || (need.sentiment === 'negative' ? 'feature'
      : need.sentiment === 'mixed' ? 'optimization'
      : 'new_product');
  const typeConfig = TYPE_CONFIG[typeKey] || TYPE_CONFIG.feature;
  const priorityConfig = need.priority ? PRIORITY_CONFIG[need.priority] : null;

  return (
    <article className="bg-white rounded-xl border border-gray-100 shadow-sm hover:shadow-md transition-shadow">
      {/* 卡片主体 */}
      <div
        className="p-5 cursor-pointer"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="flex items-start gap-4">
          {/* 序号 */}
          <span className="text-sm text-gray-300 font-medium w-6 pt-0.5 text-right">
            {String(index + 1).padStart(2, '0')}
          </span>

          {/* 内容 */}
          <div className="flex-1 min-w-0">
            {/* 标签行 */}
            <div className="flex items-center gap-2 mb-2 flex-wrap">
              <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${typeConfig.color}`}>
                {typeConfig.label}
              </span>
              {need.subcategory && (
                <span className="text-xs text-gray-400">
                  {need.subcategory}
                </span>
              )}
              {/* 本周新增标识（7 天内发现的新需求） */}
              {(need as any).isNew && (
                <span
                  className="inline-flex items-center gap-0.5 px-1.5 py-0.5 rounded bg-red-50 text-red-600 text-[10px] font-semibold"
                  title={`发现于 ${(need as any).discoveredAt || '近期'}`}
                >
                  <span className="w-1 h-1 rounded-full bg-red-500"></span>
                  本周新增
                </span>
              )}
              {/* 跨产品通用需求标识 */}
              {(need as any).isCrossProduct && (
                <span
                  className="inline-flex items-center px-1.5 py-0.5 rounded bg-emerald-50 text-emerald-700 text-[10px] font-medium"
                  title="该需求在多个产品上都有反馈，具备跨产品通用性"
                >
                  跨产品通用
                </span>
              )}
              {need.apps.slice(0, 4).map(app => (
                <span
                  key={app}
                  className="inline-flex items-center px-1.5 py-0.5 rounded bg-gray-50 text-gray-500 text-xs"
                  title={app}
                >
                  {app}
                </span>
              ))}
              {need.apps.length > 4 && (
                <span
                  className="text-xs text-gray-400"
                  title={need.apps.slice(4).join('、')}
                >
                  +{need.apps.length - 4}
                </span>
              )}
            </div>

            {/* 标题 + 提及数 */}
            <div className="flex items-center gap-2 mb-1.5">
              <h3 className="text-base font-medium text-gray-900">
                {need.title}
              </h3>
              <span className="text-xs text-gray-400">
                {need.mentionCount.toLocaleString()} 人提及
              </span>
            </div>

            {/* 描述 - 解释标题（自洽、扎根证据） */}
            <p className="text-sm text-gray-600 leading-relaxed">
              {need.description || need.userVoice}
            </p>

            {/* 关键词 + 查看典型样本 */}
            <div className="flex flex-wrap items-center gap-x-2 gap-y-1 mt-3">
              {need.keywords
                .filter(kw => kw !== typeConfig.label && kw !== need.subcategory)
                .slice(0, 4)
                .map((kw) => (
                <span key={kw} className="text-xs text-gray-400">
                  #{kw}
                </span>
              ))}
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  const aiInfo: AISolutionInfo = {
                    title: need.title,
                    userVoice: need.userVoice || '',
                    userSummary: need.description || '',
                    aiSolution: need.aiSolution || '',
                    aiKeywords: need.aiKeywords || [],
                    aiDescription: need.aiDescription || ''
                  };
                  onViewReferences(need.references, need.mentionCount, need.mentionSources, aiInfo);
                }}
                className="inline-flex items-center gap-1 text-xs text-blue-500 hover:text-blue-600 transition-colors"
              >
                <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
                </svg>
                查看典型样本
              </button>
            </div>
          </div>

          {/* 展开提示 */}
          <span className="text-xs text-gray-400 hover:text-gray-500 flex-shrink-0 whitespace-nowrap">
            {isExpanded ? '收起' : 'AI 方向 ↓'}
          </span>
        </div>
      </div>

      {/* 展开详情 */}
      {isExpanded && (
        <div className="px-5 pb-5 border-t border-gray-100">
          {/* ml-10 = 序号宽度 w-6 (1.5rem) + gap-4 (1rem) = 2.5rem = 10 */}
          <div className="pt-4 ml-10">
            
            {/* 展开时仅在卡片主体没有显示用户原声时，才补充显示一条样本片段 */}
            {!need.userVoice && need.references.length > 0 && (
              <p className="text-sm text-gray-500 mb-3">
                "{need.references[0]?.snippet}"
              </p>
            )}

            {/* AI 介入方案 - 带模块标题 */}
            {need.aiDescription && (
              <div className="bg-blue-50/40 border border-blue-100 rounded-lg px-4 py-3">
                <div className="flex items-center gap-1.5 mb-1.5">
                  <svg className="w-3.5 h-3.5 text-blue-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                  </svg>
                  <span className="text-xs font-medium text-blue-700">AI 价值方向</span>
                </div>
                <p className="text-sm text-gray-700 leading-relaxed">{need.aiDescription}</p>
              </div>
            )}
          </div>

          {/* AI 对话面板 - 暂时隐藏 */}
          {/* {showChat && (
            <div className="mt-4">
              <AIChatPanel 
                need={need} 
                onClose={() => setShowChat(false)} 
              />
            </div>
          )} */}
        </div>
      )}
    </article>
  );
}

function App() {
  const [currentCategory, setCurrentCategory] = useState<CategoryTab>('wechat');
  const [selectedSubCategory, setSelectedSubCategory] = useState<string | null>(null);
  const [activeReferences, setActiveReferences] = useState<{ refs: Reference[]; mentionCount: number; mentionSources: MentionSource[]; aiInfo?: AISolutionInfo } | null>(null);
  const [displayCount, setDisplayCount] = useState(5);
  const [showNoUpdateToast, setShowNoUpdateToast] = useState(false);

  // === 搜索 / 排序 / 筛选 ===
  type SortMode = 'score' | 'recent' | 'mentions';
  const [sortMode, setSortMode] = useState<SortMode>('score');
  const [searchKeyword, setSearchKeyword] = useState('');
  const [sourceFilters, setSourceFilters] = useState<Set<string>>(new Set()); // 空=全选
  const [typeFilters, setTypeFilters] = useState<Set<string>>(new Set());     // 空=全选
  const [onlyCrossProduct, setOnlyCrossProduct] = useState(false);
  
  // 页面级挖掘状态
  const [showMiningOverlay, setShowMiningOverlay] = useState(true);
  const [miningDate, setMiningDate] = useState<string | null>(null);
  const [miningError, setMiningError] = useState<string | null>(null);
  
  // 挖掘状态管理（每个类目独立）
  const [digStatus, setDigStatus] = useState<Record<CategoryTab, DigStatus>>({
    wechat: { lastDigDate: null, isDigging: false },
    social: { lastDigDate: null, isDigging: false },
    ai: { lastDigDate: null, isDigging: false },
    more: { lastDigDate: null, isDigging: false },
  });
  const [showDigAnimation, setShowDigAnimation] = useState(false);

  // 挖掘完成回调
  const handleMiningComplete = () => {
    const today = new Date().toLocaleDateString('zh-CN', { month: 'numeric', day: 'numeric' });
    setMiningDate(today);
    setShowMiningOverlay(false);
    // 更新所有类目的挖掘状态
    setDigStatus({
      wechat: { lastDigDate: today, isDigging: false },
      social: { lastDigDate: today, isDigging: false },
      ai: { lastDigDate: today, isDigging: false },
      more: { lastDigDate: today, isDigging: false },
    });
  };

  // 挖掘错误回调
  const handleMiningError = (error: string) => {
    setMiningError(error);
    // 出错也关闭 overlay，使用本地数据
    setTimeout(() => setShowMiningOverlay(false), 2000);
  };

  const needs = getNeedsByCategory(currentCategory);
  const subCategoriesWithNeeds = getSubCategoriesWithNeeds(currentCategory);

  // 子分类过滤（仅 more 赛道）
  let filteredNeeds = currentCategory === 'more' && selectedSubCategory
    ? needs.filter(n => n.subcategory === selectedSubCategory)
    : needs;

  // 搜索（模糊匹配：标题/描述/产品名/关键词）
  if (searchKeyword.trim()) {
    const kw = searchKeyword.trim().toLowerCase();
    filteredNeeds = filteredNeeds.filter(n => {
      const hay = [
        n.title,
        n.description,
        n.userVoice,
        n.aiDescription,
        ...(n.apps || []),
        ...(n.keywords || []),
        ...(n.aiKeywords || []),
      ].join(' ').toLowerCase();
      return hay.includes(kw);
    });
  }

  // 数据源筛选
  if (sourceFilters.size > 0) {
    filteredNeeds = filteredNeeds.filter(n => {
      const srcBreakdown = (n as any).sourceBreakdown || {};
      return Array.from(sourceFilters).some(s => (srcBreakdown[s] || 0) > 0);
    });
  }

  // 需求类型筛选
  if (typeFilters.size > 0) {
    filteredNeeds = filteredNeeds.filter(n => typeFilters.has((n as any).demandType || ''));
  }

  // 跨产品通用筛选
  if (onlyCrossProduct) {
    filteredNeeds = filteredNeeds.filter(n => (n as any).isCrossProduct);
  }

  // 排序
  if (sortMode === 'recent') {
    filteredNeeds = [...filteredNeeds].sort((a, b) => {
      const ad = Math.max(0, ...(a.references || []).map(r => new Date(r.date).getTime() || 0));
      const bd = Math.max(0, ...(b.references || []).map(r => new Date(r.date).getTime() || 0));
      return bd - ad;
    });
  } else if (sortMode === 'mentions') {
    filteredNeeds = [...filteredNeeds].sort((a, b) => (b.mentionCount || 0) - (a.mentionCount || 0));
  }
  // sortMode==='score' 保持后端默认顺序（已按综合分排序）

  // 按当前显示数量截取
  const displayNeeds = filteredNeeds.slice(0, displayCount);
  const hasMoreNeeds = displayCount < filteredNeeds.length;

  // 加载更多（每次+5条）
  const handleLoadMore = () => {
    setDisplayCount(prev => Math.min(prev + 5, filteredNeeds.length));
  };

  // 切换分类时重置状态
  const handleCategoryChange = (cat: CategoryTab) => {
    setCurrentCategory(cat);
    setSelectedSubCategory(null);
    setDisplayCount(5);
  };

  // 切换子分类时重置显示数量
  const handleSubCategoryChange = (subCat: string | null) => {
    setSelectedSubCategory(subCat);
    setDisplayCount(5);
  };

  // 获取当前分类配置
  const categoryConfig = CATEGORY_CONFIG[currentCategory];

  return (
    <div className="min-h-screen bg-gray-50">
      {/* 页面级挖掘动效 */}
      {showMiningOverlay && (
        <MiningOverlay
          onComplete={handleMiningComplete}
          onError={handleMiningError}
        />
      )}
      
      {/* 顶部区域 */}
      <header className="bg-white border-b border-gray-100">
        <div className="max-w-4xl mx-auto px-6 py-8">
          <div className="flex items-center gap-3 mb-2">
            <h1 className="text-2xl font-semibold text-gray-900">
              需求挖掘机
            </h1>
            {miningDate && (
              <span className="inline-flex items-center gap-1.5 px-2.5 py-1 bg-emerald-50 text-emerald-700 text-xs font-medium rounded-full">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>
                {miningDate} 已挖掘
              </span>
            )}
          </div>
          <p className="text-gray-500">
            来听听用户的声音，看看他们在期待什么
          </p>
        </div>
      </header>

      {/* 分类导航 */}
      <nav className="bg-white border-b border-gray-100 sticky top-0 z-10">
        <div className="max-w-4xl mx-auto px-6">
          <div className="flex gap-1">
            {(Object.keys(CATEGORY_CONFIG) as CategoryTab[]).map((cat) => (
              <button
                key={cat}
                onClick={() => handleCategoryChange(cat)}
                className={`px-4 py-3.5 text-sm font-medium transition-colors relative ${
                  currentCategory === cat
                    ? 'text-gray-900'
                    : 'text-gray-400 hover:text-gray-600'
                }`}
              >
                {CATEGORY_CONFIG[cat].shortLabel}
                {currentCategory === cat && (
                  <span className="absolute bottom-0 left-4 right-4 h-0.5 bg-gray-900 rounded-full" />
                )}
              </button>
            ))}
          </div>
        </div>
      </nav>

      {/* 主内容区 */}
      <main className="max-w-4xl mx-auto px-6 py-8">
        {/* 分类标题与说明 */}
        <section className="mb-8">
          <h2 className="text-lg font-medium text-gray-900 mb-2">
            {categoryConfig.label}
          </h2>
          <p className="text-sm text-gray-500 mb-3">
            {categoryConfig.desc}
          </p>
          <p className="text-xs text-gray-400">
            排序规则：功能缺失/明确问题 &gt; 具体能力改进 &gt; 泛化体验优化，同类按AI介入评分和提及数排序
          </p>
        </section>

        {/* 子分类导航（仅"更多领域"显示） */}
        {currentCategory === 'more' && subCategoriesWithNeeds.length > 0 && (
          <section className="mb-6">
            <div className="flex flex-wrap gap-2">
              <button
                onClick={() => handleSubCategoryChange(null)}
                className={`px-3 py-1.5 rounded-full text-sm transition-colors ${
                  selectedSubCategory === null
                    ? 'bg-gray-900 text-white'
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                }`}
              >
                全部
              </button>
              {subCategoriesWithNeeds.map(({ subCategory }) => (
                <button
                  key={subCategory.id}
                  onClick={() => handleSubCategoryChange(subCategory.id)}
                  className={`px-3 py-1.5 rounded-full text-sm transition-colors ${
                    selectedSubCategory === subCategory.id
                      ? 'bg-gray-900 text-white'
                      : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                  }`}
                >
                  {subCategory.label}
                </button>
              ))}
            </div>
          </section>
        )}

        {/* 工具栏：搜索 + 排序 + 筛选 */}
        <section className="mb-6 bg-white rounded-xl border border-gray-100 p-4 space-y-3">
          {/* 搜索框 */}
          <div className="relative">
            <svg
              className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-4.35-4.35M17 10a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
            <input
              type="text"
              value={searchKeyword}
              onChange={e => { setSearchKeyword(e.target.value); setDisplayCount(5); }}
              placeholder="搜索需求（标题、描述、产品名、关键词）"
              className="w-full pl-9 pr-9 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-100 focus:border-blue-400"
            />
            {searchKeyword && (
              <button
                onClick={() => setSearchKeyword('')}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                title="清空搜索"
              >
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            )}
          </div>

          <div className="flex flex-wrap items-center gap-x-6 gap-y-2">
            {/* 排序 */}
            <div className="flex items-center gap-1.5">
              <span className="text-xs text-gray-500">排序：</span>
              {([
                { k: 'score', label: '综合分' },
                { k: 'recent', label: '最新提及' },
                { k: 'mentions', label: '提及数' },
              ] as { k: SortMode; label: string }[]).map(opt => (
                <button
                  key={opt.k}
                  onClick={() => { setSortMode(opt.k); setDisplayCount(5); }}
                  className={`px-2 py-0.5 text-xs rounded ${
                    sortMode === opt.k
                      ? 'bg-blue-50 text-blue-700 font-medium'
                      : 'text-gray-500 hover:bg-gray-50'
                  }`}
                >
                  {opt.label}
                </button>
              ))}
            </div>

            {/* 数据源筛选 */}
            <div className="flex items-center gap-1.5">
              <span className="text-xs text-gray-500">来源：</span>
              {([
                { k: 'appstore', label: 'App Store' },
                { k: 'googleplay', label: 'Google Play' },
                { k: 'hackernews', label: 'Hacker News' },
              ]).map(opt => {
                const on = sourceFilters.has(opt.k);
                return (
                  <button
                    key={opt.k}
                    onClick={() => {
                      const next = new Set(sourceFilters);
                      on ? next.delete(opt.k) : next.add(opt.k);
                      setSourceFilters(next);
                      setDisplayCount(5);
                    }}
                    className={`px-2 py-0.5 text-xs rounded ${
                      on ? 'bg-blue-50 text-blue-700 font-medium' : 'text-gray-500 hover:bg-gray-50 border border-gray-200'
                    }`}
                  >
                    {opt.label}
                  </button>
                );
              })}
            </div>

            {/* 类型筛选 */}
            <div className="flex items-center gap-1.5">
              <span className="text-xs text-gray-500">类型：</span>
              {(['功能缺失', '体验问题', '平台策略']).map(t => {
                const on = typeFilters.has(t);
                return (
                  <button
                    key={t}
                    onClick={() => {
                      const next = new Set(typeFilters);
                      on ? next.delete(t) : next.add(t);
                      setTypeFilters(next);
                      setDisplayCount(5);
                    }}
                    className={`px-2 py-0.5 text-xs rounded ${
                      on ? 'bg-blue-50 text-blue-700 font-medium' : 'text-gray-500 hover:bg-gray-50 border border-gray-200'
                    }`}
                  >
                    {t}
                  </button>
                );
              })}
            </div>

            {/* 跨产品筛选 */}
            <label className="flex items-center gap-1.5 text-xs text-gray-500 cursor-pointer">
              <input
                type="checkbox"
                checked={onlyCrossProduct}
                onChange={e => { setOnlyCrossProduct(e.target.checked); setDisplayCount(5); }}
                className="w-3.5 h-3.5 accent-emerald-600"
              />
              只看跨产品通用
            </label>

            {/* 结果数 */}
            <div className="ml-auto text-xs text-gray-400">
              找到 <span className="font-medium text-gray-700">{filteredNeeds.length}</span> 个需求
            </div>
          </div>
        </section>

        {/* 需求列表 */}
        <section className="mb-12">
          <div className="space-y-4">
            {displayNeeds.map((need, index) => (
                <NeedCard
                  key={need.id}
                  need={need}
                  index={index}
                  onViewReferences={(refs, mentionCount, mentionSources, aiInfo) => setActiveReferences({ refs, mentionCount, mentionSources, aiInfo })}
                />
              ))}
          </div>

          {/* 加载更多按钮 - 放在最后一条下方 */}
          {hasMoreNeeds && (
            <div className="mt-6 text-center">
              <button
                onClick={handleLoadMore}
                className="inline-flex items-center gap-2 px-5 py-2.5 text-sm font-medium text-gray-600 bg-white border border-gray-200 rounded-lg hover:bg-gray-50 hover:border-gray-300 transition-colors"
              >
                发现更多用户需求
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19 9l-7 7-7-7" />
                </svg>
              </button>
            </div>
          )}

          {/* 已全部加载提示 */}
          {!hasMoreNeeds && filteredNeeds.length > 5 && (
            <div className="mt-6 text-center">
              <p className="text-sm text-gray-400">暂时没有更多新机会了，过段时间再来看看吧</p>
            </div>
          )}

          {displayNeeds.length === 0 && (
            <div className="text-center py-12 text-gray-400">
              暂无数据
            </div>
          )}
        </section>

        {/* 数据来源说明（放最后） */}
        <section className="border-t border-gray-200 pt-8">
          <h2 className="text-xs text-gray-400 mb-4 uppercase tracking-wider">
            数据来源与合规说明
          </h2>
          
          {/* 合规数据源 */}
          <div className="mb-4">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {COMPLIANT_DATA_SOURCES.map((source) => (
                <a
                  key={source.id}
                  href={source.docUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="p-3 rounded-lg border border-gray-100 hover:border-gray-200 hover:bg-gray-50 transition-colors group"
                >
                  <div className="flex items-center gap-2 mb-1">
                    <span className="w-2 h-2 rounded-full bg-green-400"></span>
                    <span className="text-sm font-medium text-gray-700 group-hover:text-blue-600">
                      {source.name}
                    </span>
                  </div>
                  <p className="text-xs text-gray-400">
                    {source.description}
                  </p>
                </a>
              ))}
            </div>
          </div>

          {/* 采集说明（精简） */}
          <p className="text-xs text-gray-400">
            采集时间：{DATA_COLLECTION_PERIOD.startDate} 至 {DATA_COLLECTION_PERIOD.endDate} · 最后更新：{DASHBOARD_DATA.lastUpdated}
          </p>
        </section>
      </main>

      {/* 无更新提示弹窗 */}
      {showNoUpdateToast && (
        <div className="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 z-50">
          <div className="bg-amber-800/90 text-white px-6 py-4 rounded-xl shadow-lg animate-fade-in">
            <div className="flex items-center gap-3">
              <svg className="w-5 h-5 text-amber-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M5 13l4 4L19 7" />
              </svg>
              <span className="text-sm">挖掘完成，数据已更新</span>
            </div>
          </div>
        </div>
      )}

      {/* Reference 弹窗 */}
      {activeReferences && (
        <ReferencePanel
          references={activeReferences.refs}
          mentionCount={activeReferences.mentionCount}
          mentionSources={activeReferences.mentionSources}
          aiInfo={activeReferences.aiInfo}
          onClose={() => setActiveReferences(null)}
        />
      )}
    </div>
  );
}

export default App;
