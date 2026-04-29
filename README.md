# 需求挖掘机 · User Pain Dashboard

从 App Store / Google Play / Hacker News 采集用户评论和讨论，用 LLM 自动抽取需求并聚类，产出按赛道（微信 / 社交娱乐 / AI 工具 / 效率工具）组织的「用户需求清单」。

## 🏛️ 架构

```
抓取（AppStore/GooglePlay/HackerNews）
     ↓
Step 1-4  清洗 & 过滤（规则）
     ↓
Step 5    LLM 抽"需求原子"（DeepSeek）
     ↓
Step 6    本地 embedding 聚类（BGE-small-zh）
     ↓
Step 7    LLM 为每个簇起标题 / 类型 / AI 评分
     ↓
Step 8    二级合并相似簇
     ↓
Step 8.6  LLM 描述修订（保证标题和描述自洽）
     ↓
Step 9    导出为 Dashboard JSON
     ↓
Step 10   （自动化模式）增量合并：新增打 is_new 标识
     ↓
Vite 构建 → GitHub Pages
```

## 🚀 自动化部署（GitHub Actions + Pages）

### 1. 一次性设置

```bash
# 本仓库
cd /Users/doudou/WorkBuddy/20260421111045
git init
git add .
git commit -m "initial commit"

# 到 https://github.com/new 创建一个 public repo（比如 user-pain-dashboard）
git remote add origin git@github.com:<USERNAME>/<REPO>.git
git branch -M main
git push -u origin main
```

### 2. 添加 GitHub Secrets

在 repo Settings → Secrets and variables → Actions → New repository secret：

- `DEEPSEEK_API_KEY` = 你的 DeepSeek API Key

### 3. 启用 GitHub Pages

Settings → Pages → Source 选 `Deploy from a branch` → 选 `gh-pages` 分支 → Save。

首次跑完 workflow 后，访问 `https://<USERNAME>.github.io/<REPO>/`。

### 4. 触发首次跑

- 定时：每周一北京时间 7:00 自动触发（已配置 cron）
- 手动：在 Actions 标签页手动 `Run workflow`

## 🏃 本地开发

```bash
# 安装依赖
cd user-pain-dashboard
npm install
pip install sentence-transformers scikit-learn numpy scipy

# 前端启动
npm run dev
# 打开 http://localhost:5173/

# 跑一次完整管线（需要 .env 里的 DEEPSEEK_API_KEY）
for cat in wechat social ai more; do
  python3 scripts/pipeline_step1_4.py --category $cat
  python3 scripts/pipeline_step5_atoms.py --category $cat
  python3 scripts/pipeline_step6_cluster.py --category $cat --distance-threshold 0.42
  python3 scripts/pipeline_step7_label.py --category $cat
  python3 scripts/pipeline_step8_merge.py --category $cat --sim 0.82
  python3 scripts/pipeline_step8_6_refine.py --category $cat
  python3 scripts/pipeline_step9_dashboard.py --category $cat
done
```

## 📁 目录结构

```
user-pain-dashboard/
  scripts/
    crawl_*.py                   # 各渠道抓取
    crawl_incremental.py          # 增量抓取（自动化用）
    pipeline_step1_4.py           # 清洗 & 过滤
    pipeline_step5_atoms.py       # LLM 抽需求原子
    pipeline_step6_cluster.py     # 本地 embedding 聚类
    pipeline_step7_label.py       # LLM 打标
    pipeline_step8_merge.py       # 二级合并
    pipeline_step8_6_refine.py    # 描述修订
    pipeline_step9_dashboard.py   # 导出前端 JSON
    pipeline_step10_merge_new.py  # 增量合并
  data/
    raw/               # 原始抓取（.gitignore）
    processed/         # 清洗后（只提交最终的 *_ai_opportunities_consolidated.json）
  src/                 # React + Vite 前端
  dist/                # 构建产物（由 Actions 生成，不手动编辑）

.github/workflows/
  weekly-mining.yml    # 定时任务

.env.example           # 密钥模板
.gitignore
```

## 💰 成本

- DeepSeek API：每次全量跑约 ¥8-10，每周一次 → 每月约 ¥40
- GitHub Actions：公开 repo 免费
- GitHub Pages：免费

## 🔧 调参速记

| 参数 | 默认 | 含义 | 调高 | 调低 |
|------|------|------|------|------|
| `Step 6 distance-threshold` | 0.42 | 聚类松紧 | 簇更大更粗 | 簇更小更细 |
| `Step 8 sim` | 0.82 | 合并相似阈值 | 合得少 | 合得多 |
| `Step 10 SIM_THRESHOLD` | 0.85 | 新旧需求是否判同 | 更少并入 | 更多并入 |

## 📚 设计笔记

- Prompts 都在各自 Step 脚本里，修改后下次重跑即生效
- 前端展示标签（功能缺失/体验问题/平台策略）与后端 `demand_type` 字段一一对应
- 本周新增识别通过 `is_new` + `discovered_at` 两个字段，超过 7 天自动降级
- 产品名优先从 `product_breakdown` 取（精确计数），回退到 `evidence_samples.app_name`
- 前端做了"杂簇" post-filter（主产品<40% + 产品数>6 直接隐藏）
