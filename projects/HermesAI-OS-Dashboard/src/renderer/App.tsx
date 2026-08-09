import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  LayoutDashboard, Code, Wallet, FolderGit2, Cpu, 
  ChevronLeft, ChevronRight, Settings, Bell, 
  Zap, Server, Database, Globe, Monitor,
  AlertTriangle, CheckCircle, XCircle,
  Menu, X, Box
} from 'lucide-react';
import { useConfig } from './context/ConfigContext';
import { useEventBus } from './context/EventBusContext';
import { cn } from './lib/utils';

// ===== 页面组件 =====
const HermesHall = React.lazy(() => import('./pages/HermesHall'));
const VSCodeHall = React.lazy(() => import('./pages/VSCodeHall'));
const OKXHall = React.lazy(() => import('./pages/OKXHall'));
const ProjectHall = React.lazy(() => import('./pages/ProjectHall'));
const CommandCenter = React.lazy(() => import('./pages/CommandCenter'));
const Dashboard3D = React.lazy(() => import('./pages/Dashboard3D'));

const HallComponents = {
  hermes: HermesHall,
  vscode: VSCodeHall,
  okx: OKXHall,
  project: ProjectHall,
  command: CommandCenter,
  '3d': Dashboard3D,
};

type HallKey = keyof typeof HallComponents;

const HALLS: { key: HallKey; label: string; icon: React.ReactNode; description: string }[] = [
  { key: 'command', label: 'Command', icon: <Cpu className="w-5 h-5" />, description: '指挥中心' },
  { key: '3d', label: '3D 孪生', icon: <Box3DIcon />, description: '数字公司地图' },
  { key: 'hermes', label: 'Hermes', icon: <Zap className="w-5 h-5" />, description: 'Agent 实时监控' },
  { key: 'vscode', label: 'VS Code', icon: <Code className="w-5 h-5" />, description: '开发环境监控' },
  { key: 'okx', label: 'OKX', icon: <Wallet className="w-5 h-5" />, description: '交易监控与策略' },
  { key: 'project', label: 'Project', icon: <FolderGit2 className="w-5 h-5" />, description: '项目中心' },
];

function Box3DIcon() {
  return <div className="w-5 h-5 flex items-center justify-center"><Box className="w-5 h-5" /></div>;
}

import { cn } from './lib/utils';
import { eventBus } from '@shared/eventBus';

// ===== 工具函数 =====

