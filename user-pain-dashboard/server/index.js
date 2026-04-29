/**
 * 需求挖掘机 - 本地后端服务
 * 
 * 功能：
 * 1. 提供 /api/mine 接口触发实时挖掘
 * 2. 调用 Python 脚本抓取 App Store 评论
 * 3. 调用 DeepSeek API 进行 AI 分析
 * 4. 缓存当天结果，避免重复挖掘
 * 
 * 环境变量：
 *   DEEPSEEK_API_KEY - DeepSeek API 密钥
 */

import express from 'express';
import cors from 'cors';
import { spawn } from 'child_process';
import fs from 'fs/promises';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const app = express();
const PORT = 3001;

// 配置
const CONFIG = {
  dataDir: path.join(__dirname, '../data'),
  scriptsDir: path.join(__dirname, '../scripts'),
  cacheFile: path.join(__dirname, '../data/cache/mining_cache.json'),
};

app.use(cors());
app.use(express.json());

// ============================================
// 工具函数
// ============================================

async function ensureDir(dirPath) {
  try {
    await fs.mkdir(dirPath, { recursive: true });
  } catch (e) {
    // ignore
  }
}

async function readCache() {
  try {
    const content = await fs.readFile(CONFIG.cacheFile, 'utf-8');
    return JSON.parse(content);
  } catch {
    return {};
  }
}

async function writeCache(data) {
  await ensureDir(path.dirname(CONFIG.cacheFile));
  await fs.writeFile(CONFIG.cacheFile, JSON.stringify(data, null, 2));
}

function getTodayKey() {
  const now = new Date();
  return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')}`;
}

// ============================================
// 挖掘流程
// ============================================

// 全局挖掘状态
let miningState = {
  isRunning: false,
  currentPhase: null,
  progress: 0,
  error: null,
  startTime: null,
};

// SSE 连接池
const sseClients = new Set();

function broadcastProgress(data) {
  const message = `data: ${JSON.stringify(data)}\n\n`;
  sseClients.forEach(client => {
    client.write(message);
  });
}

async function runPythonScript(scriptName, args = []) {
  return new Promise((resolve, reject) => {
    const scriptPath = path.join(CONFIG.scriptsDir, scriptName);
    const proc = spawn('python3', [scriptPath, ...args], {
      cwd: CONFIG.scriptsDir,
      env: { ...process.env },
    });

    let stdout = '';
    let stderr = '';

    proc.stdout.on('data', (data) => {
      stdout += data.toString();
      console.log(`[${scriptName}] ${data.toString().trim()}`);
    });

    proc.stderr.on('data', (data) => {
      stderr += data.toString();
      console.error(`[${scriptName}] ${data.toString().trim()}`);
    });

    proc.on('close', (code) => {
      if (code === 0) {
        resolve(stdout);
      } else {
        reject(new Error(`Script ${scriptName} exited with code ${code}: ${stderr}`));
      }
    });

    proc.on('error', reject);
  });
}

