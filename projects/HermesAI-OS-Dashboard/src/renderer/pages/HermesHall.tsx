import React, { useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Zap, Bot, Brain, Cpu, HardDrive, Wifi, 
  Activity, Terminal, Sparkles, Shield,
  AlertTriangle, CheckCircle, XCircle,
  RefreshCw, Filter, Search, ChevronDown
} from 'lucide-react';
import { cn, getStatusColor, formatDuration, formatNumber } from '../lib/utils';
import { useEventBus } from '../context/EventBusContext';

export function HermesHall() {
  const { state } = useEventBus();

  // 模拟 Agent 数据（实际从 EventBus 获取）
  const agents = useMemo(() => [
    {
      id: '1',
      name: 'CTO-Agent',
      role: '架构师',
      status: 'working' as const,
      model: 'nvidia/nemotron-3-ultra:free',
      provider: 'OpenRouter',
      currentTask: { name: '设计 PowerAI 微服务架构', progress: 65 },
      tokenUsage: { prompt: 12500, completion: 8900, total: 21400, cost: 0 },
      tools: [
        { name: 'code_generation', status: 'completed' },
        { name: 'file_write', status: 'running' },
        { name: 'terminal', status: 'pending' },
      ],
      metrics: { cpu: 12.5, ram: 450, callsPerMin: 8, avgLatency: 245, errorRate: 0 },
    },
    {
      id: '2',
      name: 'Dev-Agent',
      role: '后端工程师',
      status: 'working' as const,
      model: 'qwen2.5-coder:7b',
      provider: 'Ollama',
      currentTask: { name: '实现 OKX WebSocket 订阅', progress: 40 },
      tokenUsage: { prompt: 8900, completion: 12300, total: 21200, cost: 0 },
      tools: [
        { name: 'code_generation', status: 'running' },
        { name: 'test_run', status: 'pending' },
      ],
      metrics: { cpu: 8.2, ram: 320, callsPerMin: 12, avgLatency: 89, errorRate: 0 },
    },
    {
      id: '3',
      name: 'Research-Agent',
      role: '研究员',
      status: 'waiting' as const,
      model: 'deepseek/deepseek-v4-flash',
      provider: 'OpenRouter',
      currentTask: { name: '调研 RAG 最佳实践', progress: 100 },
      tokenUsage: { prompt: 5600, completion: 3400, total: 9000, cost: 0.0012 },
      tools: [],
      metrics: { cpu: 1.2, ram: 180, callsPerMin: 0, avgLatency: 0, errorRate: 0 },
    },
    {
      id: '4',
      name: 'Trading-Agent',
      role: '量化分析师',
      status: 'working' as const,
      model: 'nvidia/nemotron-3-ultra:free',
      provider: 'OpenRouter',
      currentTask: { name: '分析 SOL/USDT 网格策略', progress: 75 },
      tokenUsage: { prompt: 15600, completion: 8900, total: 24500, cost: 0 },
      tools: [
        { name: 'market_data', status: 'completed' },
        { name: 'strategy_calc', status: 'running' },
        { name: 'risk_check', status: 'completed' },
      ],
      metrics: { cpu: 15.8, ram: 520, callsPerMin: 6, avgLatency: 312, errorRate: 0 },
    },
    {
      id: '5',
      name: 'UI-Agent',
      role: '前端工程师',
      status: 'idle' as const,
      model: 'qwen2.5-coder:7b',
      provider: 'Ollama',
      currentTask: null,
      tokenUsage: { prompt: 0, completion: 0, total: 0, cost: 0 },
      tools: [],
      metrics: { cpu: 0.5, ram: 120, callsPerMin: 0, avgLatency: 0, errorRate: 0 },
    },
    {
      id: '6',
      name: 'Security-Agent',
      role: '安全审计',
      status: 'learning' as const,
      model: 'qwen2.5:7b',
      provider: 'Ollama',
      currentTask: { name: '学习最新 CVE 漏洞模式', progress: 30 },
      tokenUsage: { prompt: 23400, completion: 18900, total: 42300, cost: 0 },
      tools: [
        { name: 'web_search', status: 'running' },
        { name: 'code_analysis', status: 'pending' },
      ],
      metrics: { cpu: 25.3, ram: 680, callsPerMin: 4, avgLatency: 445, errorRate: 0.2 },
    },
  ];

  const statusCounts = useMemo(() => ({
    working: agents.filter(a => a.status === 'working').length,
    waiting: agents.filter(a => a.status === 'waiting').length,
    idle: agents.filter(a => a.status === 'idle').length,
    learning: agents.filter(a => a.status === 'learning').length,
    error: agents.filter(a => a.status === 'error').length,
  }), [agents]);

  return (
    <div className="p-4 lg:p-6 space-y-6">
      {/* 顶部统计栏 */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3"
      >
        <StatCard label="总 Agent" value={agents.length} icon={<Bot className="w-5 h-5" />} color="ai-500" />
        <StatCard label="工作中" value={statusCounts.working} icon={<Activity className="w-5 h-5" />} color="status-working" />
        <StatCard label="等待中" value={statusCounts.waiting} icon={<Clock className="w-5 h-5" />} color="status-waiting" />
        <StatCard label="空闲" value={statusCounts.idle} icon={<Shield className="w-5 h-5" />} color="status-idle" />
        <StatCard label="学习中" value={statusCounts.learning} icon={<Sparkles className="w-5 h-5" />} color="status-learning" />
        <StatCard label="错误" value={statusCounts.error} icon={<AlertTriangle className="w-5 h-5" />} color="status-error" />
      </div>

      {/* 搜索过滤栏 */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="flex flex-col sm:flex-row gap-3 items-start sm:items-center justify-between p-4 glass-card"
      >
        <div className="flex flex-col sm:flex-row gap-3 w-full sm:w-auto">
          <div className="relative w-full sm:w-72">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-surface-500" />
            <input
              type="text"
              placeholder="搜索 Agent 名称、角色、任务..."
              className="w-full pl-10 pr-4 py-2 bg-surface-800/50 border border-surface-700 rounded-lg text-white placeholder-surface-500 focus:outline-none focus:border-ai-500"
            />
          </div>
          <select className="px-4 py-2 bg-surface-800/50 border border-surface-700 rounded-lg text-white focus:outline-none focus:border-ai-500">
            <option value="all">全部状态</option>
            <option value="working">工作中</option>
            <option value="waiting">等待中</option>
            <option value="idle">空闲</option>
            <option value="learning">学习中</option>
            <option value="error">错误</option>
          </select>
          <select className="px-4 py-2 bg-surface-800/50 border border-surface-700 rounded-lg text-white focus:outline-none focus:border-ai-500">
            <option value="all">所有模型</option>
            <option value="openrouter">OpenRouter</option>
            <option value="ollama">Ollama (本地)</option>
          </select>
        </div>
        <button className="btn-secondary">
          <RefreshCw className="w-4 h-4 mr-2" />
          刷新
        </button>
      </div>

      {/* Agent 卡片网格 */}
      <AnimatePresence mode="popLayout">
        <motion.div
          key="agents-grid"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4"
        >
          {agents.map((agent) => (
            <AgentCard key={agent.id} agent={agent} />
          ))}
        </motion.div>
      </AnimatePresence>
    </div>
  );
}

function StatCard({ label, value, icon, color }: { label: string; value: number; icon: React.ReactNode; color: string }) {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      className={cn('glass-card p-4', `border-l-4 border-${color}`)}
    >
      <div className="flex items-center justify-between">
        <div>
          <p className="text-xs text-surface-500 uppercase tracking-wide">{label}</p>
          <p className="text-2xl font-bold text-white mt-1">{value}</p>
        </div>
        <div className={cn('p-2 rounded-lg', `bg-${color}/20 text-${color}`)}>
          {icon}
        </div>
      </div>
    </motion.div>
  );
}

function AgentCard({ agent }: { agent: any }) {
  const statusColor = getStatusColor(agent.status);
  const statusIcons = {
    working: <Activity className="w-4 h-4 animate-pulse" />,
    waiting: <Clock className="w-4 h-4 animate-bounce" />,
    idle: <Shield className="w-4 h-4" />,
    learning: <Sparkles className="w-4 h-4 animate-spin" />,
    error: <AlertTriangle className="w-4 h-4 animate-pulse" />,
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className={cn('glass-card p-5 relative overflow-hidden', agent.status === 'working' && 'glow-border')}
      whileHover={{ scale: 1.01, boxShadow: '0 10px 40px -10px rgba(6,182,212,0.2)' }}
    >
      {/* 状态指示条 */}
      <div className={cn('absolute top-0 left-0 right-0 h-1', `bg-${statusColor}`)} />
      
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className={cn('p-3 rounded-xl', `bg-${statusColor}/20 text-${statusColor}`)}>
            {statusIcons[agent.status]}
          </div>
          <div>
            <h3 className="font-semibold text-white">{agent.name}</h3>
            <p className="text-sm text-surface-500">{agent.role}</p>
          </div>
        </div>
        <div className={cn('px-2 py-1 rounded-full text-xs font-medium', `bg-${statusColor}/20 text-${statusColor}`)}>
          {agent.status.toUpperCase()}
        </div>
      </div>

      {/* 当前任务 */}
      {agent.currentTask && (
        <motion.div
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: 'auto' }}
          className="mb-4 p-3 rounded-lg bg-surface-800/50 border border-surface-700/50"
        >
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs text-surface-500 uppercase tracking-wide">当前任务</span>
            <span className="text-xs font-mono text-ai-500">{agent.currentTask.progress}%</span>
          </div>
          <p className="font-medium text-white mb-2">{agent.currentTask.name}</p>
          <div className="h-2 bg-surface-700 rounded-full overflow-hidden">
            <motion.div
              initial={{ width: 0 }}
              animate={{ width: `${agent.currentTask.progress}%` }}
              className="h-full bg-gradient-to-r from-ai-500 to-purple-500"
              transition={{ duration: 0.5 }}
            />
          </div>
        </motion.div>
      )}

      {/* 模型信息 */}
      <div className="flex items-center gap-4 mb-4 text-sm">
        <div className="flex items-center gap-1 text-surface-400">
          <Terminal className="w-4 h-4" />
          <span>{agent.provider}</span>
        </div>
        <div className="flex items-center gap-1 text-surface-400">
          <Brain className="w-4 h-4" />
          <span className="truncate max-w-[180px]">{agent.model}</span>
        </div>
      </div>

      {/* Token 使用 */}
      <div className="grid grid-cols-3 gap-2 mb-4 p-3 rounded-lg bg-surface-800/50">
        <TokenStat label="Prompt" value={agent.tokenUsage.prompt} />
        <TokenStat label="Completion" value={agent.tokenUsage.completion} />
        <TokenStat label="Total" value={agent.tokenUsage.total} />
      </div>

      {/* 工具调用 */}
      {agent.tools.length > 0 && (
        <div className="mb-4">
          <p className="text-xs text-surface-500 mb-2">工具调用</p>
          <div className="flex flex-wrap gap-2">
            {agent.tools.map((tool: any, i: number) => (
              <ToolBadge key={i} tool={tool} />
            ))}
          </div>
        </div>
      )}

      {/* 性能指标 */}
      <div className="grid grid-cols-4 gap-2 pt-4 border-t border-surface-700/50">
        <MetricMini label="CPU" value={`${agent.metrics.cpu}%`} color="amber-500" />
        <MetricMini label="RAM" value={`${agent.metrics.ram}MB`} color="purple-500" />
        <MetricMini label="调用/分" value={agent.metrics.callsPerMin} color="ai-500" />
        <MetricMini label="延迟" value={`${agent.metrics.avgLatency}ms`} color="emerald-500" />
      </div>
    </motion.div>
  );
}

