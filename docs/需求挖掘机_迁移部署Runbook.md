# 需求挖掘机 · 迁移部署 Runbook

> 拿到这份文档和项目目录就能从零部署起来的操作手册。

---

## 一、项目结构（需要带走的文件）

```
user-pain-dashboard/            (主项目)
├── scripts/                     ← 核心算法脚本（10 个 pipeline + 3 个 crawler）
│   ├── crawl_appstore.py
│   ├── crawl_googleplay.py
│   ├── crawl_hackernews.py
│   ├── crawl_incremental.py
│   ├── pipeline_step1_4.py
│   ├── pipeline_step5_atoms.py
│   ├── pipeline_step6_cluster.py
│   ├── pipeline_step7_label.py
│   ├── pipeline_step8_merge.py
│   ├── pipeline_step8_5_dedup.py     (可选)
│   ├── pipeline_step8_6_refine.py
│   ├── pipeline_step9_dashboard.py
│   └── pipeline_step10_merge_new.py  (自动化模式用)
├── data/
│   └── processed/
│       └── *_ai_opportunities_consolidated.json  ← Dashboard 直接读
├── src/                         ← React 前端
├── package.json / vite.config.ts
└── tsconfig.json

.github/workflows/
└── weekly-mining.yml            ← 定时自动化

.env.example
.gitignore
README.md
```

**必须一起带走**：`user-pain-dashboard/scripts/`、`user-pain-dashboard/src/`、`user-pain-dashboard/package.json`、`user-pain-dashboard/vite.config.ts`、`.github/`、`.env.example`、`.gitignore`、`README.md`

**可选带走**：`user-pain-dashboard/data/processed/*_ai_opportunities_consolidated.json`（带上的话部署后立刻可看当前结果；不带的话要跑一遍 pipeline）

**不要带走**：`user-pain-dashboard/node_modules/`、`user-pain-dashboard/data/raw/`、`user-pain-dashboard/data/processed/*_atoms.json / *_candidates.json` 这些中间产物

---

## 二、本地开发环境

### 2.1 运行时要求

- **Python 3.10+**（3.11 推荐）
- **Node 22+**
- **macOS / Linux**（Windows 未测试，建议 WSL）

### 2.2 装依赖

```bash
# Node
cd user-pain-dashboard
npm install

# Python
pip install sentence-transformers scikit-learn numpy scipy requests
```

首次运行 Step 6 聚类时，会自动下载 BGE 模型到 `~/.cache/huggingface/`（约 100MB，一次性）。

### 2.3 配密钥

```bash
cp .env.example .env
# 编辑 .env，填入：
# DEEPSEEK_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxx
```

DeepSeek API 注册地址：https://platform.deepseek.com/

### 2.4 启动前端

```bash
cd user-pain-dashboard
npm run dev
# 打开 http://localhost:5173/
```

---

## 三、数据管线运行

### 3.1 手动全量跑

```bash
cd user-pain-dashboard

# Step 0：抓取（需要 1-2 小时，取决于网速）
python3 scripts/crawl_incremental.py --days 365 --category all

# Step 1-9：循环跑四赛道
for cat in wechat social ai more; do
  echo "=== $cat ==="
  python3 scripts/pipeline_step1_4.py --category $cat
  python3 scripts/pipeline_step5_atoms.py --category $cat         # 最耗时 + 花钱
  python3 scripts/pipeline_step6_cluster.py --category $cat --distance-threshold 0.42
  python3 scripts/pipeline_step7_label.py --category $cat
  python3 scripts/pipeline_step8_merge.py --category $cat --sim 0.82
  # 可选 Step 8.5（仅 social 有效，其他赛道跳过）：
  # python3 scripts/pipeline_step8_5_dedup.py --category $cat
  python3 scripts/pipeline_step8_6_refine.py --category $cat
  python3 scripts/pipeline_step9_dashboard.py --category $cat
done
```

**典型耗时**：
- 抓取：~60 分钟（带重试）
- Step 5 × 4 赛道：~25 分钟（并发 20、约 10,000 原子）
- Step 6-9：约 10 分钟
- **合计**：30-40 分钟（不含抓取）

**典型费用**：¥8-10 / 次

### 3.2 Checkpoint 与断点续跑

`pipeline_step5_atoms.py` 自动把进度写到 `data/processed/{cat}_atoms.checkpoint.json`，中途中断可直接重跑，从断点继续。

其他步骤都是幂等的（每次重新读上一步的 JSON）。

### 3.3 参数速查

| 脚本 | 关键参数 | 默认值 |
|------|----------|--------|
| `pipeline_step1_4` | 无 | — |
| `pipeline_step5_atoms` | `--concurrency` | 20 |
| `pipeline_step6_cluster` | `--distance-threshold` | **0.42** |
| `pipeline_step7_label` | 无 | — |
| `pipeline_step8_merge` | `--sim` | **0.82** |
| `pipeline_step8_5_dedup` | `--batch-size` | 30 |
| `pipeline_step9_dashboard` | `--category` | required |
| `pipeline_step10_merge_new` | `--new-expire-days` | 7 |

---

## 四、首次上线到 GitHub Pages

### 4.1 创建 GitHub repo

1. https://github.com/new
2. Repository name: `user-pain-dashboard`（或你喜欢的名字）
3. Public
4. **不勾选** "Add a README"（项目里有了）
5. Create

