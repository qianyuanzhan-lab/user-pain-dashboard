// @ts-nocheck
/**
 * ============================================
 * 看板数据层（真实数据）
 * ============================================
 * 
 * 数据性质：真实采集数据，非 Mock
 * 采集时间：2026-04-23
 * 数据来源：App Store 用户真实评论（通过官方 RSS API）
 * 采集量级：9692 条用户评论
 * 
 * 数据文件：
 * - data/processed/*_ai_opportunities.json（AI 分析结果）
 * - data/raw/（原始采集数据）
 * ============================================
 */
import { 
  CategoryConfig, 
  CategoryAIAnalysis,
  AIOpportunity,
  EvidenceSample,
  DashboardData,
  DataSourceInfo,
  SubCategory,
  CrawlStats,
  AppCategory
} from '../types';

// ============================================
// 数据源声明（真实采集渠道）
// 数据采集时间：2026-04-23
// ============================================
export const COMPLIANT_DATA_SOURCES: DataSourceInfo[] = [
  { 
    id: 'appstore', 
    name: 'App Store', 
    provider: 'Apple',
    complianceStatus: 'official',
    description: 'iOS 应用商店用户评论（RSS API），约 9,700 条',
    docUrl: 'https://apps.apple.com',
  },
  { 
    id: 'hackernews', 
    name: 'Hacker News', 
    provider: 'Y Combinator',
    complianceStatus: 'official',
    description: '科技社区讨论（Algolia API），约 7,100 条',
    docUrl: 'https://news.ycombinator.com',
  },
  { 
    id: 'googleplay', 
    name: 'Google Play', 
    provider: 'Google',
    complianceStatus: 'official',
    description: 'Android 应用商店用户评论，约 1,600 条',
    docUrl: 'https://play.google.com',
  },
];

// ============================================
// 类目配置（四大板块）
// ============================================
export const CATEGORY_CONFIGS: CategoryConfig[] = [
  { 
    id: 'wechat', 
    name: '微信生态', 
    shortLabel: '微信生态',
    description: '微信及其小程序、公众号等生态产品'
  },
  { 
    id: 'social', 
    name: '社交娱乐', 
    shortLabel: '社交娱乐',
    description: '陌生人社交、兴趣社区、内容平台、播客'
  },
  { 
    id: 'ai', 
    name: 'AI应用', 
    shortLabel: 'AI应用',
    description: 'AI 对话、AI 搜索、AI 创作、AI 陪伴'
  },
  { 
    id: 'more', 
    name: '更多场景', 
    shortLabel: '更多场景',
    description: '办公协作、教育学习、医疗健康、效率工具',
    subCategories: [
      { id: 'office', label: 'AI 办公', apps: ['钉钉', '飞书', '腾讯会议'] },
      { id: 'education', label: 'AI 教育', apps: ['作业帮'] },
      { id: 'health', label: 'AI 医疗', apps: ['好大夫', '丁香医生'] },
      { id: 'productivity', label: '效率工具', apps: ['滴答清单'] },
    ]
  },
];

// ============================================
// 采集统计（按类目）
// ============================================
export const CRAWL_STATS: CrawlStats[] = [
  { category: 'wechat', apps_crawled: [{ name: '微信', count: 500 }], total_reviews: 500, crawl_date: '2026-04-23' },
  { category: 'social', apps_crawled: [
    { name: 'Soul', count: 500 },
    { name: '探探', count: 500 },
    { name: '陌陌', count: 500 },
    { name: '小红书', count: 500 },
    { name: '微博', count: 500 },
    { name: '小宇宙', count: 500 },
    { name: '喜马拉雅', count: 500 },
    { name: '知乎', count: 500 },
  ], total_reviews: 4000, crawl_date: '2026-04-23' },
  { category: 'ai', apps_crawled: [
    { name: 'Kimi', count: 500 },
    { name: '豆包', count: 500 },
    { name: 'DeepSeek', count: 500 },
    { name: '通义千问', count: 500 },
    { name: '元宝', count: 500 },
    { name: '网易有道词典', count: 500 },
  ], total_reviews: 3000, crawl_date: '2026-04-23' },
  { category: 'more', apps_crawled: [
    { name: '钉钉', count: 500 },
    { name: '腾讯会议', count: 500 },
    { name: '企业微信', count: 500 },
    { name: '滴答清单', count: 500 },
    { name: '印象笔记', count: 192 },
  ], total_reviews: 2192, crawl_date: '2026-04-23' },
];

// ============================================
// 采集统计（按渠道） - 用于开屏动效
// 自动生成时间: 2026-04-24T01:18:11.217262
// ============================================
import { ChannelCrawlStats } from '../types';

// 动态计算时间范围
const getChannelTimeRange = () => {
  const endDate = new Date();
  const startDate = new Date();
  startDate.setFullYear(startDate.getFullYear() - 1);
  return {
    start: startDate.toISOString().split('T')[0],
    end: endDate.toISOString().split('T')[0],
  };
};

export const CHANNEL_CRAWL_STATS: ChannelCrawlStats = {
  totalReviews: 18419,
  channels: [
    { id: 'appstore', name: 'App Store', region: '中国区', count: 9692 },
    { id: 'googleplay', name: 'Google Play', region: '全球', count: 1600 },
    { id: 'hackernews', name: 'Hacker News', region: '全球', count: 7127 },
  ],
  timeRange: getChannelTimeRange(),
  lastUpdated: '2026-04-24',
};

// ============================================
// AI 介入机会分析数据
// 核心数据结构：按类目聚合的 AI 介入机会
// 使用整合后的数据（合并相似痛点，优选证据样本）
// ============================================

// 导入整合后的分析数据
import wechatData from '../../data/processed/wechat_ai_opportunities_consolidated.json';
import socialData from '../../data/processed/social_ai_opportunities_consolidated.json';
import aiData from '../../data/processed/ai_ai_opportunities_consolidated.json';
import moreData from '../../data/processed/more_ai_opportunities_consolidated.json';

// 微信生态 AI 介入机会
const WECHAT_ANALYSIS: CategoryAIAnalysis = wechatData as CategoryAIAnalysis;

// 社交娱乐 AI 介入机会
const SOCIAL_ANALYSIS: CategoryAIAnalysis = socialData as CategoryAIAnalysis;