function TokenStat({ label, value }: { label: string; value: number }) {
  return (
    <div className="text-center">
      <p className="text-xs text-surface-500">{label}</p>
      <p className="font-mono font-medium text-white">{formatNumber(value)}</p>
    </div>
  );
}

function MetricMini({ label, value, color }: { label: string; value: string | number; color: string }) {
  return (
    <div className="text-center p-2 rounded-lg bg-surface-800/50">
      <p className="text-xs text-surface-500">{label}</p>
      <p className={cn('font-mono font-medium', `text-${color}`)}>{value}</p>
    </div>
  );
}

function ToolBadge({ tool }: { tool: any }) {
  const statusColors = {
    pending: 'surface-500',
    running: 'ai-500',
    completed: 'green-500',
    failed: 'red-500',
  };
  const statusIcons = {
    pending: '⏳',
    running: '⚡',
    completed: '✅',
    failed: '❌',
  };

  return (
    <span className={cn('px-2 py-1 rounded text-xs font-medium flex items-center gap-1', `bg-${statusColors[tool.status]}/20 text-${statusColors[tool.status]}`)}>
      {statusIcons[tool.status]} {tool.name}
    </span>
  );
}

function MetricMini({ label, value, color }: { label: string; value: string | number; color: string }) {
  return (
    <div className="text-center p-2 rounded-lg bg-surface-800/50">
      <p className="text-xs text-surface-500">{label}</p>
      <p className={cn('font-mono font-medium', `text-${color}`)}>{value}</p>
    </div>
  );
}