async function doMining() {
  const today = getTodayKey();
  
  try {
    miningState = {
      isRunning: true,
      currentPhase: 'crawling',
      progress: 0,
      error: null,
      startTime: Date.now(),
    };
    broadcastProgress({ type: 'start', date: today, phase: 'crawling' });

    // Phase 1: 抓取评论 (0-40%)
    console.log('📥 Phase 1: 抓取 App Store 评论...');
    broadcastProgress({ type: 'progress', phase: 'crawling', progress: 10, message: '正在抓取微信评论...' });
    
    await runPythonScript('crawl_appstore.py', ['--category', 'wechat']);
    broadcastProgress({ type: 'progress', phase: 'crawling', progress: 20, message: '正在抓取社交类应用评论...' });
    
    await runPythonScript('crawl_appstore.py', ['--category', 'social']);
    broadcastProgress({ type: 'progress', phase: 'crawling', progress: 30, message: '正在抓取 AI 类应用评论...' });
    
    await runPythonScript('crawl_appstore.py', ['--category', 'ai']);
    broadcastProgress({ type: 'progress', phase: 'crawling', progress: 40, message: '正在抓取更多类目评论...' });
    
    await runPythonScript('crawl_appstore.py', ['--category', 'more']);

    // Phase 2: AI 分析 (40-90%) - 使用 DeepSeek API
    console.log('🤖 Phase 2: AI 分析用户需求（DeepSeek）...');
    miningState.currentPhase = 'analyzing';
    broadcastProgress({ type: 'progress', phase: 'analyzing', progress: 50, message: 'AI 正在分析微信用户痛点...' });
    
    await runPythonScript('analyze_with_llm.py', ['--category', 'wechat', '--provider', 'deepseek']);
    broadcastProgress({ type: 'progress', phase: 'analyzing', progress: 60, message: 'AI 正在分析社交类用户痛点...' });
    
    await runPythonScript('analyze_with_llm.py', ['--category', 'social', '--provider', 'deepseek']);
    broadcastProgress({ type: 'progress', phase: 'analyzing', progress: 70, message: 'AI 正在分析 AI 类用户痛点...' });
    
    await runPythonScript('analyze_with_llm.py', ['--category', 'ai', '--provider', 'deepseek']);
    broadcastProgress({ type: 'progress', phase: 'analyzing', progress: 80, message: 'AI 正在分析更多类目用户痛点...' });
    
    await runPythonScript('analyze_with_llm.py', ['--category', 'more', '--provider', 'deepseek']);

    // Phase 3: 汇总数据 (90-100%)
    console.log('📊 Phase 3: 汇总分析结果...');
    miningState.currentPhase = 'summarizing';
    broadcastProgress({ type: 'progress', phase: 'summarizing', progress: 95, message: '正在汇总分析结果...' });

    // 读取分析结果
    const results = {};
    for (const cat of ['wechat', 'social', 'ai', 'more']) {
      const filePath = path.join(CONFIG.dataDir, 'analyzed', `${cat}_opportunities.json`);
      try {
        const content = await fs.readFile(filePath, 'utf-8');
        results[cat] = JSON.parse(content);
      } catch (e) {
        console.warn(`无法读取 ${cat} 分析结果:`, e.message);
        results[cat] = { opportunities: [] };
      }
    }

    // 更新缓存
    const cache = await readCache();
    cache[today] = {
      date: today,
      timestamp: Date.now(),
      results,
    };
    await writeCache(cache);

    miningState = {
      isRunning: false,
      currentPhase: 'done',
      progress: 100,
      error: null,
      startTime: null,
    };
    
    broadcastProgress({ type: 'complete', date: today, results });
    console.log('✅ 挖掘完成！');
    
    return { success: true, date: today, results };

  } catch (error) {
    console.error('❌ 挖掘失败:', error);
    miningState = {
      isRunning: false,
      currentPhase: 'error',
      progress: 0,
      error: error.message,
      startTime: null,
    };
    broadcastProgress({ type: 'error', message: error.message });
    return { success: false, error: error.message };
  }
}

// ============================================
// API 路由
// ============================================

// 获取挖掘状态 / 触发挖掘
app.get('/api/mine', async (req, res) => {
  const today = getTodayKey();
  const cache = await readCache();
  
  // 检查今日是否已挖掘
  if (cache[today] && !req.query.force) {
    return res.json({
      status: 'cached',
      date: today,
      results: cache[today].results,
      cachedAt: cache[today].timestamp,
    });
  }

  // 检查是否正在挖掘
  if (miningState.isRunning) {
    return res.json({
      status: 'running',
      phase: miningState.currentPhase,
      progress: miningState.progress,
    });
  }

  // 触发新挖掘（异步）
  doMining();
  
  res.json({
    status: 'started',
    date: today,
  });
});

// SSE 进度推送
app.get('/api/mine/progress', (req, res) => {
  res.setHeader('Content-Type', 'text/event-stream');
  res.setHeader('Cache-Control', 'no-cache');
  res.setHeader('Connection', 'keep-alive');

  sseClients.add(res);
  console.log(`SSE 客户端连接，当前 ${sseClients.size} 个`);

  // 发送当前状态
  if (miningState.isRunning) {
    res.write(`data: ${JSON.stringify({
      type: 'progress',
      phase: miningState.currentPhase,
      progress: miningState.progress,
    })}\n\n`);
  }

  req.on('close', () => {
    sseClients.delete(res);
    console.log(`SSE 客户端断开，剩余 ${sseClients.size} 个`);
  });
});

// 获取今日数据
app.get('/api/data', async (req, res) => {
  const today = getTodayKey();
  const cache = await readCache();
  
  if (cache[today]) {
    return res.json({
      status: 'ok',
      date: today,
      results: cache[today].results,
    });
  }

  // 无缓存，返回最近一次的数据（如果有）
  const dates = Object.keys(cache).sort().reverse();
  if (dates.length > 0) {
    const lastDate = dates[0];
    return res.json({
      status: 'stale',
      date: lastDate,
      results: cache[lastDate].results,
      note: `数据来自 ${lastDate}，今日尚未挖掘`,
    });
  }

  res.json({ status: 'empty', message: '暂无数据，请先触发挖掘' });
});

// 健康检查
app.get('/api/health', (req, res) => {
  res.json({ status: 'ok', miningState });
});

// ============================================
// 启动服务
// ============================================

app.listen(PORT, () => {
  console.log(`🚀 需求挖掘机后端服务启动: http://localhost:${PORT}`);
  console.log(`   - GET /api/mine          触发挖掘 / 获取缓存`);
  console.log(`   - GET /api/mine/progress SSE 进度推送`);
  console.log(`   - GET /api/data          获取最新数据`);
});