// AI 应用类目 AI 介入机会
const AI_ANALYSIS: CategoryAIAnalysis = aiData as CategoryAIAnalysis;

// 更多场景类目 AI 介入机会
const MORE_ANALYSIS: CategoryAIAnalysis = moreData as CategoryAIAnalysis;

// ============================================
// 整合所有分析数据
// ============================================
export const ALL_ANALYSES: CategoryAIAnalysis[] = [
  WECHAT_ANALYSIS,
  SOCIAL_ANALYSIS,
  AI_ANALYSIS,
  MORE_ANALYSIS,
];

// ============================================
// 导出看板整体数据
// ============================================
export const dashboardData: DashboardData = {
  categories: CATEGORY_CONFIGS,
  analyses: ALL_ANALYSES,
  lastUpdated: '2026-04-24',
  disclaimer: '数据来源：App Store、Google Play、Hacker News 用户真实评论（近一年数据）。共采集 18,400+ 条评论，覆盖微信、Soul、探探、Kimi、豆包、钉钉等主流应用。每个 AI 介入机会均有精准的数据溯源，样本可直接跳转至原始评论。',
  crawlStats: CRAWL_STATS,
};

// 兼容旧导出名
export const DASHBOARD_DATA = dashboardData;

// ============================================
// 辅助函数
// ============================================

// 获取某类目的分析数据
export function getAnalysisByCategory(categoryId: AppCategory): CategoryAIAnalysis | undefined {
  return ALL_ANALYSES.find(a => a.category === categoryId);
}

/**
 * 计算需求点的"主产品占比"和"是否为杂簇"。
 * 用于 post-filter：
 *   - 硬过滤：主产品<30% 且 产品数>10 → 直接剔除（聚类明显出错的杂簇）
 *   - 软标记：主产品<50% 且 产品数>5 → 保留但标记 isCrossProduct
 */
function analyzeProductCoverage(opp: AIOpportunity): {
  mainProductRatio: number;
  productCount: number;
  isDirty: boolean;    // 杂簇：硬过滤
  isCrossProduct: boolean;  // 真的跨多产品：软标记
} {
  const pb = (opp as any).product_breakdown as Record<string, number> | undefined;
  if (!pb || Object.keys(pb).length === 0) {
    return { mainProductRatio: 1, productCount: 0, isDirty: false, isCrossProduct: false };
  }
  const values = Object.values(pb);
  const total = values.reduce((a, b) => a + b, 0);
  const top = Math.max(...values);
  const ratio = total > 0 ? top / total : 1;
  const count = Object.keys(pb).length;
  return {
    mainProductRatio: ratio,
    productCount: count,
    // 硬过滤：明显的杂簇 —— 主产品占比不足 40% 且产品数超过 6 个
    isDirty: ratio < 0.40 && count > 6,
    // 软标记：真正跨产品的通用需求
    isCrossProduct: ratio < 0.70 && count >= 3,
  };
}

// 获取某类目的 AI 介入机会列表（带杂簇过滤）
export function getOpportunitiesByCategory(categoryId: AppCategory): AIOpportunity[] {
  const analysis = getAnalysisByCategory(categoryId);
  if (!analysis) return [];
  return analysis.ai_opportunities.filter(opp => {
    const { isDirty } = analyzeProductCoverage(opp);
    return !isDirty; // 过滤掉杂簇
  });
}

// 获取某个具体的 AI 介入机会
export function getOpportunityById(opportunityId: string): AIOpportunity | undefined {
  for (const analysis of ALL_ANALYSES) {
    const opp = analysis.ai_opportunities.find(o => o.id === opportunityId);
    if (opp) return opp;
  }
  return undefined;
}

// 获取跨类目共性机会
export function getCrossProductOpportunities(): AIOpportunity[] {
  const result: AIOpportunity[] = [];
  for (const analysis of ALL_ANALYSES) {
    for (const opp of analysis.ai_opportunities) {
      if (opp.cross_product_relevance.length > 0) {
        result.push(opp);
      }
    }
  }
  return result;
}

// 按 AI 介入类型筛选
export function getOpportunitiesByType(type: '轻量介入' | '重量介入'): AIOpportunity[] {
  const result: AIOpportunity[] = [];
  for (const analysis of ALL_ANALYSES) {
    for (const opp of analysis.ai_opportunities) {
      if (opp.ai_intervention_type === type) {
        result.push(opp);
      }
    }
  }
  return result;
}

// 获取类目配置
export function getCategoryConfig(categoryId: AppCategory): CategoryConfig | undefined {
  return CATEGORY_CONFIGS.find(c => c.id === categoryId);
}

// ============================================
// 兼容旧 App.tsx 接口
// 将 AIOpportunity 转换为旧的 UserNeed 格式
// ============================================

import type { UserNeed, Reference, MentionSource } from '../types';

// 判断字符串是否为中文内容（中文字符占比 > 30%）
function isChinese(text: string): boolean {
  if (!text) return false;
  const chineseChars = (text.match(/[\u4e00-\u9fa5]/g) || []).length;
  return chineseChars / Math.max(text.length, 1) > 0.3;
}

// 解析来源渠道
function parseChannel(sample: any): string {
  const url = sample.source_url || '';
  if (url.includes('play.google.com')) return 'Google Play';
  if (url.includes('tousu.sina.com') || url.includes('heimao')) return '黑猫投诉';
  if (url.includes('news.ycombinator.com')) return 'Hacker News';
  if (url.includes('v2ex.com')) return 'V2EX';
  if (url.includes('reddit.com')) return 'Reddit';
  if (url.includes('xiaohongshu.com')) return '小红书';
  if (url.includes('coolapk.com')) return '酷安';
  return 'App Store';
}

