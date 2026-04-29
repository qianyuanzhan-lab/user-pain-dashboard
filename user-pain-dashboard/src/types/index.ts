// ============================================
// 需求挖掘机 - 类型定义
// 核心视角：类目级 AI 介入机会
// ============================================

// 应用分类（四大板块）
export type AppCategory = 'wechat' | 'social' | 'ai' | 'more';

// 情感倾向
export type Sentiment = 'positive' | 'negative' | 'mixed';

// 数据源类型
export type SourceType = 'review' | 'complaint' | 'community' | 'official';

// 数据合规状态
export type ComplianceStatus = 'official' | 'public' | 'limited';

// ============================================
// AI 介入机会相关类型（核心）
// ============================================

// AI 介入类型
export type AIInterventionType = '轻量介入' | '重量介入';

// 证据样本（精准溯源）
export interface EvidenceSample {
  id: string;                    // 样本唯一 ID
  app_name: string;              // 来源产品
  author: string;                // 用户名
  content: string;               // 原始评论内容（完整）
  rating: number;                // 评分
  date: string;                  // 日期
  source_url: string;            // 原始可跳转链接
  relevance_note: string;        // 与该需求的关联说明
}

// 优先级等级
export type PriorityLevel = 'P0' | 'P1' | 'P2' | 'P3';

// AI 介入机会
export interface AIOpportunity {
  id: string;                              // 机会唯一 ID
  title: string;                           // 简洁标题（10字以内）
  description: string;                     // 一句话描述
  ai_intervention_type: AIInterventionType; // AI 介入类型
  user_pain_summary: string;               // 用户痛点的底层本质
  priority: PriorityLevel;                 // 优先级：P0（紧急） > P1（高） > P2（中） > P3（低）
  cross_product_relevance: AppCategory[];  // 跨类目共性标签
  source_stats: {
    exact_match_count: number;             // 精准相关的评论数量
    products_mentioned: string[];          // 涉及的产品列表
  };
  evidence_samples: EvidenceSample[];      // 证据样本（≥5条）
}

// ============================================
// 类目数据结构
// ============================================

// 类目级 AI 机会分析结果
export interface CategoryAIAnalysis {
  category: AppCategory;
  category_name: string;
  analysis_date: string;
  products_analyzed: string[];
  total_reviews_analyzed: number;
  ai_opportunities: AIOpportunity[];
}

// 子类目
export interface SubCategory {
  id: string;
  label: string;
  apps: string[];
}

// 类目配置
export interface CategoryConfig {
  id: AppCategory;
  name: string;
  shortLabel: string;
  description: string;
  subCategories?: SubCategory[];
}

// ============================================
// 数据源相关类型
// ============================================

// 数据源信息
export interface DataSourceInfo {
  id: string;
  name: string;
  provider: string;
  complianceStatus: ComplianceStatus;
  description: string;
  docUrl: string;
}

// 采集统计（按类目）
export interface CrawlStats {
  category: AppCategory;
  apps_crawled: { name: string; count: number }[];
  total_reviews: number;
  crawl_date: string;
}

// 数据采集渠道统计（按渠道）
export interface ChannelCrawlStats {
  totalReviews: number;
  channels: {
    id: string;
    name: string;
    region: string;
    count: number;
  }[];
  timeRange: {
    start: string;
    end: string;
  };
  lastUpdated: string;
}

// ============================================
// 看板整体数据
// ============================================

export interface DashboardData {
  categories: CategoryConfig[];
  analyses: CategoryAIAnalysis[];
  lastUpdated: string;
  disclaimer: string;
  crawlStats: CrawlStats[];
}

// ============================================
// 旧类型兼容（逐步废弃）
// ============================================

// @deprecated 使用 EvidenceSample 代替
export interface Reference {
  id: string;
  title: string;
  source: string;
  sourceType?: SourceType;
  url: string;
  date: string;
  snippet: string;
  author?: string;       // 评论作者昵称
  rating?: number;       // 评分（1-5星）
  product?: string;      // 针对的产品名称
  translation?: string;  // 中文翻译（用于 Hacker News 等英文来源）
  relevance_note?: string; // LLM 抽出的"用户建议"一句话要点
}

// @deprecated 使用 AIOpportunity 代替
export interface MentionSource {
  platform: string;
  count: number;
  url?: string;
  note?: string;
}

// @deprecated 使用 AIOpportunity 代替
export interface UserNeed {
  id: string;
  title: string;
  description: string;
  category: AppCategory;
  subcategory?: string;
  sentiment: Sentiment;
  priority?: PriorityLevel;  // 优先级
  mentionCount: number;
  mentionSources: MentionSource[];
  references: Reference[];
  apps: string[];
  keywords: string[];
  aiSuggestion?: string;  // AI 介入建议
  userVoice?: string;     // 用户原声（简洁版）
  // AI 方案相关
  aiSolution?: string;       // AI 方案名称
  aiKeywords?: string[];     // AI 方案关键词
  aiDescription?: string;    // AI 方案描述
}

// @deprecated 使用 CategoryConfig 代替
export interface CategoryData {
  id: AppCategory;
  name: string;
  needs: UserNeed[];
  description: string;
  subCategories?: SubCategory[];
}
