import React, { useMemo, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Code, Terminal, GitBranch, Hammer, Bug, Play,
  CheckCircle, XCircle, AlertTriangle, Clock,
  FolderOpen, FileCode, Search, Filter,
  ChevronDown, RefreshCw, Maximize2,
  Copy, Download, Trash2
} from 'lucide-react';
import { cn, formatDuration, formatBytes } from '../lib/utils';
import { useEventBus } from '../context/EventBusContext';

export function VSCodeHall() {
  const { state } = useEventBus();
  const [activeTab, setActiveTab] = useState<'workspace' | 'git' | 'terminal' | 'build' | 'debug' | 'test' | 'ai'>('workspace');
  const [searchQuery, setSearchQuery] = useState('');

  // 模拟 VS Code 数据
  const vscodeData = useMemo(() => ({
    workspace: {
      name: 'PowerAI',
      path: '/Users/leo/Desktop/M1hermes/projects/power-ai',
      files: 1247,
      lines: 89432,
      lastModified: Date.now() - 1000 * 60 * 15,
    },
    git: {
      branch: 'feature/okx-websocket',
      status: 'clean',
      ahead: 3,
      behind: 1,
      remotes: ['origin', 'upstream'],
      lastCommit: {
        hash: 'a1b2c3d',
        message: 'Add OKX WebSocket reconnection logic',
        author: 'Leo',
        time: Date.now() - 1000 * 60 * 45,
      },
      changes: [
        { file: 'src/monitors/okx.ts', status: 'modified', lines: '+45 -12' },
        { file: 'src/types/okx.ts', status: 'added', lines: '+120 -0' },
        { file: 'tests/okx.test.ts', status: 'modified', lines: '+30 -5' },
      ],
      stashes: 2,
    },
    terminal: {
      sessions: [
        { id: 1, name: 'bash', cwd: '/Users/leo/Desktop/M1hermes', lastOutput: 'leo@MacBook-Pro M1hermes % ', running: true },
        { id: 2, name: 'zsh', cwd: '/Users/leo/Desktop/M1hermes/projects/power-ai', lastOutput: '✓ Compiled successfully in 2.3s', running: false },
        { id: 3, name: 'python', cwd: '/Users/leo/Desktop/M1hermes', lastOutput: '>>> import hermes', running: true },
      ],
      history: [
        'cd /Users/leo/Desktop/M1hermes',
        'npm run dev',
        'git status',
        'git add .',
        'git commit -m "Add OKX WebSocket reconnection logic"',
      ],
    },
    build: {
      status: 'success' as const,
      lastBuild: Date.now() - 1000 * 60 * 5,
      duration: 12340,
      target: 'development',
      errors: [],
      warnings: 3,
      output: [
        '✓ Compiled 1247 modules in 12.3s',
        '✓ Type checking passed',
        '✓ Linting passed',
        '⚠ Warning: Unused variable in src/monitors/okx.ts:45',
        '⚠ Warning: Deprecated API usage in src/types/legacy.ts',
        '⚠ Warning: Large bundle size detected: 2.4 MB',
      ],
    },
    debug: {
      active: false,
      breakpoints: [
        { file: 'src/monitors/okx.ts', line: 45, condition: '', verified: true },
        { file: 'src/services/websocket.ts', line: 128, condition: 'retryCount > 3', verified: true },
        { file: 'src/types/okx.ts', line: 12, condition: '', verified: false },
      ],
      watchExpressions: ['retryCount', 'ws.readyState', 'lastMessage'],
      callStack: [],
      variables: {},
    },
    test: {
      total: 247,
      passed: 244,
      failed: 2,
      skipped: 1,
      lastRun: Date.now() - 1000 * 60 * 30,
      duration: 45600,
      suites: [
        { name: 'OKX Monitor', tests: 45, passed: 45, failed: 0 },
        { name: 'WebSocket Client', tests: 32, passed: 30, failed: 2 },
        { name: 'Trading Strategy', tests: 28, passed: 28, failed: 0 },
        { name: 'Risk Manager', tests: 15, passed: 15, failed: 0 },
        { name: 'Utils', tests: 127, passed: 126, failed: 0, skipped: 1 },
      ],
      failures: [
        { suite: 'WebSocket Client', test: 'should reconnect on network error', error: 'Timeout: Expected connection within 5000ms' },
        { suite: 'WebSocket Client', test: 'should handle malformed message', error: 'TypeError: Cannot read property of undefined' },
      ],
    },
    ai: {
      edits: [
        { file: 'src/monitors/okx.ts', type: 'insert' as const, lines: 45, time: Date.now() - 1000 * 60 * 10, description: 'Add reconnection logic with exponential backoff' },
        { file: 'src/types/okx.ts', type: 'insert' as const, lines: 120, time: Date.now() - 1000 * 60 * 12, description: 'Add new OrderBook and Trade types' },
        { file: 'src/services/websocket.ts', type: 'replace' as const, lines: 8, time: Date.now() - 1000 * 60 * 25, description: 'Refactor connection handler' },
        { file: 'tests/okx.test.ts', type: 'insert' as const, lines: 30, time: Date.now() - 1000 * 60 * 8, description: 'Add reconnection test cases' },
      ],
      suggestions: [
        { file: 'src/monitors/okx.ts', line: 67, type: 'optimization', message: 'Consider using WebSocket ping/pong for keepalive' },
        { file: 'src/services/rate-limiter.ts', line: 23, type: 'security', message: 'Add rate limit headers to response' },
      ],
    },
  }), []);

  const tabs = [
    { id: 'workspace', label: 'Workspace', icon: <FolderOpen className="w-4 h-4" />, count: vscodeData.workspace.files },
    { id: 'git', label: 'Git', icon: <GitBranch className="w-4 h-4" />, count: vscodeData.git.changes.length },
    { id: 'terminal', label: 'Terminal', icon: <Terminal className="w-4 h-4" />, count: vscodeData.terminal.sessions.length },
    { id: 'build', label: 'Build', icon: <Hammer className="w-4 h-4" />, count: vscodeData.build.warnings },
    { id: 'debug', label: 'Debug', icon: <Bug className="w-4 h-4" />, count: vscodeData.debug.breakpoints.length },
    { id: 'test', label: 'Test', icon: <Play className="w-4 h-4" />, count: vscodeData.test.total },
    { id: 'ai', label: 'AI Edits', icon: <Bot className="w-4 h-4" />, count: vscodeData.ai.edits.length },
  ];

  return (
    <div className="p-4 lg:p-6 space-y-6">
      {/* 顶部状态栏 */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex flex-col sm:flex-row gap-4 items-start sm:items-center justify-between p-4 glass-card"
      >
        <div className="flex items-center gap-4">
          <div className="p-3 rounded-xl bg-blue-500/20 text-blue-500">
            <Code className="w-6 h-6" />
          </div>
          <div>
            <h2 className="text-xl font-semibold text-white">{vscodeData.workspace.name}</h2>
            <p className="text-sm text-surface-500 truncate max-w-xs">{vscodeData.workspace.path}</p>
          </div>
          <div className="flex items-center gap-2 text-sm text-surface-400">
            <span>{vscodeData.workspace.files} 文件</span>
            <span>·</span>
            <span>{vscodeData.workspace.lines.toLocaleString()} 行代码</span>
            <span>·</span>
            <span>最后修改 {Math.round((Date.now() - vscodeData.workspace.lastModified) / 60000)} 分钟前</span>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <input
            type="text"
            placeholder="搜索文件..."
            className="px-3 py-2 bg-surface-800/50 border border-surface-700 rounded-lg text-white placeholder-surface-500 focus:outline-none focus:border-blue-500 w-64"
          />
          <button className="btn-secondary">
            <RefreshCw className="w-4 h-4 mr-2" />
            同步
          </button>
        </div>
      </motion.div>

      {/* 标签页导航 */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="flex gap-1 bg-surface-900/50 rounded-xl p-1"
      >
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id as any)}
            className={cn(
              'flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200',
              'relative overflow-hidden',
              activeTab === tab.id
                ? 'bg-gradient-to-r from-blue-500/20 to-purple-500/20 text-white border border-blue-500/30'
                : 'text-surface-400 hover:bg-surface-800/50 hover:text-white'
            )}
          >
            {tab.icon}
            {tab.label}
            {tab.count > 0 && (
              <span className={cn(
                'px-2 py-0.5 rounded-full text-xs font-medium',
                activeTab === tab.id ? 'bg-white/20 text-white' : 'bg-surface-700 text-surface-300'
              )}>
                {tab.count}
              </span>
            )}
          </button>
        ))}
      </motion.div>

      {/* 内容区 */}
      <AnimatePresence mode="wait">
        {activeTab === 'workspace' && <WorkspaceTab data={vscodeData.workspace} />}
        {activeTab === 'git' && <GitTab data={vscodeData.git} />}
        {activeTab === 'terminal' && <TerminalTab data={vscodeData.terminal} />}
        {activeTab === 'build' && <BuildTab data={vscodeData.build} />}
        {activeTab === 'debug' && <DebugTab data={vscodeData.debug} />}
        {activeTab === 'test' && <TestTab data={vscodeData.test} />}
        {activeTab === 'ai' && <AITab data={vscodeData.ai} />}
      </AnimatePresence>
    </div>
  );
}