// ===== Sidebar 组件 =====
function Sidebar({ isOpen, onToggle, activeHall, onHallChange }: { 
  isOpen: boolean; 
  onToggle: () => void;
  activeHall: HallKey;
  onHallChange: (hall: HallKey) => void;
}) {
  const { state: configState } = useConfig();

  return (
    <motion.aside
      initial={{ x: -280 }}
      animate={{ x: isOpen ? 0 : -280 }}
      transition={{ type: 'spring', damping: 25, stiffness: 300 }}
      className="fixed left-0 top-0 z-50 h-full w-72 bg-surface-900/95 backdrop-blur-xl border-r border-surface-700/50 flex flex-col"
    >
      {/* Logo */}
      <div className="flex items-center justify-between h-16 px-4 border-b border-surface-700/50">
        <div className="flex items-center gap-3">
          <motion.div
            animate={{ rotate: [0, 360] }}
            transition={{ duration: 20, repeat: Infinity, ease: 'linear' }}
            className="w-10 h-10 rounded-xl bg-gradient-to-br from-ai-500 to-purple-500 flex items-center justify-center"
          >
            <Zap className="w-6 h-6 text-white" />
          </motion.div>
          <div>
            <h1 className="font-semibold text-white">Hermes AI OS</h1>
            <p className="text-xs text-surface-500">Command Center</p>
          </div>
        </div>
        <button 
          onClick={onToggle}
          className="lg:hidden p-2 rounded-lg hover:bg-surface-800 text-surface-400"
          aria-label="关闭侧边栏"
        >
          <X className="w-5 h-5" />
        </button>
      </div>

      {/* 导航菜单 */}
      <nav className="flex-1 py-4 px-3 space-y-1 overflow-y-auto">
        {HALLS.map((hall) => (
          <button
            key={hall.key}
            onClick={() => onHallChange(hall.key)}
            className={cn(
              'w-full flex items-center gap-3 px-3 py-2.5 rounded-xl transition-all duration-200',
              'text-left group',
              activeHall === hall.key
                ? 'bg-gradient-to-r from-ai-500/20 to-purple-500/20 text-white border border-ai-500/30'
                : 'text-surface-300 hover:bg-surface-800/50 hover:text-white'
            )}
          >
            <span className={cn(
              'w-10 h-10 rounded-lg flex items-center justify-center transition-transform group-hover:scale-110',
              activeHall === hall.key 
                ? 'bg-ai-500/30 text-ai-400' 
                : 'bg-surface-800 text-surface-400'
            )}>
              {hall.icon}
            </span>
            <div className="flex-1 min-w-0">
              <p className="font-medium truncate">{hall.label}</p>
              <p className="text-xs text-surface-500 truncate">{hall.description}</p>
            </div>
            {activeHall === hall.key && (
              <motion.div
                layoutId="activeIndicator"
                className="w-1 h-10 bg-gradient-to-b from-ai-500 to-purple-500 rounded-r-full"
                transition={{ type: 'spring', damping: 20, stiffness: 300 }}
              />
            )}
          </button>
        ))}
      </nav>

      {/* 底部状态栏 */}
      <div className="p-4 border-t border-surface-700/50 space-y-3">
        {/* 系统状态指标 */}
        <div className="grid grid-cols-3 gap-2">
          <MetricCard label="CPU" value="12%" color="ai-500" trend="down" />
          <MetricCard label="RAM" value="3.2GB" color="purple-500" trend="up" />
          <MetricCard label="NET" value="45Mbps" color="amber-500" trend="stable" />
        </div>

        {/* 版本信息 */}
        <div className="flex items-center justify-between text-xs text-surface-500">
          <span>v1.0.0-dev</span>
          <span>Electron 31</span>
        </div>
      </div>
    </motion.aside>
  );
}

function MetricCard({ label, value, color, trend }: { label: string; value: string; color: string; trend: 'up' | 'down' | 'stable' }) {
  const trendIcons = {
    up: <ChevronUp className="w-3 h-3 text-green-500" />,
    down: <ChevronDown className="w-3 h-3 text-red-500" />,
    stable: <ChevronRight className="w-3 h-3 text-surface-500" />,
  };

  return (
    <div className="glass-card p-3">
      <p className="text-xs text-surface-500">{label}</p>
      <div className="flex items-center justify-between mt-1">
        <span className="font-mono font-semibold text-white">{value}</span>
        <span className={`text-${color}-500`}>{trendIcons[trend]}</span>
      </div>
    </div>
  );
}

