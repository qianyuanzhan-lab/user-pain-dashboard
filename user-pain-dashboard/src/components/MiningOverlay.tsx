import React, { useState, useEffect, useRef } from 'react';
import { CHANNEL_CRAWL_STATS } from '../data/dashboardData';

interface MiningOverlayProps {
  onComplete: () => void;
  onError: (error: string) => void;
}

// 真实数据源配置
const DATA_CHANNELS = [
  { id: 'hackernews', name: 'Hacker News', desc: '科技社区讨论' },
  { id: 'appstore', name: 'App Store', desc: 'iOS 用户评价' },
  { id: 'googleplay', name: 'Google Play', desc: 'Android 用户评价' },
];

function getActiveChannels() {
  const activeChannels: { id: string; name: string; desc: string; count: number }[] = [];
  
  for (const channel of DATA_CHANNELS) {
    const stats = CHANNEL_CRAWL_STATS.channels.find(c => c.id === channel.id);
    if (stats && stats.count > 0) {
      activeChannels.push({
        ...channel,
        count: stats.count,
      });
    }
  }
  
  activeChannels.sort((a, b) => b.count - a.count);
  return activeChannels;
}

function getTotalReviews(): number {
  return CHANNEL_CRAWL_STATS.totalReviews;
}

// 线稿风格挖掘机 SVG（深灰描边、无填充，履带底部完全贴着底边，无空白）
// viewBox 裁剪到 y=10 到 y=68，车轮底部 y=68 贴着 viewBox 底边
function Excavator({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 10 120 58" fill="none" xmlns="http://www.w3.org/2000/svg">
      <g stroke="#374151" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" fill="none">
        {/* 履带外框 - 底部贴着 y=68 */}
        <path d="M20 68 C12 68 8 62 8 56 C8 50 12 44 20 44 L58 44 C66 44 70 50 70 56 C70 62 66 68 58 68 Z" />
        {/* 履带轮子 */}
        <circle cx="20" cy="56" r="6" />
        <circle cx="39" cy="56" r="6" />
        <circle cx="58" cy="56" r="6" />
        
        {/* 车身底座 */}
        <rect x="14" y="32" width="50" height="14" rx="2" />
        
        {/* 发动机舱 */}
        <rect x="44" y="20" width="18" height="14" rx="2" />
        {/* 排气管 */}
        <rect x="48" y="12" width="4" height="10" rx="1" />
        
        {/* 驾驶室 */}
        <rect x="22" y="14" width="20" height="20" rx="2" />
        {/* 窗户 */}
        <rect x="25" y="17" width="14" height="10" rx="1" />
        
        {/* 大臂（从驾驶室顶部向右上伸出） */}
        <path d="M42 20 L78 8 L82 12 L46 26" strokeWidth="3" />
        
        {/* 小臂（从大臂末端向下弯曲） */}
        <path d="M80 10 L100 36 L96 40 L76 16" strokeWidth="3" />
        
        {/* 铲斗 */}
        <path d="M98 38 Q108 42 112 54 Q108 58 100 56 L92 44 Z" strokeWidth="2.5" />
        {/* 铲斗开口 */}
        <path d="M100 56 Q96 62 92 58" strokeWidth="2" />
        
        {/* 液压缸（大臂上） */}
        <line x1="36" y1="28" x2="60" y2="18" strokeWidth="1.5" />
        <line x1="34" y1="30" x2="58" y2="20" strokeWidth="1.5" />
        
        {/* 液压缸（小臂上） */}
        <line x1="70" y1="20" x2="88" y2="38" strokeWidth="1.5" />
      </g>
    </svg>
  );
}

/**
 * 全屏挖掘动效组件
 * 动效时长：3 秒，使用 CSS transition 而非 setInterval
 */