function WorkspaceTab({ data }: { data: any }) {
  const [expandedFolders, setExpandedFolders] = useState<Set<string>>(new Set(['src', 'tests']));

  const fileTree = [
    { name: 'src', type: 'folder', children: [
      { name: 'monitors', type: 'folder', children: [
        { name: 'okx.ts', type: 'file', ext: 'ts', size: 12450 },
        { name: 'system.ts', type: 'file', ext: 'ts', size: 8920 },
        { name: 'openrouter.ts', type: 'file', ext: 'ts', size: 6750 },
      ]},
      { name: 'services', type: 'folder', children: [
        { name: 'websocket.ts', type: 'file', ext: 'ts', size: 15600 },
        { name: 'rate-limiter.ts', type: 'file', ext: 'ts', size: 4320 },
      ]},
      { name: 'types', type: 'folder', children: [
        { name: 'okx.ts', type: 'file', ext: 'ts', size: 3200 },
        { name: 'shared.ts', type: 'file', ext: 'ts', size: 2100 },
      ]},
      { name: 'agents', type: 'folder', children: [
        { name: 'cto.ts', type: 'file', ext: 'ts', size: 8900 },
        { name: 'dev.ts', type: 'file', ext: 'ts', size: 7600 },
        { name: 'trading.ts', type: 'file', ext: 'ts', size: 11200 },
      ]},
    ]},
    { name: 'tests', type: 'folder', children: [
      { name: 'okx.test.ts', type: 'file', ext: 'ts', size: 15400 },
      { name: 'websocket.test.ts', type: 'file', ext: 'ts', size: 8900 },
      { name: 'integration.test.ts', type: 'file', ext: 'ts', size: 22100 },
    ]},
    { name: 'docs', type: 'folder', children: [
      { name: 'architecture.md', type: 'file', ext: 'md', size: 12400 },
      { name: 'api.md', type: 'file', ext: 'md', size: 8900 },
    ]},
    { name: 'package.json', type: 'file', ext: 'json', size: 2450 },
    { name: 'tsconfig.json', type: 'file', ext: 'json', size: 1200 },
    { name: 'README.md', type: 'file', ext: 'md', size: 5600 },
  ];

  function renderTree(items: any[], level = 0) {
    return (
      <ul className={level > 0 ? 'ml-6 border-l border-surface-700/50 pl-4' : ''}>
        {items.map((item, i) => (
          <li key={`${item.name}-${i}`} className="py-1">
            {item.type === 'folder' ? (
              <FolderNode
                name={item.name}
                children={item.children}
                expanded={expandedFolders.has(item.name)}
                onToggle={() => setExpandedFolders(prev => {
                  const next = new Set(prev);
                  if (next.has(item.name)) next.delete(item.name);
                  else next.add(item.name);
                  return next;
                })}
                level={level}
              />
            ) : (
              <FileNode item={item} />
            )}
          </li>
        ))}
      </ul>
    );
  }

  return (
    <div className="h-[calc(100vh-300px)] overflow-y-auto p-4 space-y-4">
      <div className="glass-card p-4">
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-semibold">文件资源管理器</h3>
          <span className="text-xs text-surface-500">{data.files} 文件 · {data.lines.toLocaleString()} 行</span>
        </div>
        {renderTree(fileTree)}
      </div>
    </div>
  );
}

