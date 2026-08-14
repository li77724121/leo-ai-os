import React, { useMemo, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Wallet, TrendingUp, TrendingDown, AlertTriangle, CheckCircle,
  Shield, AlertCircle, DollarSign, BarChart2, PieChart,
  RefreshCw, Filter, Search, ChevronDown, MoreHorizontal,
  Send, Receive, Zap, Activity, Gauge, Target
} from 'lucide-react';
import { cn, formatCurrency, formatPercent, formatNumber, formatDuration } from '../lib/utils';
import { useEventBus } from '../context/EventBusContext';

export function OKXHall() {
  const { state } = useEventBus();
  const [activeView, setActiveView] = useState<'positions' | 'strategies' | 'risk' | 'signals' | 'history'>('positions');
  const [timeRange, setTimeRange] = useState<'1h' | '4h' | '24h' | '7d'>('24h');

  const okxMetrics = useMemo(() => state.okxMetrics || {
    positions: [
      { symbol: 'SOL/USDT', side: 'long', size: '1.25', entry: '72.45', mark: '73.68', pnl: '+15.38', pnlPct: '+2.12%', lev: '1x', liq: '58.20' },
      { symbol: 'BTC/USDT', side: 'long', size: '0.025', entry: '64200', mark: '64850', pnl: '+16.25', pnlPct: '+1.01%', lev: '1x', liq: '52000' },
      { symbol: 'ETH/USDT', side: 'short', size: '0.45', entry: '3280', mark: '3245', pnl: '+15.75', pnlPct: '+1.08%', lev: '1x', liq: '4100' },
      { symbol: 'ARB/USDT', side: 'long', size: '125', entry: '1.42', mark: '1.45', pnl: '+3.75', pnlPct: '+2.11%', lev: '1x', liq: '1.15' },
    ],
    totalPnL: 51.13,
    dailyPnL: 23.45,
    riskLevel: 'low' as const,
    apiStatus: 'connected' as const,
    strategies: [
      { name: 'SOL Grid Bot', status: 'running', pnl: '+$23.45', winRate: '68%', trades: 47 },
      { name: 'BTC Trend Follow', status: 'running', pnl: '+$8.20', winRate: '54%', trades: 12 },
      { name: 'ETH Mean Reversion', status: 'paused', pnl: '-$2.10', winRate: '45%', trades: 8 },
    ],
    signals: [
      { symbol: 'SOL/USDT', action: 'buy', confidence: 0.82, price: 73.68, reason: 'Grid lower band hit', time: Date.now() - 1000*60*15 },
      { symbol: 'BTC/USDT', action: 'hold', confidence: 0.65, price: 64850, reason: 'Waiting for breakout', time: Date.now() - 1000*60*45 },
      { symbol: 'ETH/USDT', action: 'sell', confidence: 0.71, price: 3245, reason: 'RSI overbought + resistance', time: Date.now() - 1000*60*5 },
      { symbol: 'ARB/USDT', action: 'buy', confidence: 0.78, price: 1.45, reason: 'Grid lower band + volume spike', time: Date.now() - 1000*60*30 },
    ],
    history: [
      { id: 1, symbol: 'SOL/USDT', side: 'buy', size: '0.25', price: '72.80', pnl: '+2.15', time: Date.now() - 1000*60*60*2 },
      { id: 2, symbol: 'BTC/USDT', side: 'sell', size: '0.005', price: '64500', pnl: '+8.50', time: Date.now() - 1000*60*60*5 },
      { id: 3, symbol: 'ETH/USDT', side: 'buy', size: '0.15', price: '3220', pnl: '-1.20', time: Date.now() - 1000*60*60*8 },
      { id: 4, symbol: 'ARB/USDT', side: 'sell', size: '50', price: '1.47', pnl: '+1.50', time: Date.now() - 1000*60*60*12 },
    ],
  }), [state.okxMetrics]);

  const views = [
    { id: 'positions', label: '仓位', icon: <Wallet className="w-4 h-4" /> },
    { id: 'strategies', label: '策略', icon: <Target className="w-4 h-4" /> },
    { id: 'risk', label: '风控', icon: <Shield className="w-4 h-4" /> },
    { id: 'signals', label: '信号', icon: <Zap className="w-4 h-4" /> },
    { id: 'history', label: '历史', icon: <Activity className="w-4 h-4" /> },
  ];

  return (
    <div className="p-4 lg:p-6 space-y-6">
      {/* 顶部核心指标 */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-6 gap-3"
      >
        <MetricCard
          label="账户权益"
          value={formatCurrency(okxMetrics.totalPnL + 10000)}
          icon={<DollarSign className="w-6 h-6" />}
          color="emerald-500"
          trend="up"
          trendValue={formatCurrency(okxMetrics.totalPnL)}
          subtitle={`日盈亏 ${formatCurrency(okxMetrics.dailyPnL)}`}
          glow
        />
        <MetricCard
          label="活跃仓位"
          value={okxMetrics.positions.length}
          unit="个"
          icon={<Wallet className="w-6 h-6" />}
          color="amber-500"
        />
        <MetricCard
          label="日盈亏"
          value={formatCurrency(okxMetrics.dailyPnL)}
          icon={<TrendingUp className="w-6 h-6" />}
          color={okxMetrics.dailyPnL >= 0 ? 'green-500' : 'red-500'}
          trend={okxMetrics.dailyPnL >= 0 ? 'up' : 'down'}
          trendValue={okxMetrics.dailyPnL >= 0 ? '+5.2%' : '-2.1%'}
        />
        <MetricCard
          label="风险等级"
          value={okxMetrics.riskLevel.toUpperCase()}
          icon={<Shield className="w-6 h-6" />}
          color={okxMetrics.riskLevel === 'critical' ? 'red-500' : okxMetrics.riskLevel === 'high' ? 'amber-500' : 'green-500'}
        />
        <MetricCard
          label="API 状态"
          value={okxMetrics.apiStatus === 'connected' ? '正常' : '异常'}
          icon={<Activity className="w-6 h-6" />}
          color={okxMetrics.apiStatus === 'connected' ? 'green-500' : 'red-500'}
        />
        <MetricCard
          label="运行策略"
          value={okxMetrics.strategies.filter(s => s.status === 'running').length}
          unit="个"
          icon={<Target className="w-6 h-6" />}
          color="blue-500"
        />
      </motion.div>

      {/* 视图切换 */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="flex flex-wrap gap-2 bg-surface-900/50 rounded-xl p-1"
      >
        {views.map((view) => (
          <button
            key={view.id}
            onClick={() => setActiveView(view.id as any)}
            className={cn(
              'flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all',
              activeView === view.id
                ? 'bg-gradient-to-r from-amber-500/20 to-orange-500/20 text-white border border-amber-500/30'
                : 'text-surface-400 hover:bg-surface-800/50 hover:text-white'
            )}
          >
            {view.icon}
            {view.label}
          </button>
        ))}
      </motion.div>

      {/* 内容区 */}
      <AnimatePresence mode="wait">
        {activeView === 'positions' && <PositionsView data={okxMetrics} />}
        {activeView === 'strategies' && <StrategiesView data={okxMetrics} />}
        {activeView === 'risk' && <RiskView data={okxMetrics} />}
        {activeView === 'signals' && <SignalsView data={okxMetrics} />}
        {activeView === 'history' && <HistoryView data={okxMetrics} />}
      </AnimatePresence>
    </div>
  );
}

/* ===== 仓位视图 ===== */
function PositionsView({ data }: { data: any }) {
  return (
    <div className="space-y-6">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="glass-card overflow-hidden"
      >
        <div className="p-5 border-b border-surface-700/50">
          <div className="flex items-center justify-between">
            <h3 className="font-semibold">持仓详情 ({data.positions.length})</h3>
            <div className="flex items-center gap-2">
              <span className={cn('px-2 py-0.5 rounded text-xs font-medium', data.totalPnL >= 0 ? 'bg-green-500/20 text-green-500' : 'bg-red-500/20 text-red-500')}>
                总盈亏: {formatCurrency(data.totalPnL)}
              </span>
              <button className="btn-secondary text-xs">
                <Send className="w-3 h-3 mr-1" />
                平仓全部
              </button>
            </div>
          </div>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="text-left text-xs text-surface-500 uppercase tracking-wider bg-surface-800/50">
                <th className="p-4">交易对</th>
                <th className="p-4">方向</th>
                <th className="p-4">数量</th>
                <th className="p-4">开仓价</th>
                <th className="p-4">标记价</th>
                <th className="p-4">杠杆</th>
                <th className="p-4">强平价</th>
                <th className="p-4">未实现盈亏</th>
                <th className="p-4">盈亏%</th>
                <th className="p-4">操作</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-surface-700/50">
              {data.positions.map((pos: any, i: number) => (
                <tr key={i} className="hover:bg-surface-800/50 transition-colors">
                  <td className="p-4 font-mono font-medium text-white">{pos.symbol}</td>
                  <td className="p-4">
                    <span className={cn('px-2 py-0.5 rounded text-xs font-medium', 
                      pos.side === 'long' ? 'bg-green-500/20 text-green-500' : 'bg-red-500/20 text-red-500')}>
                      {pos.side.toUpperCase()}
                    </span>
                  </td>
                  <td className="p-4 font-mono text-surface-300">{pos.size}</td>
                  <td className="p-4 font-mono text-surface-300">${pos.entry}</td>
                  <td className="p-4 font-mono text-white">${pos.mark}</td>
                  <td className="p-4 text-surface-400">{pos.lev}</td>
                  <td className="p-4 font-mono text-surface-500">${pos.liq}</td>
                  <td className="p-4">
                    <span className={cn('font-mono font-medium', parseFloat(pos.pnl) >= 0 ? 'text-green-500' : 'text-red-500')}>
                      {pos.pnl}
                    </span>
                  </td>
                  <td className="p-4">
                    <span className={cn('font-mono font-medium', parseFloat(pos.pnlPct) >= 0 ? 'text-green-500' : 'text-red-500')}>
                      {pos.pnlPct}
                    </span>
                  </td>
                  <td className="p-4">
                    <button className="btn-danger text-xs px-2 py-1">平仓</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </motion.div>

      {/* 盈亏分布图 */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="grid grid-cols-1 lg:grid-cols-2 gap-4"
      >
        <div className="glass-card p-5">
          <h3 className="font-semibold mb-4 flex items-center gap-2">
            <BarChart2 className="w-5 h-5 text-amber-500" />
            盈亏分布
          </h3>
          <div className="h-64">
            <PnLDistributionChart positions={data.positions} />
          </div>
        </div>
        <div className="glass-card p-5">
          <h3 className="font-semibold mb-4 flex items-center gap-2">
            <PieChart className="w-5 h-5 text-blue-500" />
            资金分配
          </h3>
          <div className="h-64">
            <AllocationChart positions={data.positions} />
          </div>
        </div>
      </motion.div>
    </div>
  );
}

/* ===== 策略视图 ===== */
function StrategiesView({ data }: { data: any }) {
  return (
    <div className="space-y-4">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="grid grid-cols-1 md:grid-cols-3 gap-4"
      >
        {data.strategies.map((strategy: any, i: number) => (
          <motion.div
            key={i}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.1 }}
            className={cn('glass-card p-5 relative overflow-hidden', strategy.status === 'paused' && 'opacity-60')}
          >
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-semibold text-white">{strategy.name}</h3>
              <span className={cn('px-2 py-0.5 rounded text-xs font-medium',
                strategy.status === 'running' ? 'bg-green-500/20 text-green-500' :
                strategy.status === 'paused' ? 'bg-amber-500/20 text-amber-500' : 'bg-red-500/20 text-red-500'
              )}>
                {strategy.status.toUpperCase()}
              </span>
            </div>
            <div className="space-y-3 mb-4">
              <div className="flex items-center justify-between">
                <span className="text-surface-400">累计盈亏</span>
                <span className={cn('font-bold font-mono text-lg', strategy.pnl.startsWith('+') ? 'text-green-500' : 'text-red-500')}>
                  {strategy.pnl}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-surface-400">胜率</span>
                <span className="font-bold text-white">{strategy.winRate}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-surface-400">交易次数</span>
                <span className="font-mono text-white">{strategy.trades}</span>
              </div>
            </div>
            <div className="flex gap-2">
              <button className={cn('flex-1 btn-secondary text-sm', strategy.status === 'running' && 'bg-amber-500/20 text-amber-500 border-amber-500/30')}>
                {strategy.status === 'running' ? '暂停' : '启动'}
              </button>
              <button className="btn-danger px-3 py-1 text-xs">停止</button>
            </div>
          </motion.div>
        ))}
      </motion.div>
    </div>
  );
}

/* ===== 风控视图 ===== */
function RiskView({ data }: { data: any }) {
  const totalSize = data.positions.reduce((sum: number, p: any) => sum + parseFloat(p.size) * parseFloat(p.mark), 0);
  const totalMargin = totalSize; // 1x杠杆
  const maxDrawdown = Math.min(...data.positions.map((p: any) => parseFloat(p.pnlPct.replace('%', ''))));

  return (
    <div className="space-y-4">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="grid grid-cols-1 md:grid-cols-4 gap-4"
      >
        <MetricCard label="总敞口" value={formatCurrency(totalMargin)} icon={<DollarSign className="w-6 h-6" />} color="amber-500" />
        <MetricCard label="保证金占用" value={`${((totalMargin / 10000) * 100).toFixed(1)}%`} icon={<Shield className="w-6 h-6" />} color="blue-500" />
        <MetricCard label="最大回撤" value={`${maxDrawdown.toFixed(2)}%`} icon={<TrendingDown className="w-6 h-6" />} color={maxDrawdown < -5 ? 'red-500' : 'green-500'} />
        <MetricCard label="风险等级" value={data.riskLevel.toUpperCase()} icon={<Shield className="w-6 h-6" />} color={data.riskLevel === 'critical' ? 'red-500' : data.riskLevel === 'high' ? 'amber-500' : 'green-500'} />
      </motion.div>

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="grid grid-cols-1 lg:grid-cols-2 gap-4"
      >
        <div className="glass-card p-5">
          <h3 className="font-semibold mb-4 flex items-center gap-2">
            <AlertTriangle className="w-5 h-5 text-amber-500" />
            风控规则检查
          </h3>
          <div className="space-y-3">
            {[
              { rule: '单币种最大仓位 ≤ 30%', status: 'pass', detail: '当前最大 SOL 18.5%' },
              { rule: '单日最大亏损 ≤ 5%', status: 'pass', detail: '当前日亏 0.8%' },
              { rule: '最大杠杆 ≤ 3x', status: 'pass', detail: '当前均为 1x' },
              { rule: '强平价距离 ≥ 15%', status: 'pass', detail: '最小距离 23.4%' },
              { rule: '相关性对冲检查', status: 'warning', detail: 'BTC/ETH 相关性 0.87' },
            ].map((rule, i) => (
              <div key={i} className="flex items-center justify-between py-2 px-3 rounded-lg bg-surface-800/50">
                <div className="flex items-center gap-3">
                  <span className={cn('w-2 h-2 rounded-full', rule.status === 'pass' ? 'bg-green-500' : rule.status === 'warning' ? 'bg-amber-500' : 'bg-red-500')} />
                  <span className="text-sm text-white">{rule.rule}</span>
                </div>
                <span className={cn('px-2 py-0.5 rounded text-xs', rule.status === 'pass' ? 'bg-green-500/20 text-green-500' : rule.status === 'warning' ? 'bg-amber-500/20 text-amber-500' : 'bg-red-500/20 text-red-500')}>
                  {rule.status === 'pass' ? '通过' : rule.status === 'warning' ? '预警' : '违规'}
                </span>
              </div>
            ))}
          </div>
        </div>

        <div className="glass-card p-5">
          <h3 className="font-semibold mb-4 flex items-center gap-2">
            <Gauge className="w-5 h-5 text-red-500" />
            强平价监控
          </h3>
          <div className="space-y-3">
            {[
              { symbol: 'SOL/USDT', mark: 73.68, liq: 58.20, distance: 21.1 },
              { symbol: 'BTC/USDT', mark: 64850, liq: 52000, distance: 19.8 },
              { symbol: 'ETH/USDT', mark: 3245, liq: 4100, distance: 26.3 },
              { symbol: 'ARB/USDT', mark: 1.45, liq: 1.15, distance: 20.7 },
            ].map((pos, i) => (
              <div key={i} className="flex items-center justify-between py-2 px-3 rounded-lg bg-surface-800/50">
                <div className="flex items-center gap-3">
                  <span className="font-mono text-white">{pos.symbol}</span>
                  <span className="text-xs text-surface-500">标记: ${pos.mark}</span>
                </div>
                <div className="flex items-center gap-3">
                  <div className="w-32 h-2 bg-surface-700 rounded-full overflow-hidden">
                    <motion.div
                      initial={{ width: 0 }}
                      animate={{ width: `${pos.distance}%` }}
                      className="h-full bg-gradient-to-r from-green-500 to-amber-500 rounded-full"
                      transition={{ duration: 0.5 }}
                    />
                  </div>
                  <span className={cn('text-sm font-medium', pos.distance < 20 ? 'text-red-500' : 'text-green-500')}>
                    距离 ${pos.liq} (${pos.distance.toFixed(1)}%)
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </motion.div>
    </div>
  );
}

/* ===== 信号视图 ===== */
function SignalsView({ data }: { data: any }) {
  return (
    <div className="space-y-4">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="glass-card overflow-hidden"
      >
        <div className="p-5 border-b border-surface-700/50 flex items-center justify-between">
          <h3 className="font-semibold">实时交易信号 ({data.signals.length})</h3>
          <div className="flex items-center gap-2">
            <span className="px-2 py-0.5 text-xs bg-green-500/20 text-green-500 rounded">实时更新</span>
            <button className="btn-secondary text-xs"><RefreshCw className="w-3 h-3 mr-1" />刷新</button>
          </div>
        </div>
        <div className="divide-y divide-surface-700/50">
          {data.signals.map((signal: any, i: number) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: i * 0.05 }}
              className="px-5 py-4 hover:bg-surface-800/50"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <span className={cn('px-3 py-1 rounded text-sm font-medium',
                    signal.action === 'buy' ? 'bg-green-500/20 text-green-500' :
                    signal.action === 'sell' ? 'bg-red-500/20 text-red-500' : 'bg-amber-500/20 text-amber-500')}>
                    {signal.action.toUpperCase()}
                  </span>
                  <div>
                    <p className="font-mono font-medium text-white">{signal.symbol}</p>
                    <p className="text-xs text-surface-500">{signal.reason}</p>
                  </div>
                </div>
                <div className="flex items-center gap-4 text-sm">
                  <span className="font-mono text-white">${signal.price}</span>
                  <span className={cn('px-2 py-0.5 rounded text-xs font-medium',
                    signal.confidence > 0.8 ? 'bg-green-500/20 text-green-500' :
                    signal.confidence > 0.6 ? 'bg-amber-500/20 text-amber-500' : 'bg-red-500/20 text-red-500')}>
                    置信度 {(signal.confidence * 100).toFixed(0)}%
                  </span>
                  <span className="text-surface-500">{Math.round((Date.now() - signal.time) / 60000)}分钟前</span>
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      </motion.div>
    </div>
  );
}

/* ===== 历史视图 ===== */
function HistoryView({ data }: { data: any }) {
  return (
    <div className="space-y-4">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="glass-card overflow-hidden"
      >
        <div className="p-5 border-b border-surface-700/50">
          <h3 className="font-semibold">成交历史 ({data.history.length})</h3>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="text-left text-xs text-surface-500 uppercase tracking-wider bg-surface-800/50">
                <th className="p-4">时间</th>
                <th className="p-4">交易对</th>
                <th className="p-4">方向</th>
                <th className="p-4">数量</th>
                <th className="p-4">价格</th>
                <th className="p-4">盈亏</th>
                <th className="p-4">策略</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-surface-700/50">
              {data.history.map((trade: any, i: number) => (
                <tr key={i} className="hover:bg-surface-800/50">
                  <td className="p-4 text-sm text-surface-400">{new Date(trade.time).toLocaleString()}</td>
                  <td className="p-4 font-mono text-white">{trade.symbol}</td>
                  <td className="p-4">
                    <span className={cn('px-2 py-0.5 rounded text-xs font-medium',
                      trade.side === 'buy' ? 'bg-green-500/20 text-green-500' : 'bg-red-500/20 text-red-500')}>
                      {trade.side.toUpperCase()}
                    </span>
                  </td>
                  <td className="p-4 font-mono text-surface-300">{trade.size}</td>
                  <td className="p-4 font-mono text-white">${trade.price}</td>
                  <td className="p-4">
                    <span className={cn('font-mono font-medium', trade.pnl.startsWith('+') ? 'text-green-500' : 'text-red-500')}>
                      {trade.pnl}
                    </span>
                  </td>
                  <td className="p-4 text-xs text-surface-500">Grid/Trend</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </motion.div>
    </div>
  );
}

/* ===== 通用组件 ===== */
function MetricCard({ label, value, unit, icon, color, trend, trendValue, subtitle, glow }: any) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className={`glass-card p-5 relative overflow-hidden ${glow ? 'glow-border' : ''}`}
      whileHover={{ scale: 1.02, boxShadow: '0 10px 40px -10px rgba(6,182,212,0.3)' }}
    >
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs font-medium text-surface-500 uppercase tracking-wide mb-1">{label}</p>
          <div className="flex items-baseline gap-1">
            <span className="text-3xl font-bold text-white tabular-nums">{value}</span>
            {unit && <span className="text-surface-500 text-sm mt-1">{unit}</span>}
          </div>
          {subtitle && <p className="text-xs text-surface-500 mt-1">{subtitle}</p>}
          {trend && trendValue && (
            <div className="flex items-center gap-1 mt-2">
              <span className={`text-xs font-medium ${trend === 'up' ? 'text-green-500' : trend === 'down' ? 'text-red-500' : 'text-surface-500'}`}>
                {trend === 'up' ? '↑' : trend === 'down' ? '↓' : '→'} {trendValue}
              </span>
            </div>
          )}
        </div>
        <div className={`p-3 rounded-xl bg-${color}/20 text-${color}`}>{icon}</div>
      </div>
      <div className="absolute bottom-0 left-0 right-0 h-1 bg-gradient-to-r from-transparent via-current to-transparent opacity-20">
        <motion.div className="h-full w-1/3 bg-current" animate={{ x: ['-100%', '300%'] }} transition={{ duration: 2, repeat: Infinity, ease: 'linear' }} />
      </div>
    </motion.div>
  );
}

function StatCard({ label, value, icon, color }: any) {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      className={`glass-card p-4 border-l-4 border-${color}`}
    >
      <div className="flex items-center justify-between">
        <div>
          <p className="text-xs text-surface-500 uppercase tracking-wide">{label}</p>
          <p className="text-2xl font-bold text-white mt-1">{value}</p>
        </div>
        <div className={`p-2 rounded-lg bg-${color}/20 text-${color}`}>{icon}</div>
      </div>
    </motion.div>
  );
}

function PnLDistributionChart({ positions }: { positions: any[] }) {
  return (
    <svg viewBox="0 0 100 100" className="w-full h-full" preserveAspectRatio="none">
      {positions.map((pos, i) => (
        <rect
          key={i}
          x={i * 22 + 4}
          y={100 - Math.max(10, (parseFloat(pos.pnlPct) + 10) * 3)}
          width={18}
          height={Math.max(10, (parseFloat(pos.pnlPct) + 10) * 3)}
          fill={parseFloat(pos.pnlPct) >= 0 ? '#06b6d4' : '#ef4444'}
          rx={2}
        />
      ))}
      {positions.map((pos, i) => (
        <text
          key={`label-${i}`}
          x={i * 22 + 13}
          y={100 - Math.max(10, (parseFloat(pos.pnlPct) + 10) * 3) - 5}
          textAnchor="middle"
          fontSize="8"
          fill="white"
          fontFamily="monospace"
        >
          {pos.pnlPct}
        </text>
      ))}
    </svg>
  );
}

function AllocationChart({ positions }: { positions: any[] }) {
  const total = positions.reduce((sum, p) => sum + parseFloat(p.size) * parseFloat(p.mark), 0);
  let currentAngle = -90;

  return (
    <svg viewBox="0 0 100 100" className="w-full h-full" preserveAspectRatio="none">
      {positions.map((pos, i) => {
        const value = parseFloat(pos.size) * parseFloat(pos.mark);
        const percentage = (value / total) * 100;
        const angle = (percentage / 100) * 360;
        const startAngle = currentAngle;
        currentAngle += angle;

        const startRad = (startAngle * Math.PI) / 180;
        const endRad = (currentAngle * Math.PI) / 180;
        const largeArc = angle > 180 ? 1 : 0;

        const x1 = 50 + 35 * Math.cos(startRad);
        const y1 = 50 + 35 * Math.sin(startRad);
        const x2 = 50 + 35 * Math.cos(endRad);
        const y2 = 50 + 35 * Math.sin(endRad);

        const colors = ['#06b6d4', '#a855f7', '#f59e0b', '#ef4444', '#22c55e', '#0ea5e9'];
        return (
          <g key={i}>
            <path
              d={`M 50 50 L ${x1} ${y1} A 35 35 0 ${largeArc} 1 ${x2} ${y2} Z`}
              fill={colors[i % colors.length]}
              opacity="0.8"
            />
          </g>
        );
      })}
      <circle cx="50" cy="50" r="20" fill="#020617" />
      <text x="50" y="48" textAnchor="middle" fontSize="10" fill="white" fontFamily="monospace" fontWeight="bold">
        分配
      </text>
      <text x="50" y="62" textAnchor="middle" fontSize="8" fill="#64748b" fontFamily="monospace">
        100%
      </text>
    </svg>
  );
}