// ===== TopBar 组件 =====
function TopBar({ sidebarOpen, onToggleSidebar, activeHall }: { 
  sidebarOpen: boolean; 
  onToggleSidebar: () => void;
  activeHall: HallKey;
}) {
  const { state: configState } = useConfig();
  const { state: eventState } = useEventBus();
  const [showAlerts, setShowAlerts] = useState(false);
  const [showSettings, setShowSettings] = useState(false);

  const unreadAlerts = eventState.alerts.filter(a => a.status === 'active').length;
  const pendingApprovals = eventState.governanceRequests.filter(r => r.status === 'pending').length;

  return (
    <motion.header
      initial={{ y: -80 }}
      animate={{ y: 0 }}
      className="fixed top-0 left-0 right-0 z-40 h-14 bg-surface-950/80 backdrop-blur-xl border-b border-surface-700/50 flex items-center justify-between px-4 lg:px-6"
      style={{ left: sidebarOpen ? 280 : 0 }}
    >
      <div className="flex items-center gap-4">
        <button
          onClick={onToggleSidebar}
          className="lg:hidden p-2 rounded-lg hover:bg-surface-800 text-surface-300"
          aria-label="打开菜单"
        >
          <Menu className="w-5 h-5" />
        </button>

        {/* 面包屑 */}
        <div className="hidden md:flex items-center gap-2 text-sm">
          <span className="text-surface-500">Hermes AI OS</span>
          <ChevronRight className="w-4 h-4 text-surface-600" />
          <span className="font-medium text-white capitalize">{activeHall}</span>
        </div>
      </div>

      <div className="flex items-center gap-3">
        {/* 搜索 */}
        <div className="relative hidden lg:block">
          <input
            type="text"
            placeholder="搜索 Agent、任务、技能..."
            className="w-64 pl-10 pr-4 py-2 bg-surface-800/50 border border-surface-700 rounded-lg text-white placeholder-surface-500 focus:outline-none focus:border-ai-500 focus:ring-1 focus:ring-ai-500 transition-all"
          />
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-surface-500" />
        </div>

        {/* 告警铃铛 */}
        <button
          onClick={() => setShowAlerts(!showAlerts)}
          className={cn('relative p-2 rounded-lg hover:bg-surface-800 transition-colors', unreadAlerts > 0 && 'text-amber-500')}
        >
          <Bell className="w-5 h-5" />
          {unreadAlerts > 0 && (
            <motion.span
              animate={{ scale: [1, 1.3, 1] }}
              transition={{ repeat: Infinity, duration: 1.5 }}
              className="absolute -top-1 -right-1 w-5 h-5 bg-amber-500 text-white text-xs font-bold rounded-full flex items-center justify-center"
            >
              {unreadAlerts > 9 ? '9+' : unreadAlerts}
            </motion.span>
          )}
        </button>

        {/* 审批待办 */}
        {pendingApprovals > 0 && (
          <button className="relative p-2 rounded-lg hover:bg-surface-800 transition-colors text-red-500">
            <AlertTriangle className="w-5 h-5" />
            <span className="absolute -top-1 -right-1 w-5 h-5 bg-red-500 text-white text-xs font-bold rounded-full flex items-center justify-center">
              {pendingApprovals}
            </span>
          </button>
        )}

        {/* 设置 */}
        <button
          onClick={() => setShowSettings(!showSettings)}
          className="p-2 rounded-lg hover:bg-surface-800 transition-colors text-surface-400"
        >
          <Settings className="w-5 h-5" />
        </button>
      </div>
    </motion.header>
  );
}

// ===== 右侧面板：告警/设置 =====
function RightPanel({ showAlerts, onCloseAlerts, showSettings, onCloseSettings }: any) {
  if (!showAlerts && !showSettings) return null;

  return (
    <motion.div
      initial={{ x: 400 }}
      animate={{ x: 0 }}
      exit={{ x: 400 }}
      className="fixed top-14 right-0 bottom-0 z-50 w-80 bg-surface-900/95 backdrop-blur-xl border-l border-surface-700/50 overflow-y-auto"
    >
      {showAlerts && (
        <AlertPanel onClose={onCloseAlerts} />
      )}
      {showSettings && (
        <SettingsPanel onClose={onCloseSettings} />
      )}
    </motion.div>
  );
}

function AlertPanel({ onClose }: { onClose: () => void }) {
  const { state } = useEventBus();

  return (
    <div className="h-full flex flex-col">
      <div className="flex items-center justify-between p-4 border-b border-surface-700/50">
        <h3 className="font-semibold">告警中心</h3>
        <button onClick={onClose} className="p-1 rounded hover:bg-surface-800">
          <X className="w-5 h-5" />
        </button>
      </div>
      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {state.alerts.length === 0 ? (
          <div className="text-center py-12 text-surface-500">
            <Bell className="w-12 h-12 mx-auto mb-4 opacity-30" />
            <p>暂无告警</p>
          </div>
        ) : (
          state.alerts.map((alert: any) => (
            <AlertCard key={alert.id} alert={alert} />
          ))
        )}
      </div>
    </div>
  );
}