function FolderNode({ name, children, expanded, onToggle, level }: any) {
  return (
    <div>
      <button
        onClick={onToggle}
        className="flex items-center gap-2 py-1 px-2 rounded hover:bg-surface-800/50 transition-colors"
      >
        <ChevronDown className={cn('w-4 h-4 text-surface-500 transition-transform', expanded && 'rotate-90')} />
        <FolderOpen className="w-4 h-4 text-amber-500" />
        <span className="font-medium text-white">{name}</span>
        <span className="text-xs text-surface-500">({children.length})</span>
      </button>
      {expanded && <div>{renderTree(children, level + 1)}</div>}
    </div>
  );
}

function FileNode({ item }: { item: any }) {
  const icons: Record<string, any> = {
    ts: <FileCode className="w-4 h-4 text-blue-500" />,
    js: <FileCode className="w-4 h-4 text-yellow-500" />,
    json: <FileCode className="w-4 h-4 text-green-500" />,
    md: <FileCode className="w-4 h-4 text-purple-500" />,
  };

  return (
    <div className="flex items-center gap-2 py-1 px-2 rounded hover:bg-surface-800/50 transition-colors group">
      {icons[item.ext] || <FileCode className="w-4 h-4 text-surface-500" />}
      <span className="text-sm text-surface-300 truncate flex-1">{item.name}</span>
      <span className="text-xs text-surface-500 opacity-0 group-hover:opacity-100 transition-opacity">
        {formatBytes(item.size)}
      </span>
    </div>
  );
}

