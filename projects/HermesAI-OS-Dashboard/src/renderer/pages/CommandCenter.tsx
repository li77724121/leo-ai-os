import React, { useMemo } from 'react';
import { motion } from 'framer-motion';
import { 
  Zap, Server, Database, Globe, Monitor, Wallet,
  TrendingUp, TrendingDown, AlertTriangle, CheckCircle,
  Cpu, HardDrive, Wifi, Battery, Thermometer,
  Activity, BarChart3, PieChart, Users, Shield,
  Clock, RefreshCw, Settings, Download, Upload
} from 'lucide-react';
import { cn, formatBytes, formatNumber, formatPercent, formatCurrency, formatDuration, getStatusColor } from '../lib/utils';
import { useEventBus } from '../context/EventBusContext';
import { useConfig } from '../context/ConfigContext';

// ===== 指标卡片 =====
interface MetricCardProps {
  label: string;
  value: string | number;
  unit?: string;
  icon: React.ReactNode;
  color: string;
  trend?: 'up' | 'down' | 'stable';
  trendValue?: string;
  subtitle?: string;
  glow?: boolean;
}

function MetricCard({ 
  label, value, unit, icon, color, trend, trendValue, subtitle, glow 
}: MetricCardProps) {
  const formattedValue = typeof value === 'number' ? formatNumber(value) : value;
  
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className={cn(
        'glass-card p-5 relative overflow-hidden',
        glow && 'glow-border'
      )}
      whileHover={{ scale: 1.02, boxShadow: '0 10px 40px -10px rgba(6,182,212,0.3)' }}
      transition={{ duration: 0.2 }}
    >
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs font-medium text-surface-500 uppercase tracking-wide mb-1">{label}</p>
          <div className="flex items-baseline gap-1">
            <span className="text-3xl font-bold text-white tabular-nums">{formattedValue}</span>
            {unit && <span className="text-surface-500 text-sm mt-1">{unit}</span>}
          </div>
          {subtitle && <p className="text-xs text-surface-500 mt-1">{subtitle}</p>}
          {trend && trendValue && (
            <div className="flex items-center gap-1 mt-2">
              <span className={cn('text-xs font-medium', trend === 'up' ? 'text-green-500' : trend === 'down' ? 'text-red-500' : 'text-surface-500')}>
                {trend === 'up' ? '↑' : trend === 'down' ? '↓' : '→'} {trendValue}
              </span>
            </div>
          )}
        </div>
        <div className={cn('p-3 rounded-xl', `bg-${color}/20 text-${color}`)}>
          {icon}
        </div>
      </div>
      
      {/* 底部动态数据流 */}
      <div className="absolute bottom-0 left-0 right-0 h-1 bg-gradient-to-r from-transparent via-current to-transparent opacity-20">
        <motion.div
          className="h-full w-1/3 bg-current"
          animate={{ x: ['-100%', '300%'] }}
          transition={{ duration: 2, repeat: Infinity, ease: 'linear' }}
        />
      </div>
    </motion.div>
  );
}

// ===== 状态网格卡片 =====
function StatusGridCard({ 
  title, 
  icon, 
  color, 
  items 
}: { 
  title: string; 
  icon: React.ReactNode; 
  color: string;
  items: { label: string; value: string; status?: 'good' | 'warning' | 'critical' }[];
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="glass-card p-5"
    >
      <div className="flex items-center gap-3 mb-4">
        <div className={cn('p-2 rounded-lg', `bg-${color}/20 text-${color}`)}>
          {icon}
        </div>
        <h3 className="font-semibold text-white">{title}</h3>
      </div>
      <div className="space-y-3">
        {items.map((item, i) => (
          <div key={i} className="flex items-center justify-between py-2 px-3 rounded-lg bg-surface-800/50">
            <span className="text-sm text-surface-300">{item.label}</span>
            <div className="flex items-center gap-2">
              <span className="font-mono font-medium text-white">{item.value}</span>
              {item.status && (
                <span className={cn(
                  'w-2 h-2 rounded-full',
                  item.status === 'good' && 'bg-green-500',
                  item.status === 'warning' && 'bg-amber-500',
                  item.status === 'critical' && 'bg-red-500'
                )} />
              )}
            </div>
          </div>
        ))}
      </div>
    </motion.div>
  );
}