// 将 AIOpportunity 转换为 UserNeed（旧格式）
function opportunityToNeed(opp: AIOpportunity, categoryId: AppCategory): UserNeed {
  // 1. 优先使用中文样本，如果没有中文样本则使用全部样本
  const allSamples = opp.evidence_samples;
  const chineseSamples = allSamples.filter((s: any) => {
    const text = s.content || s.original_text || '';
    return isChinese(text);
  });
  
  // 如果有中文样本就用中文，没有就用全部（保证不会为空）
  const effectiveSamples = chineseSamples.length > 0 ? chineseSamples : allSamples;

  // 2. 按来源分组，实现来源多元化
  const samplesByChannel = new Map<string, any[]>();
  effectiveSamples.forEach((s: any) => {
    const channel = parseChannel(s);
    if (!samplesByChannel.has(channel)) {
      samplesByChannel.set(channel, []);
    }
    samplesByChannel.get(channel)!.push(s);
  });

  // 3. 轮询选取样本（每个渠道各取一条，循环直到取满 5 条）
  // 优先级：有索引链接的渠道（小红书、酷安）> 其他 > App Store
  const channelPriority = ['小红书', '酷安', 'V2EX', 'Reddit', '黑猫投诉', 'Google Play', 'App Store', 'Hacker News'];
  const sortedChannels = Array.from(samplesByChannel.keys()).sort((a, b) => {
    const aIdx = channelPriority.indexOf(a);
    const bIdx = channelPriority.indexOf(b);
    return (aIdx === -1 ? 999 : aIdx) - (bIdx === -1 ? 999 : bIdx);
  });

  const selectedSamples: any[] = [];
  const channelIndices = new Map<string, number>();
  sortedChannels.forEach(ch => channelIndices.set(ch, 0));

  while (selectedSamples.length < 5) {
    let added = false;
    for (const channel of sortedChannels) {
      if (selectedSamples.length >= 5) break;
      const samples = samplesByChannel.get(channel)!;
      const idx = channelIndices.get(channel)!;
      if (idx < samples.length) {
        selectedSamples.push(samples[idx]);
        channelIndices.set(channel, idx + 1);
        added = true;
      }
    }
    if (!added) break; // 所有渠道都取完了
  }

  // 4. 转换为 Reference 格式
  const references: Reference[] = selectedSamples.map((s: any, idx: number) => {
    const sourceStr = s.source || '';
    const [platform, appName] = sourceStr.includes(' - ') 
      ? sourceStr.split(' - ', 2) 
      : [sourceStr, ''];
    
    // 提取产品名称：优先用 app_name，其次从 source 解析
    const product = s.app_name || appName || '';
    
    return {
      id: s.id || `sample_${idx}`,
      title: (product || '用户') + ' 评论',
      snippet: s.content || s.original_text || '',
      url: s.source_url || '',
      source: parseChannel(s),
      // 时间：有就显示，没有就留空（前端会判断是否渲染）
      date: s.date || '',
      author: s.author || '',
      rating: s.rating,
      product: product,
      translation: s.translation || '',
      relevance_note: s.pain_point_extracted || s.relevance_note || '',
    };
  });

  // 5. 构建 mentionSources 统计
  const sourceMap = new Map<string, number>();
  effectiveSamples.forEach((s: any) => {
    const channel = parseChannel(s);
    sourceMap.set(channel, (sourceMap.get(channel) || 0) + 1);
  });
  
  const mentionSources: MentionSource[] = Array.from(sourceMap.entries())
    .map(([platform, count]) => ({ platform, count }))
    .sort((a, b) => b.count - a.count);

  // 6. 优先从新 pipeline 的 product_breakdown 取（按提及数排序），
  //    回退到 evidence_samples 里的 app_name
  let filteredApps: string[] = [];
  const productBreakdown = (opp as any).product_breakdown as Record<string, number> | undefined;
  if (productBreakdown && Object.keys(productBreakdown).length > 0) {
    filteredApps = Object.entries(productBreakdown)
      .sort((a, b) => b[1] - a[1])
      .map(([app]) => app)
      // 过滤掉 HN 的 story_title 长文本（看起来像话题标题而非产品名）
      .filter(app => app.length > 0 && app.length <= 30 && !app.includes(':'));
  }
  // 兜底：从 evidence 样本里提取
  if (filteredApps.length === 0) {
    const appCountMap = new Map<string, number>();
    effectiveSamples.forEach((s: any) => {
      const appName = s.app_name || '';
      if (appName && appName.length <= 30) {
        appCountMap.set(appName, (appCountMap.get(appName) || 0) + 1);
      }
    });
    filteredApps = Array.from(appCountMap.entries())
      .sort((a, b) => b[1] - a[1])
      .map(([app]) => app);
  }

  return {
    id: opp.id,
    title: opp.title,
    description: opp.description,
    category: categoryId,
    subcategory: undefined,
    // 只显示中文 app 名称，过滤掉英文标题
    apps: filteredApps,
    // 关键词：使用 AI 关键词而非合并来源（合并来源可能包含分类名）
    keywords: (opp.ai_keywords || []).slice(0, 4),
    sentiment: opp.ai_intervention_type === '轻量介入' ? 'mixed' : 'negative',
    priority: opp.priority,
    mentionCount: opp.source_stats.exact_match_count,
    mentionSources,
    references,
    // AI 介入建议
    aiSuggestion: (opp as any).ai_suggestion || '',
    // 用户心声
    userVoice: (opp as any).user_voice || '',
    // AI 方案相关
    aiSolution: (opp as any).ai_solution || '',
    aiKeywords: (opp as any).ai_keywords || [],
    aiDescription: (opp as any).ai_description || '',
    // 后端 demand_type：功能缺失 / 体验问题 / 平台策略
    demandType: (opp as any).demand_type || '',
    // 是否为跨多个产品的通用需求（用于 UI 展示标识）
    isCrossProduct: analyzeProductCoverage(opp).isCrossProduct,
    // 是否为本周新发现的需求（Step 10 合并时打的标）
    isNew: (opp as any).is_new === true,
    discoveredAt: (opp as any).discovered_at || '',
    // 数据源分布（用于前端"按数据源筛选"）
    sourceBreakdown: (opp.source_stats as any)?.source_breakdown || {},
  } as any;
}

// 获取某类目的需求列表（旧接口，兼容 App.tsx）
export function getNeedsByCategory(categoryId: AppCategory): UserNeed[] {
  const opportunities = getOpportunitiesByCategory(categoryId);
  return opportunities.map(opp => opportunityToNeed(opp, categoryId));
}

// 获取有数据的子分类列表（旧接口，兼容 App.tsx）
export function getSubCategoriesWithNeeds(categoryId: AppCategory): { subCategory: SubCategory; needCount: number }[] {
  const config = getCategoryConfig(categoryId);
  if (!config?.subCategories) return [];
  
  // 目前子分类逻辑暂不实现，返回空数组
  return [];
}