function GitTab({ data }: { data: any }) {
  return (
    <div className="p-4 space-y-6">
      {/* 分支信息 */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="grid grid-cols-1 md:grid-cols-4 gap-4"
      >
        <StatCard label="当前分支" value={data.branch} icon={<GitBranch className="w-5 h-5" />} color="blue-500" />
        <StatCard label="状态" value={data.status} icon={<CheckCircle className="w-5 h-5" />} color="green-500" />
        <StatCard label="领先" value={data.ahead} icon={<ChevronUp className="w-5 h-5" />} color="green-500" />
        <StatCard label="落后" value={data.behind} icon={<ChevronDown className="w-5 h-5" />} color="amber-500" />
      </motion.div>

      {/* 最近提交 */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="glass-card p-5"
      >
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-semibold">最近提交</h3>
          <span className="px-2 py-0.5 text-xs bg-blue-500/20 text-blue-500 rounded">
            {data.ahead} 领先 · {data.behind} 落后
          </span>
        </div>
        <div className="space-y-3">
          <CommitRow commit={data.lastCommit} />
        </div>
      </motion.div>

      {/* 文件变更 */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
        className="glass-card p-5"
      >
        <h3 className="font-semibold mb-4">工作区变更 ({data.changes.length})</h3>
        <div className="space-y-2">
          {data.changes.map((change: any, i: number) => (
            <div key={i} className="flex items-center justify-between py-2 px-3 rounded-lg bg-surface-800/50">
              <div className="flex items-center gap-3">
                <span className={cn('px-2 py-0.5 rounded text-xs font-medium', 
                  change.status === 'modified' && 'bg-blue-500/20 text-blue-500',
                  change.status === 'added' && 'bg-green-500/20 text-green-500',
                  change.status === 'deleted' && 'bg-red-500/20 text-red-500'
                )}>
                  {change.status.toUpperCase()}
                </span>
                <span className="font-mono text-sm text-white truncate max-w-md">{change.file}</span>
              </div>
              <span className="text-xs text-surface-500 font-mono">{change.lines}</span>
            </div>
          ))}
        </div>
      </motion.div>

      {/* Stashes */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}
        className="glass-card p-5"
      >
        <h3 className="font-semibold mb-3">Stashes ({data.stashes})</h3>
        <div className="text-surface-500 text-sm">暂无 stash 详情</div>
      </motion.div>
    </div>
  );
}

function TerminalTab({ data }: { data: any }) {
  const [activeSession, setActiveSession] = useState(data.sessions[0]);

  return (
    <div className="h-[calc(100vh-300px)] flex flex-col">
      {/* 会话标签 */}
      <div className="flex gap-1 bg-surface-900/50 rounded-xl p-1 border-b border-surface-700/50">
        {data.sessions.map((session: any) => (
          <button
            key={session.id}
            onClick={() => setActiveSession(session)}
            className={cn(
              'flex items-center gap-2 px-3 py-2 rounded-lg text-sm transition-colors',
              activeSession.id === session.id
                ? 'bg-blue-500/20 text-white border border-blue-500/30'
                : 'text-surface-400 hover:bg-surface-800/50'
            )}
          >
            <span className={cn('w-2 h-2 rounded-full', session.running ? 'bg-green-500' : 'bg-surface-500')} />
            {session.name}
            <span className="text-xs text-surface-500">{session.cwd.split('/').pop()}</span>
          </button>
        ))}
        <button className="ml-auto p-2 rounded-lg hover:bg-surface-800 text-surface-400">
          <span className="w-5 h-5">+</span>
        </button>
      </div>

      {/* 终端输出 */}
      <div className="flex-1 overflow-hidden bg-surface-950 relative">
        <div className="absolute top-2 right-2 flex gap-2 z-10">
          <button className="p-1 rounded hover:bg-surface-800 text-surface-400"><Copy className="w-4 h-4" /></button>
          <button className="p-1 rounded hover:bg-surface-800 text-surface-400"><Download className="w-4 h-4" /></button>
          <button className="p-1 rounded hover:bg-surface-800 text-surface-400"><Trash2 className="w-4 h-4" /></button>
        </div>
        <div className="h-full p-4 font-mono text-sm text-surface-300 overflow-y-auto bg-surface-950">
          <div className="space-y-1">
            <TerminalLine prompt={true} cwd={activeSession.cwd} />
            {data.history.map((cmd: string, i: number) => (
              <TerminalLine key={i} command={cmd} />
            ))}
            <TerminalLine prompt={true} cwd={activeSession.cwd} />
          </div>
        </div>
      </div>
    </div>
  );
}

function TerminalLine({ prompt, cwd, command }: { prompt?: boolean; cwd?: string; command?: string }) {
  return (
    <div className="flex items-baseline gap-2">
      {prompt && (
        <>
          <span className="text-green-500">➜</span>
          <span className="text-blue-500">{cwd?.split('/').pop() || '~'}</span>
          <span className="text-amber-500">$</span>
        </>
      )}
      {command && <span className="text-white ml-2">{command}</span>}
    </div>
  );
}

function BuildTab({ data }: { data: any }) {
  const statusColors = {
    success: 'green-500',
    failed: 'red-500',
    building: 'amber-500',
    idle: 'surface-500',
  };

  return (
    <div className="p-4 space-y-6">
      {/* 构建状态 */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="glass-card p-5"
      >
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-semibold">构建状态</h3>
          <span className={cn('px-3 py-1 rounded-full text-sm font-medium', `bg-${statusColors[data.status]}/20 text-${statusColors[data.status]}`)}>
            {data.status.toUpperCase()}
          </span>
        </div>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <StatCard label="上次构建" value={formatDuration(data.lastBuild ? Date.now() - data.lastBuild : 0)} icon={<Clock className="w-5 h-5" />} color="blue-500" />
          <StatCard label="耗时" value={formatDuration(data.duration)} icon={<Clock className="w-5 h-5" />} color="amber-500" />
          <StatCard label="警告" value={data.warnings} icon={<AlertTriangle className="w-5 h-5" />} color="amber-500" />
          <StatCard label="错误" value={data.errors.length} icon={<XCircle className="w-5 h-5" />} color="red-500" />
        </div>
      </motion.div>

      {/* 构建输出 */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="glass-card p-5"
      >
        <h3 className="font-semibold mb-4">构建输出</h3>
        <div className="bg-surface-950 rounded-lg p-4 font-mono text-sm max-h-96 overflow-y-auto">
          <pre className="text-surface-300 whitespace-pre-wrap">
            {data.output.map((line: string, i: number) => (
              <div key={i} className={cn('py-0.5', 
                line.includes('✓') && 'text-green-500',
                line.includes('⚠') && 'text-amber-500',
                line.includes('✗') && 'text-red-500'
              )}>
                {line}
              </div>
            ))}
          </pre>
        </div>
      </motion.div>
    </div>
  );
}

function DebugTab({ data }: { data: any }) {
  return (
    <div className="p-4 space-y-6">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="grid grid-cols-1 lg:grid-cols-3 gap-4"
      >
        <div className="lg:col-span-2 space-y-4">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="glass-card p-5"
          >
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-semibold">断点 ({data.breakpoints.length})</h3>
              <span className={cn('px-2 py-0.5 rounded text-xs', data.active ? 'bg-green-500/20 text-green-500' : 'bg-surface-700 text-surface-500')}>
                {data.active ? '调试中' : '未运行'}
              </span>
            </div>
            <div className="space-y-2">
              {data.breakpoints.map((bp: any, i: number) => (
                <div key={i} className="flex items-center justify-between py-2 px-3 rounded-lg bg-surface-800/50">
                  <div className="flex items-center gap-3">
                    <input type="checkbox" defaultChecked={bp.verified} className="w-4 h-4 accent-blue-500" />
                    <div>
                      <p className="font-mono text-sm text-white truncate max-w-xs">{bp.file}:{bp.line}</p>
                      {bp.condition && <p className="text-xs text-surface-500">条件: {bp.condition}</p>}
                    </div>
                  </div>
                  <span className={cn('px-2 py-0.5 rounded text-xs', bp.verified ? 'bg-green-500/20 text-green-500' : 'bg-amber-500/20 text-amber-500')}>
                    {bp.verified ? '已验证' : '未验证'}
                  </span>
                </div>
              ))}
            </div>
          </motion.div>
        </div>
        <div className="space-y-4">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="glass-card p-5"
          >
            <h3 className="font-semibold mb-3">监视表达式</h3>
            <div className="space-y-2">
              {data.watchExpressions.map((expr: string, i: number) => (
                <div key={i} className="flex items-center justify-between py-2 px-3 rounded-lg bg-surface-800/50">
                  <span className="font-mono text-white">{expr}</span>
                  <span className="text-surface-500">等待调试...</span>
                </div>
              ))}
            </div>
          </motion.div>
        </div>
      </motion.div>
    </div>
  );
}

function TestTab({ data }: { data: any }) {
  const passRate = ((data.passed / data.total) * 100).toFixed(1);

  return (
    <div className="p-4 space-y-6">
      {/* 测试概览 */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="grid grid-cols-2 md:grid-cols-5 gap-4"
      >
        <StatCard label="总测试" value={data.total} icon={<Play className="w-5 h-5" />} color="ai-500" />
        <StatCard label="通过" value={data.passed} icon={<CheckCircle className="w-5 h-5" />} color="green-500" />
        <StatCard label="失败" value={data.failed} icon={<XCircle className="w-5 h-5" />} color="red-500" />
        <StatCard label="跳过" value={data.skipped} icon={<Clock className="w-5 h-5" />} color="amber-500" />
        <StatCard label="通过率" value={`${passRate}%`} icon={<CheckCircle className="w-5 h-5" />} color={parseFloat(passRate) === 100 ? 'green-500' : 'amber-500'} />
      </motion.div>

      {/* 测试套件 */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="glass-card p-5"
      >
        <h3 className="font-semibold mb-4">测试套件</h3>
        <div className="space-y-3">
          {data.suites.map((suite: any, i: number) => (
            <div key={i} className="flex items-center justify-between py-3 px-3 rounded-lg bg-surface-800/50">
              <div className="flex items-center gap-3">
                <span className={cn('w-8 h-8 rounded-lg flex items-center justify-center', 
                  suite.failed === 0 ? 'bg-green-500/20' : 'bg-red-500/20'
                )}>
                  {suite.failed === 0 ? <CheckCircle className="w-5 h-5 text-green-500" /> : <XCircle className="w-5 h-5 text-red-500" />}
                </span>
                <div>
                  <p className="font-medium text-white">{suite.name}</p>
                  <p className="text-xs text-surface-500">{suite.tests} 测试 · {suite.passed} 通过 · {suite.failed} 失败</p>
                </div>
              </div>
              <div className="flex items-center gap-4 text-sm">
                <span className="text-green-500">{suite.passed} 通过</span>
                <span className="text-red-500">{suite.failed} 失败</span>
                <span className="text-amber-500">{suite.skipped} 跳过</span>
              </div>
            </div>
          ))}
        </div>
      </motion.div>

      {/* 失败详情 */}
      {data.failures.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="glass-card p-5 border-l-4 border-red-500"
        >
          <h3 className="font-semibold mb-3 text-red-500">失败详情 ({data.failures.length})</h3>
          <div className="space-y-3">
            {data.failures.map((failure: any, i: number) => (
              <div key={i} className="bg-surface-950 rounded-lg p-4">
                <div className="flex items-center justify-between mb-2">
                  <span className="font-medium text-white">{failure.suite}</span>
                  <span className="text-red-500 font-mono">{failure.test}</span>
                </div>
                <pre className="text-red-400 text-sm overflow-x-auto">{failure.error}</pre>
              </div>
            ))}
          </div>
        </motion.div>
      )}
    </div>
  );
}

function AITab({ data }: { data: any }) {
  return (
    <div className="p-4 space-y-6">
      {/* AI 编辑历史 */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="glass-card p-5"
      >
        <h3 className="font-semibold mb-4 flex items-center gap-2">
          <Bot className="w-5 h-5 text-purple-500" />
          AI 编辑历史 ({data.edits.length})
        </h3>
        <div className="space-y-3">
          {data.edits.map((edit: any, i: number) => (
            <div key={i} className="flex items-start gap-3 py-3 px-3 rounded-lg bg-surface-800/50">
              <div className={cn('w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0', 
                edit.type === 'insert' && 'bg-green-500/20',
                edit.type === 'delete' && 'bg-red-500/20',
                edit.type === 'replace' && 'bg-blue-500/20'
              )}>
                {edit.type === 'insert' && <span className="text-green-500">+</span>}
                {edit.type === 'delete' && <span className="text-red-500">−</span>}
                {edit.type === 'replace' && <span className="text-blue-500">↻</span>}
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between mb-1">
                  <span className="font-medium text-white truncate">{edit.file}</span>
                  <span className="text-xs text-surface-500">{Math.round((Date.now() - edit.time) / 60000)} 分钟前</span>
                </div>
                <p className="text-sm text-surface-300">{edit.description}</p>
                <div className="flex items-center gap-2 mt-1">
                  <span className="px-2 py-0.5 text-xs rounded bg-surface-700 text-surface-400">{edit.type}</span>
                  <span className="px-2 py-0.5 text-xs rounded bg-surface-700 text-surface-400">+{edit.lines} 行</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </motion.div>

      {/* AI 建议 */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="glass-card p-5 border-l-4 border-purple-500"
      >
        <h3 className="font-semibold mb-3 flex items-center gap-2">
          <Sparkles className="w-5 h-5 text-purple-500" />
          AI 代码建议 ({data.suggestions.length})
        </h3>
        <div className="space-y-3">
          {data.suggestions.map((suggestion: any, i: number) => (
            <div key={i} className="p-3 rounded-lg bg-surface-800/50 border border-purple-500/30">
              <div className="flex items-start gap-3">
                <Sparkles className="w-5 h-5 text-purple-500 mt-0.5" />
                <div className="flex-1">
                  <div className="flex items-center justify-between mb-1">
                    <span className="font-medium text-white">{suggestion.file}:{suggestion.line}</span>
                    <span className={cn('px-2 py-0.5 rounded text-xs', 
                      suggestion.type === 'optimization' && 'bg-blue-500/20 text-blue-500',
                      suggestion.type === 'security' && 'bg-red-500/20 text-red-500'
                    )}>
                      {suggestion.type}
                    </span>
                  </div>
                  <p className="text-sm text-surface-300">{suggestion.message}</p>
                </div>
              </div>
            </div>
          ))}
        </div>
      </motion.div>
    </div>
  );
}