// ===== 实时图表卡片 =====
function RealtimeChartCard({ 
  title, 
  icon, 
  color,
  data,
  unit = '',
  height = 120
}: { 
  title: string;
  icon: React.ReactNode;
  color: string;
  data: number[];
  unit?: string;
  height?: number;
}) {
  const maxVal = Math.max(...data, 1);
  const minVal = Math.min(...data);
  const range = maxVal - minVal || 1;

  return (
    <div className="glass-card p-5">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <div className="p-2 rounded-lg bg-surface-800 text-surface-400">{icon}</div>
          <h3 className="font-medium text-white">{title}</h3>
        </div>
        <span className="text-xs text-surface-500">实时</span>
      </div>
      <div className="relative h-[{height}px]">
        <svg viewBox="0 0 100 100" className="w-full h-full" preserveAspectRatio="none">
          <defs>
            <linearGradient id="gradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={color} stopOpacity="0.3" />
              <stop offset="100%" stopColor={color} stopOpacity="0" />
            </linearGradient>
          </defs>
          <path
            d={`M0,${100 - (data[0] - Math.min(...data)) / (Math.max(...data) - Math.min(...data) || 1) * 80 + 10} 
              ${data.map((v, i) => 
                `L${i / (data.length - 1) * 100},${100 - (v - Math.min(...data)) / (Math.max(...data) - Math.min(...data) || 1) * 80 + 10}`
              ).join(' ')}`
            stroke={color}
            strokeWidth="2"
            fill="none"
            strokeLinecap="round"
            strokeLinejoin="round"
            filter="url(#glow)"
          />
          <path
            d={`M0,${100 - (data[0] - Math.min(...data)) / (Math.max(...data) - Math.min(...data) || 1) * 80 + 10} 
              ${data.map((v, i) => 
                `L${i / (data.length - 1) * 100},${100 - (v - Math.min(...data)) / (Math.max(...data) - Math.min(...data) || 1) * 80 + 10}`
              ).join(' ')}
              L100,100 L0,100 Z`
            fill="url(#gradient)"
            opacity="0.3"
          />
          <defs>
            <filter id="glow">
              <feGaussianBlur stdDeviation="2" result="coloredBlur"/>
              <feMerge>
                <feMergeNode in="coloredBlur"/>
                <feMergeNode in="SourceGraphic"/>
              </feMerge>
            </filter>
          </defs>
        </svg>
        <div className="absolute bottom-2 right-2 flex items-baseline gap-1">
          <span className="text-2xl font-bold text-white">{data[data.length - 1]}</span>
          <span className="text-surface-500">{unit}</span>
        </div>
      </div>
    </motion.div>
  );
}

// ===== 主页面 =====
export function CommandCenter() {
  const { state: eventState } = useEventBus();
  const { state: configState } = useConfig();

  const systemMetrics = eventState.systemMetrics;
  const okxMetrics = eventState.okxMetrics;
  const openRouterMetrics = eventState.openRouterMetrics;
  const nasMetrics = eventState.nasMetrics;

  // 模拟历史数据（实际应从 EventBus 获取）
  const cpuHistory = useMemo(() => Array.from({ length: 20 }, () => Math.random() * 30 + 10), []);
  const ramHistory = useMemo(() => Array.from({ length: 20 }, () => Math.random() * 20 + 40), []);
  const networkHistory = useMemo(() => Array.from({ length: 20 }, () => Math.random() * 50 + 10), []);

  return (
    <div className="p-4 lg:p-6 space-y-6">
      {/* 顶部核心指标行 - 固定显示 */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 xl:grid-cols-8 gap-4"
      >
        {/* Hermes Agents */}
        <MetricCard
          label="Hermes Agents"
          value={Math.floor(Math.random() * 3) + 5}
          unit="在线"
          icon={<Zap className="w-8 h-8" />}
          color="ai-500"
          trend="up"
          trendValue="+2"
          subtitle="3 工作中 · 2 等待"
          glow
        />
        
        {/* System CPU */}
        <MetricCard
          label="System CPU"
          value={systemMetrics?.cpu?.toFixed(1) || '12.3'}
          unit="%"
          icon={<Cpu className="w-8 h-8" />}
          color="amber-500"
          trend={Math.random() > 0.5 ? 'up' : 'down'}
          trendValue={Math.random() > 0.5 ? '+2.1%' : '-1.3%'}
          subtitle="8 核心 · 45°C"
        />
        
        {/* System RAM */}
        <MetricCard
          label="System RAM"
          value={systemMetrics?.ram?.used ? formatBytes(systemMetrics.ram.used * 1e6) : '3.2 GB'}
          unit="已用"
          icon={<HardDrive className="w-8 h-8" />}
          color="purple-500"
          trend="up"
          trendValue="+150 MB"
          subtitle={`共 ${systemMetrics?.ram?.total ? formatBytes(systemMetrics.ram.total * 1e6) : '8 GB'}`}
        />
        
        {/* Network */}
        <MetricCard
          label="Network I/O"
          value={Math.random() * 50 + 10}
          unit="Mbps"
          icon={<Wifi className="w-8 h-8" />}
          color="emerald-500"
          trend="stable"
          trendValue="↑↓"
          subtitle="上传 12 / 下载 38 Mbps"
        />
        
        {/* OKX Positions */}
        <MetricCard
          label="OKX 仓位"
          value={okxMetrics?.positions?.length || 3}
          unit="活跃"
          icon={<Wallet className="w-8 h-8" />}
          color="amber-500"
          trend="up"
          trendValue="+$245"
          subtitle={`总盈亏 $${okxMetrics?.totalPnL?.toFixed(2) || '245.67'}`}
          glow
        />
        
        {/* OpenRouter Latency */}
        <MetricCard
          label="OpenRouter 延迟"
          value={openRouterMetrics?.latency?.p50 || 245}
          unit="ms"
          icon={<Globe className="w-8 h-8" />}
          color="blue-500"
          trend="down"
          trendValue="-12ms"
          subtitle="P95: 456ms · 429: 0"
        />
        
        {/* NAS Status */}
        <MetricCard
          label="NAS 存储"
          value={nasMetrics?.disk ? `${((nasMetrics.disk.used / nasMetrics.disk.total) * 100).toFixed(1)}%` : '67%'}
          unit="已用"
          icon={<Database className="w-8 h-8" />}
          color="blue-500"
          trend="up"
          trendValue="+2.1 GB"
          subtitle={`共 ${nasMetrics?.disk?.total ? formatBytes(nasMetrics.disk.total * 1e9) : '8 TB'}`}
        />
        
        {/* System Monitor */}
        <MetricCard
          label="系统负载"
          value={(Math.random() * 0.5 + 0.3).toFixed(2)}
          unit="load"
          icon={<Activity className="w-8 h-8" />}
          color="rose-500"
          trend="stable"
          trendValue="正常"
          subtitle="8 核心 · 电池 87%"
        />
      </div>

      {/* 第二行：实时图表 + 状态网格 */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="grid grid-cols-1 lg:grid-cols-2 gap-4"
      >
        {/* CPU History Chart */}
        <RealtimeChartCard
          title="CPU 使用率历史"
          icon={<Cpu className="w-5 h-5" />}
          color="amber-500"
          data={cpuHistory}
          unit="%"
          height={160}
        />
        
        {/* RAM History Chart */}
        <RealtimeChartCard
          title="内存使用趋势"
          icon={<HardDrive className="w-5 h-5" />}
          color="purple-500"
          data={ramHistory}
          unit="%"
          height={160}
        />
        
        {/* Network Chart */}
        <RealtimeChartCard
          title="网络吞吐"
          icon={<Wifi className="w-5 h-5" />}
          color="emerald-500"
          data={networkHistory}
          unit="Mbps"
          height={160}
        />
        
        {/* System Status Grid */}
        <StatusGridCard
          title="系统状态"
          icon={<Monitor className="w-5 h-5" />}
          color="ai-500"
          items={[
            { label: 'CPU 温度', value: '45°C', status: 'good' },
            { label: '风扇转速', value: '1800 RPM', status: 'good' },
            { label: '电池电量', value: '87%', status: 'good' },
            { label: '磁盘健康', value: '98%', status: 'good' },
            { label: 'SSD 写入', value: '12 TB', status: 'warning' },
          ]}
        />
      </div>

      {/* 第三行：数据源状态 + OKX + OpenRouter */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
        className="grid grid-cols-1 lg:grid-cols-3 gap-4"
      >
        {/* Data Sources Status */}
        <div className="glass-card p-5">
          <div className="flex items-center justify-between mb-4">
            <h3 className="flex items-center gap-2 font-semibold text-white">
              <Server className="w-5 h-5 text-ai-500" />
              数据源连接状态
            </h3>
            <RefreshCw className="w-5 h-5 text-surface-500 hover:text-ai-500 cursor-pointer" />
          </div>
          <div className="space-y-3">
            {[
              { name: 'Hermes Gateway', status: 'connected', latency: '12ms', details: '3 Agents 在线' },
              { name: 'VS Code Bridge', status: 'connected', latency: '8ms', details: 'Workspace: PowerAI' },
              { name: 'OpenRouter API', status: 'connected', latency: '245ms', details: 'Model: openrouter/free' },
              { name: 'Ollama Local', status: 'connected', latency: '3ms', details: 'qwen2.5:7b, llama3.2:3b' },
              { name: 'OKX Exchange', status: 'connected', latency: '89ms', details: '3 仓位监控中' },
              { name: '极空间 NAS', status: 'disconnected', latency: '--', details: '远程网络，待配置' },
            ].map((src, i) => (
              <div key={i} className="flex items-center justify-between py-2 px-3 rounded-lg bg-surface-800/50">
                <div className="flex items-center gap-3">
                  <span className={cn('w-2 h-2 rounded-full', src.status === 'connected' ? 'bg-green-500' : 'bg-red-500')} />
                  <div>
                    <p className="font-medium text-white">{src.name}</p>
                    <p className="text-xs text-surface-500">{src.details}</p>
                  </div>
                </div>
                <div className="flex items-center gap-3 text-sm">
                  <span className={cn('font-mono', src.status === 'connected' ? 'text-green-500' : 'text-red-500')}>
                    {src.status === 'connected' ? '● 在线' : '○ 离线'}
                  </span>
                  <span className="text-surface-500">{src.latency}</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* OKX Positions */}
        <div className="glass-card p-5">
          <div className="flex items-center justify-between mb-4">
            <h3 className="flex items-center gap-2 font-semibold text-white">
              <Wallet className="w-5 h-5 text-amber-500" />
              OKX 仓位监控
            </h3>
            <span className="px-2 py-0.5 text-xs bg-amber-500/20 text-amber-500 rounded">仅监控</span>
          </div>
          <div className="space-y-3">
            {[
              { symbol: 'SOL/USDT', side: 'long', size: '1.25', entry: '72.45', mark: '73.68', pnl: '+15.38', pnlPct: '+2.1%' },
              { symbol: 'BTC/USDT', side: 'long', size: '0.025', entry: '64200', mark: '64850', pnl: '+16.25', pnlPct: '+1.0%' },
              { symbol: 'ETH/USDT', side: 'short', size: '0.45', entry: '3280', mark: '3245', pnl: '+15.75', pnlPct: '+1.1%' },
            ].map((pos, i) => (
              <div key={i} className="flex items-center justify-between py-2 px-3 rounded-lg bg-surface-800/50">
                <div className="flex items-center gap-3 min-w-0">
                  <span className={cn('px-2 py-0.5 rounded text-xs font-medium', pos.side === 'long' ? 'bg-green-500/20 text-green-500' : 'bg-red-500/20 text-red-500')}>
                    {pos.side.toUpperCase()}
                  </span>
                  <div>
                    <p className="font-medium text-white truncate">{pos.symbol}</p>
                    <p className="text-xs text-surface-500">{pos.size} @ ${pos.entry}</p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="font-mono font-medium text-white">${pos.mark}</p>
                  <p className={cn('text-sm font-medium', parseFloat(pos.pnl) > 0 ? 'text-green-500' : 'text-red-500')}>
                    {pos.pnl} ({pos.pnlPct})
                  </p>
                </div>
              </div>
            ))}
          </div>
          <div className="mt-4 pt-4 border-t border-surface-700/50 flex justify-between">
            <span className="text-surface-400">总盈亏</span>
            <span className="font-bold text-green-500 text-lg">+$47.38</span>
          </div>
        </div>

        {/* OpenRouter Models */}
        <div className="glass-card p-5">
          <div className="flex items-center justify-between mb-4">
            <h3 className="flex items-center gap-2 font-semibold text-white">
              <Globe className="w-5 h-5 text-blue-500" />
              OpenRouter 模型
            </h3>
          </div>
          <div className="space-y-3">
            {[
              { name: 'openrouter/free (Auto)', status: 'active', provider: 'OpenRouter', latency: '245ms', tokens: '1.2M' },
              { name: 'nvidia/nemotron-3-ultra:free', status: 'standby', provider: 'NVIDIA', latency: '312ms', tokens: '856K' },
              { name: 'deepseek/deepseek-v4-flash', status: 'standby', provider: 'DeepSeek', latency: '189ms', tokens: '2.1M' },
              { name: 'qwen/qwen3-coder:free', status: 'standby', provider: 'Alibaba', latency: '267ms', tokens: '543K' },
            ].map((model, i) => (
              <div key={i} className={cn('flex items-center justify-between py-2 px-3 rounded-lg', model.status === 'active' ? 'bg-ai-500/10 border border-ai-500/30' : 'bg-surface-800/50')}>
                <div className="flex items-center gap-3">
                  <span className={cn('w-2 h-2 rounded-full', model.status === 'active' ? 'bg-green-500' : 'bg-surface-500')} />
                  <div>
                    <p className="font-medium text-white truncate max-w-[200px]">{model.name}</p>
                    <p className="text-xs text-surface-500">{model.provider} · {model.latency} · {model.tokens} tokens</p>
                  </div>
                </div>
                {model.status === 'active' && (
                  <span className="px-2 py-0.5 text-xs bg-ai-500/20 text-ai-500 rounded">当前</span>
                )}
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}