function AlertCard({ alert }: { alert: any }) {
  const severityColors = {
    info: 'ai-500',
    warning: 'amber-500',
    critical: 'red-500',
  };

  return (
    <motion.div
      initial={{ opacity: 0, x: 20 }}
      animate={{ opacity: 1, x: 0 }}
      className={cn('glass-card p-4', alert.severity === 'critical' && 'border-l-4 border-red-500')}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <span className={cn('px-2 py-0.5 rounded text-xs font-medium', `bg-${severityColors[alert.severity]}/20 text-${severityColors[alert.severity]}`)}>
              {alert.severity.toUpperCase()}
            </span>
            <span className="text-xs text-surface-500">{alert.source}</span>
          </div>
          <p className="font-medium text-white mb-1">{alert.title}</p>
          <p className="text-sm text-surface-400">{alert.message}</p>
          <p className="text-xs text-surface-500 mt-2">{new Date(alert.createdAt).toLocaleString()}</p>
        </div>
        {alert.status === 'active' && (
          <button className="btn-secondary text-xs whitespace-nowrap">确认</button>
        )}
      </div>
    </motion.div>
  );
}

function SettingsPanel({ onClose }: { onClose: () => void }) {
  const { state, updateConfig } = useConfig();

  return (
    <div className="h-full flex flex-col">
      <div className="flex items-center justify-between p-4 border-b border-surface-700/50">
        <h3 className="font-semibold">设置</h3>
        <button onClick={onClose} className="p-1 rounded hover:bg-surface-800">
          <X className="w-5 h-5" />
        </button>
      </div>
      <div className="flex-1 overflow-y-auto p-4 space-y-6">
        <section>
          <h4 className="font-medium mb-4 text-surface-300">界面</h4>
          <div className="space-y-4">
            <SettingToggle 
              label="启用动画" 
              value={state.config.ui.animations} 
              onChange={(v) => updateConfig({ ui: { ...state.config.ui, animations: v } })} 
            />
            <SettingToggle 
              label="紧凑模式" 
              value={state.config.ui.compactMode} 
              onChange={(v) => updateConfig({ ui: { ...state.config.ui, compactMode: v }})} 
            />
          </div>
        </section>
        <section>
          <h4 className="font-medium mb-4 text-surface-300">告警</h4>
          <div className="space-y-4">
            <SettingToggle 
              label="声音提醒" 
              value={state.config.alerts.sound} 
              onChange={(v) => updateConfig({ alerts: { ...state.config.alerts, sound: v } })} 
            />
            <SettingToggle 
              label="桌面通知" 
              value={state.config.alerts.desktop} 
              onChange={(v) => updateConfig({ alerts: { ...state.config.alerts, desktop: v } })} 
            />
          </div>
        </section>
        <section>
          <h4 className="font-medium mb-4 text-surface-300">刷新间隔</h4>
          <div className="space-y-4">
            <SettingNumber 
              label="系统指标 (ms)" 
              value={state.config.refreshIntervals.system} 
              onChange={(v) => updateConfig({ refreshIntervals: { ...state.config.refreshIntervals, system: v } })} 
            />
            <SettingNumber 
              label="Agent 状态 (ms)" 
              value={state.config.refreshIntervals.agents} 
              onChange={(v) => updateConfig({ refreshIntervals: { ...state.config.refreshIntervals, agents: v } })} 
            />
          </div>
        </section>
      </div>
    </div>
  );
}