// 旧常量兼容
export const CATEGORY_CONFIG: Record<string, { label: string; shortLabel: string; desc: string }> = {
  wechat: { label: '微信生态', shortLabel: '微信生态', desc: '微信及其小程序、公众号等生态产品' },
  social: { label: '社交娱乐', shortLabel: '社交娱乐', desc: '陌生人社交、兴趣社区、内容平台、播客' },
  ai: { label: 'AI应用', shortLabel: 'AI应用', desc: 'AI 对话、AI 搜索、AI 创作、AI 陪伴' },
  more: { label: '更多场景', shortLabel: '更多场景', desc: '办公协作、教育学习、医疗健康、效率工具' },
};

export const MORE_SUB_CATEGORIES = CATEGORY_CONFIGS.find(c => c.id === 'more')?.subCategories || [];

// 动态计算数据采集时间范围：当天往前推 1 年
const getDataCollectionPeriod = () => {
  const endDate = new Date();
  const startDate = new Date();
  startDate.setFullYear(startDate.getFullYear() - 1);
  
  return {
    startDate: startDate.toISOString().split('T')[0],
    endDate: endDate.toISOString().split('T')[0],
    description: '近一年数据',
  };
};

export const DATA_COLLECTION_PERIOD = getDataCollectionPeriod();

export default dashboardData;