### 4.2 推代码

```bash
cd /path/to/project
git init
git add .
git commit -m "initial commit"
git branch -M main
git remote add origin git@github.com:<你的用户名>/<repo名>.git
git push -u origin main
```

### 4.3 配置 GitHub Secrets

Repo 页面 → Settings → Secrets and variables → Actions → **New repository secret**

添加：
- **Name**: `DEEPSEEK_API_KEY`
- **Value**: `sk-xxx...`（你的 DeepSeek Key）

### 4.4 启用 GitHub Pages

Settings → Pages：

- **Source**: `Deploy from a branch`
- **Branch**: `gh-pages`（首次跑完 Actions 才会出现此分支；暂时没有的话先用 main/docs 占位）
- Save

### 4.5 首次触发 Actions

Actions 标签页 → 选 "Weekly Demand Mining" → Run workflow → Run（会手动跑一次）

首次约 60-90 分钟（装依赖 + 下 embedding 模型 + 跑完整管线）。

跑完后：
- `gh-pages` 分支自动创建，里面是构建产物
- 回到 Settings → Pages 选 `gh-pages` → 保存
- 几分钟后访问：`https://<你的用户名>.github.io/<repo名>/`

---

## 五、定时任务

`.github/workflows/weekly-mining.yml` 已配置：

```yaml
on:
  schedule:
    - cron: '0 23 * * 0'   # UTC 周日 23:00 = 北京周一 07:00
  workflow_dispatch:        # 支持手动触发
```

如需改时间：
- **改频率**：`'0 23 * * *'` 每天；`'0 23 * * 1,4'` 周一/周四
- **改时区**：cron 只支持 UTC，换算后填

---

## 六、排障（常见问题）

### Q1：Step 5 中途失败或卡死？
A：删掉 checkpoint 文件重跑，或 `tail -f data/processed/*atoms.checkpoint.json` 看进度
```bash
rm data/processed/{cat}_atoms.checkpoint.json
python3 scripts/pipeline_step5_atoms.py --category {cat}
```

### Q2：某个赛道结果为 0 个需求点？
A：候选池太小了。看 `data/processed/{cat}_candidates.json` 的 `stats.candidate_total`：
- < 50 → Step 5 不会产出多少原子，考虑放宽 Step 1-4 的 min_score
- < 200 → 正常但结果数会少

### Q3：HN 数据太吵？
A：编辑 `scripts/pipeline_step1_4.py` 的 `TOPIC_KEYWORDS` 字典，给对应赛道加关键词或改 `is_on_topic` 逻辑

### Q4：聚类颗粒度不对？
A：调 Step 6 的 `--distance-threshold`：
- 想更粗：往 0.50 调
- 想更细：往 0.35 调
- 然后 Step 7-9 要重跑

### Q5：打标分类不对？
A：编辑 `scripts/pipeline_step7_label.py` 的 `PROMPT_TEMPLATE`，加更多边界案例到 demand_type 判定规则里

### Q6：前端白屏？
A：可能 JSON 格式错。开浏览器 Console 看报错，一般是 demand_type 字段缺失导致 TypeScript 类型错误

### Q7：GitHub Actions 报 API key 无效？
A：检查 Secrets 有没有多余空格/换行，注意是在 repo 级 Settings，不是账号级

---

## 七、资产迁移 Checklist

搬到新机器前先打包：

```bash
# 打包核心代码 + 当前数据
tar czf user-pain-dashboard-$(date +%Y%m%d).tar.gz \
  user-pain-dashboard/scripts \
  user-pain-dashboard/src \
  user-pain-dashboard/package.json \
  user-pain-dashboard/package-lock.json \
  user-pain-dashboard/tsconfig*.json \
  user-pain-dashboard/vite.config.ts \
  user-pain-dashboard/index.html \
  user-pain-dashboard/tailwind.config.js \
  user-pain-dashboard/postcss.config.js \
  user-pain-dashboard/public \
  user-pain-dashboard/data/processed/*_ai_opportunities_consolidated.json \
  .github \
  .env.example \
  .gitignore \
  README.md \
  docs/需求挖掘机_总览与调试历史.md \
  docs/需求挖掘机_迁移部署Runbook.md
```

迁移后：
```bash
tar xzf user-pain-dashboard-*.tar.gz
cp .env.example .env
# 编辑 .env 填密钥
cd user-pain-dashboard
npm install
npm run dev
```

---

## 八、当前部署方案对比

| 方案 | 上线时间 | 维护成本 | 适合谁 |
|------|---:|---:|------|
| **GitHub Pages + Actions** | 1 小时 | 零 | 长期稳定运营，需要自动化 |
| **Vercel（手动上传）** | 5 分钟 | 每周手动 | 临时 demo、不想配 Actions |
| **Cloudflare Pages** | 10 分钟 | 低 | 想要国内 CDN |
| **自建 VPS + crontab** | 30 分钟 | 中 | 数据敏感、不想上云 |

---

## 九、联系与归档

- 本项目核心代码 & 调试笔记：`/Users/doudou/WorkBuddy/20260421111045/`
- memory 记录：`.workbuddy/memory/2026-04-*.md`
- 设计演进笔记：`docs/*.md`（调试过程产物）
- 最终呈现 JSON：`user-pain-dashboard/data/processed/*_ai_opportunities_consolidated.json`

*最后更新：2026-04-29*