function SettingToggle({ label, value, onChange }: { label: string; value: boolean; onChange: (v: boolean) => void }) {
  return (
    <label className="flex items-center justify-between cursor-pointer">
      <span className="text-sm text-surface-300">{label}</span>
      <button
        onClick={() => onChange(!value)}
        className={cn('relative w-11 h-6 rounded-full transition-colors', value ? 'bg-ai-500' : 'bg-surface-700')}
        role="switch"
        aria-checked={value}
      >
        <span className={cn('absolute top-0.5 w-5 h-5 bg-white rounded-full transition-transform', value ? 'translate-x-5' : 'translate-x-0.5')} />
      </button>
    </label>
  );
}

function SettingNumber({ label, value, onChange }: { label: string; value: number; onChange: (v: number) => void }) {
  return (
    <div className="flex items-center gap-4">
      <span className="text-sm text-surface-300 w-32">{label}</span>
      <input
        type="number"
        value={value}
        onChange={(e) => onChange(parseInt(e.target.value) || 0)}
        className="flex-1 px-3 py-2 bg-surface-800 border border-surface-700 rounded-lg text-white focus:outline-none focus:border-ai-500"
        min="100"
        max="60000"
        step="100"
      />
      <span className="text-xs text-surface-500">ms</span>
    </div>
  );
}

// ===== 主应用 =====
export function App() {
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [activeHall, setActiveHall] = useState<HallKey>('command');
  const [showAlerts, setShowAlerts] = useState(false);
  const [showSettings, setShowSettings] = useState(false);

  // 监听来自主进程的事件
  useEffect(() => {
    const unsubGov = window.electron.on.governanceRequest((request) => {
      // 触发 EventBus 事件
      eventBus.emit('governance:request', request);
    });
    const unsubAlert = window.electron.on.alert((alert) => {
      eventBus.emit('alert:created', alert);
    });
    const unsubMetrics = window.electron.on.metricsUpdate((data) => {
      eventBus.emit('metrics:update', data);
    });
    return () => {
      unsubGov(); unsubAlert(); unsubMetrics();
    };
  }, []);

  return (
    <div className="h-screen w-full bg-surface-950 overflow-hidden">
      {/* 侧边栏 */}
      <Sidebar 
        isOpen={sidebarOpen} 
        onToggle={() => setSidebarOpen(!sidebarOpen)}
        activeHall={activeHall}
        onHallChange={setActiveHall}
      />

      {/* 顶部栏 */}
      <TopBar 
        sidebarOpen={sidebarOpen} 
        onToggleSidebar={() => setSidebarOpen(!sidebarOpen)}
        activeHall={activeHall}
      />

      {/* 右侧面板 */}
      <RightPanel 
        showAlerts={showAlerts} 
        onCloseAlerts={() => setShowAlerts(false)}
        showSettings={showSettings}
        onCloseSettings={() => setShowSettings(false)}
      />

      {/* 主内容区 */}
      <main 
        className={cn(
          'pt-14 h-full overflow-auto transition-all duration-300',
          sidebarOpen ? 'lg:ml-72' : 'lg:ml-0'
        )}
      >
        <AnimatePresence mode="wait">
          <React.Suspense fallback={<PageSkeleton />}>
            {(() => {
              const ActiveComponent = HallComponents[activeHall];
              return ActiveComponent ? <ActiveComponent key={activeHall} /> : null;
            })()}
          </React.Suspense>
        </AnimatePresence>
      </main>
    </div>
  );
}

function PageSkeleton() {
  return (
    <div className="p-6 space-y-4 animate-pulse">
      <div className="h-8 bg-surface-800 rounded w-1/4"></div>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {[1,2,3,4,5,6].map(i => (
          <div key={i} className="h-40 bg-surface-800 rounded-xl"></div>
        ))}
      </div>
    </div>
  );
}

// 导入缺失的图标
import { Search, ChevronUp, ChevronDown } from 'lucide-react';

export default App;