// 产品需求机会（自动生成于 2026-04-24 09:46）
export const PRODUCT_OPPORTUNITIES = [
  {
    id: 'relationship_maintenance_3d4c3a',
    scenarioId: 'relationship_maintenance',
    title: '关系维护',
    description: '用户希望更好地维护与亲友的关系',
    priority: 'P0',
    productValue: 'high',
    mentionCount: 946,
    avgRating: 2.7,
    userVoices: ['随意批评用户，聊天次数到敷衍，乱加我的设定  ，设计它的人脑子有问题  浪费我精力 ，势力眼', '继续加强。期待新版本新体验。不然就要掉队了。国产的领头羊还没', '可以改正一下，不要连这么基础的功能都要钱，知道还是需要吃饭和'],
    aiOpportunities: [
    {
      type: '智能提醒',
      desc: 'AI 识别重要关系并提醒用户保持联系',
    },{
      type: '话题建议',
      desc: 'AI 根据共同兴趣推荐聊天话题',
    },{
      type: '仪式感增强',
      desc: 'AI 在特殊日子生成个性化祝福内容',
    }
    ],
    dataSources: { 'App Store': 826, 'Google Play': 120 },
    evidenceSamples: [
    {
      text: '随意批评用户，聊天次数到敷衍，乱加我的设定  ，设计它的人脑子有问题  浪费我精力 ，势力眼',
      source: 'App Store',
      app: 'Kimi',
      sentiment: 'negative',
    },{
      text: '需要开新聊天时。能不能自动识别。把刚刚没结束的内容自动带入到新聊天中呢。每次建立新聊天都得告诉它刚刚的聊天记忆载入。另外搜索能力很强但是错误信息不少。甄别分析能力需要提升。感觉这是架构问题吧。还是训练',
      source: 'App Store',
      app: 'Kimi',
      sentiment: 'negative',
    },{
      text: '好软件是好软件，就是有点问题聊天上和查资料上限动辄直接六天，希望可以改正一下，不要连这么基础的功能都要钱，知道还是需要吃饭和成本的，但是能不能改一下？最高限制为24个小时而不是一百多小时。',
      source: 'App Store',
      app: 'Kimi',
      sentiment: 'neutral',
    },{
      text: '非常好很方便可以安在各个聊天工具里（微信飞书）初学者也能好好使用',
      source: 'App Store',
      app: 'Kimi',
      sentiment: 'positive',
    },{
      text: '也是最好的导师最好的朋友',
      source: 'App Store',
      app: 'Kimi',
      sentiment: 'positive',
    }
    ],
  },  {
    id: 'emotional_expression_233bf0',
    scenarioId: 'emotional_expression',
    title: '情感表达',
    description: '用户想更好地表达情感，但找不到合适的方式',
    priority: 'P0',
    productValue: 'high',
    mentionCount: 758,
    avgRating: 2.8,
    userVoices: ['&gt; 嗯嗯, was &quot;cute&quot; where a man should h...', 'Great to see another layer of transparency in ios1...', '用 你就让我交费 你最起码也得说几句话吧'],
    aiOpportunities: [
    {
      type: '表达助手',
      desc: 'AI 帮助用户将想法转化为合适的文字',
    },{
      type: '情绪识别',
      desc: 'AI 感知对方情绪并建议回应方式',
    },{
      type: '创意表达',
      desc: 'AI 生成个性化表情/贴纸/小视频',
    }
    ],
    dataSources: { 'Hacker News': 2, 'App Store': 714, 'Google Play': 42 },
    evidenceSamples: [
    {
      text: '&gt; 嗯嗯, was &quot;cute&quot; where a man should have just said 嗯. Apparently, this is the kind of t',
      source: 'Hacker News',
      app: '',
      sentiment: 'neutral',
    },{
      text: 'Great to see another layer of transparency in ios14. Bit I wonder why everyone talking about one spe',
      source: 'Hacker News',
      app: '',
      sentiment: 'neutral',
    },{
      text: '会员会员 还是会员 已到高峰期一句话都说不出来 然后一天24个小时全是高峰期 和诈骗软件的套路一样 我压根都不知道你能不能用 你就让我交费 你最起码也得说几句话吧',
      source: 'App Store',
      app: 'Kimi',
      sentiment: 'negative',
    },{
      text: '更新后语音播报读了一段后开始卡顿，重新语音播报还是不行，麻烦尽快修复，很不方便，谢谢',
      source: 'App Store',
      app: 'Kimi',
      sentiment: 'positive',
    },{
      text: '何时能提高语音识别的精准度，英文识别错多一些，，语音识别总出错，，资源能力不足时就直说，还总回复累了，整的跟缺心眼一样',
      source: 'App Store',
      app: 'Kimi',
      sentiment: 'neutral',
    }
    ],
  },  {
    id: 'group_coordination_649828',
    scenarioId: 'group_coordination',
    title: '群体协调',
    description: '用户需要在群组中协调多人活动',
    priority: 'P0',
    productValue: 'high',
    mentionCount: 659,
    avgRating: 2.3,
    userVoices: ['I am but that is despite there being many very sol...', 'I know that people keep saying &quot;we&#x27;re ea...', 'I&#x27;ve conducted hundreds of FAANG-level coding...'],
    aiOpportunities: [
    {
      type: '智能协调',
      desc: 'AI 自动整合各方时间/意向，提出最优方案',
    },{
      type: '任务追踪',
      desc: 'AI 追踪群内待办事项完成情况',
    },{
      type: '信息摘要',
      desc: 'AI 总结群聊重点，@未读重要消息',
    }
    ],
    dataSources: { 'Hacker News': 77, 'App Store': 536, 'Google Play': 46 },
    evidenceSamples: [
    {
      text: 'I am but that is despite there being many very solid reasons not to. It&#x27;s mainly painful until',
      source: 'Hacker News',
      app: '',
      sentiment: 'neutral',
    },{
      text: 'I know that people keep saying &quot;we&#x27;re early on here&quot;, but I take it as a negative sig',
      source: 'Hacker News',
      app: '',
      sentiment: 'neutral',
    },{
      text: 'I&#x27;ve conducted hundreds of FAANG-level coding interviews, and recently tried to run my intervie',
      source: 'Hacker News',
      app: '',
      sentiment: 'neutral',
    },{
      text: 'There are several engineering tasks that I&#x27;ve just found explained better by ChatGPT than scour',
      source: 'Hacker News',
      app: '',
      sentiment: 'neutral',
    },{
      text: 'ChatGPT is cool and novel, but FAANG&#x27;s requirements for ML&#x2F;AI go far beyond what ChatGPT p',
      source: 'Hacker News',
      app: '',
      sentiment: 'neutral',
    }
    ],
  },  {
    id: 'quick_reply_75f411',
    scenarioId: 'quick_reply',
    title: '快速回复',
    description: '用户需要快速处理大量消息',
    priority: 'P0',
    productValue: 'high',
    mentionCount: 421,
    avgRating: 2.2,
    userVoices: ['付费用户更新2.6后，快速模式没用几下就拉倒了，提示3小时后，要么升级', '客服电话 退款通道邮件不回复', '用起来比其他ai好 不过就是连续问几个问题之后就说系统忙 回答不出来 建议充值'],
    aiOpportunities: [
    {
      type: '智能回复',
      desc: 'AI 根据上下文生成回复建议',
    },{
      type: '批量处理',
      desc: 'AI 帮助用户批量处理同类消息',
    },{
      type: '代理模式',
      desc: 'AI 在用户授权下自动处理简单消息',
    }
    ],
    dataSources: { 'App Store': 390, 'Google Play': 31 },
    evidenceSamples: [
    {
      text: '付费用户更新2.6后，快速模式没用几下就拉倒了，提示3小时后，要么升级',
      source: 'App Store',
      app: 'Kimi',
      sentiment: 'positive',
    },{
      text: 'kimi不开会员就用不了 客服态度和死人一样 官网没有客服电话 退款通道邮件不回复',
      source: 'App Store',
      app: 'Kimi',
      sentiment: 'neutral',
    },{
      text: '用起来比其他ai好 不过就是连续问几个问题之后就说系统忙 回答不出来 建议充值',
      source: 'App Store',
      app: 'Kimi',
      sentiment: 'neutral',
    },{
      text: '感觉升级后就是为了圈钱的——我说怎么一直在使用的时候老是跳提示让你升级，原来就是为了圈钱！ 特别难用，原本能正常聊的，现在就直接不能聊了，回复也是一坨‍太难用了 我恨你',
      source: 'App Store',
      app: 'Kimi',
      sentiment: 'negative',
    },{
      text: '用的人太多，经常卡顿',
      source: 'App Store',
      app: 'Kimi',
      sentiment: 'negative',
    }
    ],
  },  {
    id: 'work_life_balance_e455e8',
    scenarioId: 'work_life_balance',
    title: '工作生活边界',
    description: '用户希望区分工作和私人社交',
    priority: 'P0',
    productValue: 'high',
    mentionCount: 222,
    avgRating: 2.8,
    userVoices: ['在工作、学习和生活中遇到各种困难和问题，往往使人感到困惑和烦恼。自从有了KIMI，很多以往的问题都不...', '今天使用kimi发现表格渲染 bug 严重影响工作，今天突然变成无限制横向拉伸，长内容不换行，超出屏...', '差死了，明明就是已读乱回，千万别下！！！！！！！！！！！！！！！！！避雷！！！！！！！'],
    aiOpportunities: [
    {
      type: '场景切换',
      desc: 'AI 根据时间/地点自动切换工作/生活模式',
    },{
      type: '延迟回复',
      desc: 'AI 代为管理非工作时间的工作消息',
    },{
      type: '边界守护',
      desc: 'AI 帮助用户委婉拒绝不合理要求',
    }
    ],
    dataSources: { 'App Store': 204, 'Google Play': 18 },
    evidenceSamples: [
    {
      text: '在工作、学习和生活中遇到各种困难和问题，往往使人感到困惑和烦恼。自从有了KIMI，很多以往的问题都不成问题。它可以从更深层次及更长远的角度来分析问题，从而达到更好更完美的效果。',
      source: 'App Store',
      app: 'Kimi',
      sentiment: 'neutral',
    },{
      text: '今天使用kimi发现表格渲染 bug 严重影响工作，今天突然变成无限制横向拉伸，长内容不换行，超出屏幕数倍。4月17日更新后表格渲染异常，横向无限拉伸无法阅读，严重影响文档处理。',
      source: 'App Store',
      app: 'Kimi',
      sentiment: 'negative',
    },{
      text: '差死了，明明就是已读乱回，千万别下！！！！！！！！！！！！！！！！！避雷！！！！！！！',
      source: 'App Store',
      app: 'Kimi',
      sentiment: 'negative',
    },{
      text: '不是你这一到9点就没法用是怎么回事，而且还是周末',
      source: 'App Store',
      app: 'Kimi',
      sentiment: 'neutral',
    },{
      text: 'KIMI是我使用过的国内中文版大模型中处理Excel相关工作最杰出的！逻辑清晰，分析准确且细致。期望KIMI成为中国的GEMINI，在数学，科学，工程技术，医学，金融（经济学）等领域崭露头角，同时在A',
      source: 'App Store',
      app: 'Kimi',
      sentiment: 'neutral',
    }
    ],
  },  {
    id: 'fraud_protection_48208a',
    scenarioId: 'fraud_protection',
    title: '防诈防骗',
    description: '用户担心被骗或遇到不安全的内容',
    priority: 'P0',
    productValue: 'high',
    mentionCount: 195,
    avgRating: 1.6,
    userVoices: ['冲着clawbot去的，花了200月费， Agent 不挺的崩溃。 骗子公司', '作假吧，又说是骗你的。让查某平台规则，直接给我杜纂了一套新', '跟坨屎一样 自己推荐的东西成分表发出去又说不安全 不安全推荐什么？脑子有病了一样在左右脑互搏'],
    aiOpportunities: [
    {
      type: '风险识别',
      desc: 'AI 识别可疑消息/链接/转账',
    },{
      type: '身份验证',
      desc: 'AI 辅助验证对方真实身份',
    },{
      type: '安全提醒',
      desc: 'AI 在风险场景主动提醒',
    }
    ],
    dataSources: { 'App Store': 172, 'Google Play': 23 },
    evidenceSamples: [
    {
      text: '冲着clawbot去的，花了200月费， Agent 不挺的崩溃。 骗子公司',
      source: 'App Store',
      app: 'Kimi',
      sentiment: 'negative',
    },{
      text: '用kimi写论文的避雷一下，kimi会编造文献编造内容，一本正经的我都以为是真的，然后让他确认一下，他说 嘿嘿刚刚是骗你的啦！然后让他务必使用真实的，又编了一长串，又问他 你确定你没有作假吧，又说是骗',
      source: 'App Store',
      app: 'Kimi',
      sentiment: 'negative',
    },{
      text: '跟坨屎一样 自己推荐的东西成分表发出去又说不安全 不安全推荐什么？脑子有病了一样在左右脑互搏',
      source: 'App Store',
      app: '豆包',
      sentiment: 'positive',
    },{
      text: '点了外卖，等了一个多小时，没有送到，千问说系统原因赔偿我，让我再等了一个多小时，不仅赔偿没到，外卖也没到，千质问千问，千问说骗我的，从头到尾都是骗我的，说那些都是假的，我恨千问一辈子',
      source: 'App Store',
      app: '通义千问',
      sentiment: 'negative',
    },{
      text: '元宝APP真的超好用，界面简洁清爽，操作简单易懂，功能齐全实用，日常办事、便民服务一站式搞定，响应快不卡顿。福利靠谱划算，安全省心不繁琐，上手毫无难度，体验感拉满，日常必备宝藏软件，强烈推荐！',
      source: 'App Store',
      app: '元宝',
      sentiment: 'positive',
    }
    ],
  },  {
    id: 'info_overload_5f3d3a',
    scenarioId: 'info_overload',
    title: '信息过载',
    description: '用户被海量信息淹没，找不到重要内容',
    priority: 'P0',
    productValue: 'high',
    mentionCount: 189,
    avgRating: 2.2,
    userVoices: ['充了199，问了一个问题，网断了还没给出答案，就被限制了，让4小时后再问，好无语啊，找客服也找不到', '优先保证agant能回答问题，老是终止有点烦，而且是很频繁，', '发通知就发，app右上角给我多个小红点什么意思？点开又什么消'],
    aiOpportunities: [
    {
      type: '优先级排序',
      desc: 'AI 识别并置顶重要消息',
    },{
      type: '智能摘要',
      desc: 'AI 生成聊天记录/群消息摘要',
    },{
      type: '免打扰优化',
      desc: 'AI 学习用户习惯，智能管理通知',
    }
    ],
    dataSources: { 'App Store': 180, 'Google Play': 9 },
    evidenceSamples: [
    {
      text: '充了199，问了一个问题，网断了还没给出答案，就被限制了，让4小时后再问，好无语啊，找客服也找不到',
      source: 'App Store',
      app: 'Kimi',
      sentiment: 'neutral',
    },{
      text: '最近时常发生任务暂停，权益返还问题，算法确实不够用，咱也不能终止任务，希望优先保证agant能回答问题，老是终止有点烦，而且是很频繁，建议要么就不回答，可提示算力不足，不要回答了结果中断，这样体验感更',
      source: 'App Store',
      app: 'Kimi',
      sentiment: 'neutral',
    },{
      text: '你想发通知就发，app右上角给我多个小红点什么意思？点开又什么消息都没有，就想硬来膈应我？',
      source: 'App Store',
      app: 'Kimi',
      sentiment: 'neutral',
    },{
      text: '刚注册了电话搜了一些内容，过了一会就有内容相关的骚扰电话打来',
      source: 'App Store',
      app: 'Kimi',
      sentiment: 'neutral',
    },{
      text: '真的从来没用过这么差劲的人工智能软件，豆包DeepSeek都比这个好，明明就没有这个东西，非要说有害得我去试了半天，就是找不到，擅长耍人类是吗，真是人工智障',
      source: 'App Store',
      app: 'Kimi',
      sentiment: 'neutral',
    }
    ],
  },  {
    id: 'content_moderation_95c4ec',
    scenarioId: 'content_moderation',
    title: '内容治理',
    description: '用户遇到不良内容或骚扰',
    priority: 'P1',
    productValue: 'medium',
    mentionCount: 1429,
    avgRating: 1.3,
    userVoices: ['垃圾，最基本的问题他还能错，还要收费，条文都告诉他了他还能说错', '狗屎一样，刚开始好用，用到后面天天算力不足，开始收割了，垃圾', '真的垃圾，还没问几道题就跟我说算力不足要去充钱升级666'],
    aiOpportunities: [
    {
      type: '智能过滤',
      desc: 'AI 自动识别并过滤不良内容',
    },{
      type: '行为分析',
      desc: 'AI 识别异常行为模式',
    },{
      type: '社区守护',
      desc: 'AI 辅助维护群组健康氛围',
    }
    ],
    dataSources: { 'App Store': 1321, 'Google Play': 108 },
    evidenceSamples: [
    {
      text: '垃圾，最基本的问题他还能错，还要收费，条文都告诉他了他还能说错',
      source: 'App Store',
      app: 'Kimi',
      sentiment: 'negative',
    },{
      text: '狗屎一样，刚开始好用，用到后面天天算力不足，开始收割了，垃圾',
      source: 'App Store',
      app: 'Kimi',
      sentiment: 'neutral',
    },{
      text: '真的垃圾，还没问几道题就跟我说算力不足要去充钱升级666',
      source: 'App Store',
      app: 'Kimi',
      sentiment: 'negative',
    },{
      text: '现在是怎么个意思啊？就问了一个问题就太累了生成不了了。。。什么时候这么垃圾了',
      source: 'App Store',
      app: 'Kimi',
      sentiment: 'negative',
    },{
      text: '相当难用，内容会加入主观广告，让你的答案带有极端倾向性',
      source: 'App Store',
      app: 'Kimi',
      sentiment: 'negative',
    }
    ],
  },  {
    id: 'memory_retrieval_68a01c',
    scenarioId: 'memory_retrieval',
    title: '记忆检索',
    description: '用户想找回过去的聊天内容、图片、文件',
    priority: 'P1',
    productValue: 'medium',
    mentionCount: 905,
    avgRating: 2.2,
    userVoices: ['一直生成不了动不动就累了或者聊的人太多，一直点都没反应，以前还可以对话现在发都发不出去', '加一个可以关闭数据反馈的功能，还有word里面占位符读取后就', '之前说高峰期算力不足，请升级会员才可“畅用思考模型”。 升了会员，没两天，“思考模型”又用不了了，不...'],
    aiOpportunities: [
    {
      type: '语义搜索',
      desc: 'AI 理解用户模糊描述，精准定位内容',
    },{
      type: '智能归档',
      desc: 'AI 自动整理图片/文件/链接',
    },{
      type: '回忆助手',
      desc: 'AI 生成与某人/某时期的互动回顾',
    }
    ],
    dataSources: { 'App Store': 828, 'Google Play': 77 },
    evidenceSamples: [
    {
      text: '一直生成不了动不动就累了或者聊的人太多，一直点都没反应，以前还可以对话现在发都发不出去',
      source: 'App Store',
      app: 'Kimi',
      sentiment: 'neutral',
    },{
      text: '能不能加一个可以关闭数据反馈的功能，还有word里面占位符读取后就看不到图片，也无法识别LaTex格式',
      source: 'App Store',
      app: 'Kimi',
      sentiment: 'neutral',
    },{
      text: '之前说高峰期算力不足，请升级会员才可“畅用思考模型”。 升了会员，没两天，“思考模型”又用不了了，不问使用人意见，强行降级为快速模型，答案质量不可用，那买会员来还有啥意义！又再说什么“请升级会员”，这',
      source: 'App Store',
      app: 'Kimi',
      sentiment: 'neutral',
    },{
      text: '吃相太难看了 之前还能生成 ppt 现在却必须要订阅会员才行，有些时候来提的问题都不回答 说使用人数太多了 ，无语极了真的',
      source: 'App Store',
      app: 'Kimi',
      sentiment: 'negative',
    },{
      text: '经过一番体验，我觉得还不错，我是老用户了，优点是我发现这款应用适配性很高iPhone 6s都能流畅使用，缺点是对话上下文对话几下就要3小时之后才能恢复了，并且几乎是24小时高峰期，编写网站内容非常费时',
      source: 'App Store',
      app: 'Kimi',
      sentiment: 'neutral',
    }
    ],
  },  {
    id: 'social_entertainment_9e22ab',
    scenarioId: 'social_entertainment',
    title: '社交娱乐',
    description: '用户希望与朋友一起玩耍互动',
    priority: 'P1',
    productValue: 'medium',
    mentionCount: 487,
    avgRating: 2.1,
    userVoices: ['I built a mem0-based personal memory server — a kn...', 'I like to try out new notes&#x2F;PKM&#x2F;second b...', 'Initially it was, but Android&#x2F;Google have bec...'],
    aiOpportunities: [
    {
      type: '互动游戏',
      desc: 'AI 驱动的社交小游戏',
    },{
      type: '智能匹配',
      desc: 'AI 匹配兴趣相投的玩伴',
    },{
      type: '氛围营造',
      desc: 'AI 在群聊中增添趣味元素',
    }
    ],
    dataSources: { 'Hacker News': 28, 'App Store': 398, 'Google Play': 61 },
    evidenceSamples: [
    {
      text: 'I built a mem0-based personal memory server — a knowledge vault Claude can read&#x2F;write to. Getti',
      source: 'Hacker News',
      app: '',
      sentiment: 'neutral',
    },{
      text: 'I like to try out new notes&#x2F;PKM&#x2F;second brain apps but with AI tokens and limitations, I ta',
      source: 'Hacker News',
      app: '',
      sentiment: 'neutral',
    },{
      text: 'Initially it was, but Android&#x2F;Google have become the establishment. And ARM-based devices are b',
      source: 'Hacker News',
      app: '',
      sentiment: 'neutral',
    },{
      text: 'You laid out a number of points there, and I think some of them are indicative of what&#x27;s really',
      source: 'Hacker News',
      app: '',
      sentiment: 'neutral',
    },{
      text: 'What is the DedSec Project? Is the live adaptation of the Watch Dogs games, that brings mobile hacki',
      source: 'Hacker News',
      app: '',
      sentiment: 'neutral',
    }
    ],
  },  {
    id: 'privacy_control_d6bf5b',
    scenarioId: 'privacy_control',
    title: '隐私控制',
    description: '用户对个人信息暴露感到不安',
    priority: 'P1',
    productValue: 'medium',
    mentionCount: 417,
    avgRating: 1.9,
    userVoices: ['最近也不知道是怎么了，升级完以后连话都懒得说了，动不动就是聊的太长了，新建会话了以后有一样，刚问就聊...', '问他什么他答什么，答的东西也很实用。就是有时候会限制一些东西，比如什么涉及隐私什么的，但实际上就不存...', '做免费的直接搞成付费ai算了'],
    aiOpportunities: [
    {
      type: '隐私检测',
      desc: 'AI 提醒可能的隐私风险',
    },{
      type: '智能分组',
      desc: 'AI 自动管理好友分组和可见范围',
    },{
      type: '匿名模式',
      desc: 'AI 辅助的匿名社交场景',
    }
    ],
    dataSources: { 'App Store': 380, 'Google Play': 37 },
    evidenceSamples: [
    {
      text: '最近也不知道是怎么了，升级完以后连话都懒得说了，动不动就是聊的太长了，新建会话了以后有一样，刚问就聊的太长了，什么毛病啊，一个星都不想给',
      source: 'App Store',
      app: 'Kimi',
      sentiment: 'neutral',
    },{
      text: '问他什么他答什么，答的东西也很实用。就是有时候会限制一些东西，比如什么涉及隐私什么的，但实际上就不存在',
      source: 'App Store',
      app: 'Kimi',
      sentiment: 'neutral',
    },{
      text: '自从推出付费套餐之后正常使用就经常算力不足，特别是白天，基本上问三句就有一句会算力不足，不想做免费的直接搞成付费ai算了',
      source: 'App Store',
      app: 'Kimi',
      sentiment: 'neutral',
    },{
      text: '非常差 别的我都不想说了',
      source: 'App Store',
      app: 'Kimi',
      sentiment: 'negative',
    },{
      text: '我是一个业余汉化者 日漫翻译通常会参考很多AI和翻译软件 kimi是我对比于D和豆包来说（可能是我不会用这两）翻译最通顺、最贴合日常的AI   但对于非日语专业的我来说 帮助最大的还是kimi的识图功',
      source: 'App Store',
      app: 'Kimi',
      sentiment: 'neutral',
    }
    ],
  },  {
    id: 'digital_identity_a97376',
    scenarioId: 'digital_identity',
    title: '数字身份',
    description: '用户希望在数字世界中有更好的自我呈现',
    priority: 'P1',
    productValue: 'medium',
    mentionCount: 116,
    avgRating: 2.3,
    userVoices: ['这个月之暗面为了成功登月呢，已经向国人展示了其暗面——他们开始抛弃普通用户，稍微复杂一点的任务就分配...', '现在问Kimi一个题怎么做思路指挥出来一半思路完全展示不出来，根本看不懂再说什么', 'iOS 18.8.8 系统，更新豆包最新版本后，登录账号就出现所有按钮点击无反应、界面卡死，未登录状...'],
    aiOpportunities: [
    {
      type: 'AI头像',
      desc: 'AI 生成个性化虚拟形象',
    },{
      type: '内容美化',
      desc: 'AI 优化用户发布的图片/文字',
    },{
      type: '兴趣展示',
      desc: 'AI 帮助用户更好地展示兴趣爱好',
    }
    ],
    dataSources: { 'App Store': 112, 'Google Play': 4 },
    evidenceSamples: [
    {
      text: '这个月之暗面为了成功登月呢，已经向国人展示了其暗面——他们开始抛弃普通用户，稍微复杂一点的任务就分配不到算力就被拒绝回答了。大家一起抵制AI霸权吧',
      source: 'App Store',
      app: 'Kimi',
      sentiment: 'neutral',
    },{
      text: '现在问Kimi一个题怎么做思路指挥出来一半思路完全展示不出来，根本看不懂再说什么',
      source: 'App Store',
      app: 'Kimi',
      sentiment: 'neutral',
    },{
      text: 'iOS 18.8.8 系统，更新豆包最新版本后，登录账号就出现所有按钮点击无反应、界面卡死，未登录状态正常。已尝试卸载重装、强制重启手机、更换网络，均无效，请求尽快修复兼容问题。',
      source: 'App Store',
      app: '豆包',
      sentiment: 'negative',
    },{
      text: '作为一名将DeepSeek App深度融入日常工作的用户，我近期在“专家模式”下遇到了一个严重影响使用连续性的问题，特此反馈，希望官方团队能够关注。  问题描述： 在同一“专家模式”对话窗口内，我近期',
      source: 'App Store',
      app: 'DeepSeek',
      sentiment: 'positive',
    },{
      text: '现在的小d老师聊几句就弹出对话频繁  给的人设也不贴了  头像也不见了 虽然响应更快速 但完完全全像换了一款ai',
      source: 'App Store',
      app: 'DeepSeek',
      sentiment: 'positive',
    }
    ],
  },  {
    id: 'content_creation_6eb214',
    scenarioId: 'content_creation',
    title: '内容创作',
    description: '用户想创作有趣的内容但缺乏灵感或技能',
    priority: 'P2',
    productValue: 'medium',
    mentionCount: 46,
    avgRating: 3.8,
    userVoices: ['非常有趣的更新日志，让我的乐观旋转', '豆包非常的有趣，我很喜欢他豆包的语句也非常的流畅，温馨', '问个写差评的事，AI先是自作主张加一堆废话分析，明确说了只要文案，它还在那教育我“止损”。语气阴阳怪...'],
    aiOpportunities: [
    {
      type: '创意生成',
      desc: 'AI 根据场景生成创意内容',
    },{
      type: '素材推荐',
      desc: 'AI 推荐合适的配图/音乐/模板',
    },{
      type: '风格迁移',
      desc: 'AI 将用户内容转化为特定风格',
    }
    ],
    dataSources: { 'App Store': 42, 'Google Play': 4 },
    evidenceSamples: [
    {
      text: '非常有趣的更新日志，让我的乐观旋转',
      source: 'App Store',
      app: 'Kimi',
      sentiment: 'neutral',
    },{
      text: '豆包非常的有趣，我很喜欢他豆包的语句也非常的流畅，温馨',
      source: 'App Store',
      app: '豆包',
      sentiment: 'positive',
    },{
      text: '问个写差评的事，AI先是自作主张加一堆废话分析，明确说了只要文案，它还在那教育我“止损”。语气阴阳怪气，反问用户“满意了？去发吧”。最后质问它，它才认错。一个AI搞得跟有情绪一样，用户体验垃圾。',
      source: 'App Store',
      app: 'DeepSeek',
      sentiment: 'negative',
    },{
      text: '生图粗糙，没有差异化，没有风格（写实）选择，没有无水印下载，失去“复用创意”功能、修改提示词要一遍一遍复制、粘贴，不能在图像上点击生成视频，需要下载再上传（二次审查或是安全考虑？不得而知）不如通义时代',
      source: 'App Store',
      app: '通义千问',
      sentiment: 'neutral',
    },{
      text: '中介做房源介绍文案，亮点突出又真实，客户咨询量都多了不少哈哈哈',
      source: 'App Store',
      app: '通义千问',
      sentiment: 'neutral',
    }
    ],
  }
];

export const OPPORTUNITIES_META = {
  generatedAt: '2026-04-24T01:18:01.301177',
  totalReviewsAnalyzed: 32421,
  scenariosIdentified: 13,
};