export function MiningOverlay({ onComplete, onError }: MiningOverlayProps) {
  const [phase, setPhase] = useState<'init' | 'mining' | 'done' | 'error'>('init');
  const [errorMsg, setErrorMsg] = useState('');
  const [channelIndex, setChannelIndex] = useState(0);
  const [displayCount, setDisplayCount] = useState(0); // 数字递增动画
  
  const totalReviews = useRef(getTotalReviews()).current;
  const activeChannels = useRef(getActiveChannels()).current;
  const animationDuration = 3000; // 3秒

  useEffect(() => {
    // 尝试连接后端
    const eventSource = new EventSource('http://localhost:3001/api/mine/progress');
    let useLocal = false;

    const startMining = () => {
      setPhase('mining');
      
      // 数字递增动画：从 0 逐渐增长到 totalReviews
      const countSteps = 30; // 分 30 步递增
      const countInterval = animationDuration / countSteps;
      let step = 0;
      const countTimer = setInterval(() => {
        step++;
        // 使用 easeOut 效果：前快后慢
        const progress = step / countSteps;
        const eased = 1 - Math.pow(1 - progress, 3);
        setDisplayCount(Math.floor(eased * totalReviews));
        if (step >= countSteps) {
          clearInterval(countTimer);
          setDisplayCount(totalReviews);
        }
      }, countInterval);
      
      // 切换渠道名称（每秒切换一次）
      const channelTimer = setInterval(() => {
        setChannelIndex(prev => {
          if (prev >= activeChannels.length - 1) {
            clearInterval(channelTimer);
            return prev;
          }
          return prev + 1;
        });
      }, animationDuration / activeChannels.length);
      
      // 3秒后完成
      setTimeout(() => {
        setPhase('done');
        clearInterval(channelTimer);
        clearInterval(countTimer);
        setDisplayCount(totalReviews);
        setTimeout(onComplete, 600);
      }, animationDuration);
    };

    eventSource.onopen = () => {
      fetch('http://localhost:3001/api/mine')
        .then(res => res.json())
        .then(data => {
          if (data.status === 'cached') {
            setPhase('done');
            setTimeout(onComplete, 400);
            eventSource.close();
          }
        })
        .catch(() => {
          useLocal = true;
          startMining();
        });
    };

    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type === 'complete') {
          setPhase('done');
          setTimeout(onComplete, 400);
          eventSource.close();
        } else if (data.type === 'error') {
          setPhase('error');
          setErrorMsg(data.message);
          onError(data.message);
          eventSource.close();
        }
      } catch (e) {
        console.error('Parse SSE error:', e);
      }
    };

    eventSource.onerror = () => {
      if (!useLocal) {
        useLocal = true;
        eventSource.close();
        startMining();
      }
    };

    return () => {
      eventSource.close();
    };
  }, [onComplete, onError, activeChannels.length]);

  const currentChannel = activeChannels[channelIndex];

  return (
    <div className="fixed inset-0 bg-stone-50 z-50 flex items-center justify-center">
      <div className="text-center max-w-md px-6">
        
        {/* 主文案 */}
        <h1 className="text-xl font-medium text-stone-700 mb-8">
          {phase === 'done' ? '准备好了' : '正在挖掘用户需求'}
        </h1>

        {/* 挖掘阶段：当前数据源 */}
        {(phase === 'init' || phase === 'mining') && currentChannel && (
          <div className="mb-6 h-6">
            <div className="flex items-center justify-center gap-2">
              <span className="text-stone-600 font-medium">{currentChannel.name}</span>
              <span className="text-stone-300">·</span>
              <span className="text-stone-400 text-sm">{currentChannel.desc}</span>
            </div>
          </div>
        )}

        {/* 完成阶段 */}
        {phase === 'done' && (
          <div className="mb-6">
            <div className="w-12 h-12 mx-auto bg-emerald-50 rounded-full flex items-center justify-center">
              <svg className="w-6 h-6 text-emerald-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
              </svg>
            </div>
            <p className="text-stone-400 text-sm mt-3">
              共 {totalReviews.toLocaleString()} 条真实评价
            </p>
          </div>
        )}

        {/* 挖掘机 + 进度条（车轮底部贴着进度条） */}
        {phase !== 'done' && phase !== 'error' && (
          <div className="w-full max-w-xs mx-auto">
            {/* 进度条容器 */}
            <div className="relative h-12">
              {/* 进度条轨道（扁平风格） */}
              <div className="absolute bottom-0 left-0 right-0 h-1.5 bg-stone-200 rounded-full overflow-hidden">
                {/* 进度条填充 */}
                <div
                  className="absolute inset-y-0 left-0 bg-stone-400 rounded-full"
                  style={{
                    width: phase === 'mining' ? '100%' : '2%',
                    transition: phase === 'mining' ? `width ${animationDuration}ms linear` : 'none'
                  }}
                />
              </div>
              
              {/* 挖掘机（底部贴着进度条顶部，无空隙） */}
              <div 
                className="absolute"
                style={{ 
                  bottom: '6px', // 进度条高度 6px，车轮底部贴着
                  left: phase === 'mining' ? 'calc(100% - 44px)' : '0px',
                  transition: phase === 'mining' ? `left ${animationDuration}ms linear` : 'none'
                }}
              >
                <Excavator className="w-11 h-auto" />
              </div>
            </div>
            
            {/* 已读取数量 - 动态递增 */}
            <p className="text-stone-400 text-sm mt-4">
              已读取 <span className="text-stone-600 font-medium">{displayCount.toLocaleString()}</span> 条评价
            </p>
          </div>
        )}

        {/* 错误状态 */}
        {phase === 'error' && (
          <div className="mt-4 p-3 bg-red-50 rounded-lg text-red-600 text-sm">
            <p className="mb-2">{errorMsg || '加载失败'}</p>
            <button
              onClick={() => window.location.reload()}
              className="px-3 py-1.5 bg-white rounded text-red-600 text-sm border border-red-200"
            >
              重试
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
