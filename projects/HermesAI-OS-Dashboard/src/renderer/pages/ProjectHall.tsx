import React, { useMemo, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  FolderGit2, Rocket, Zap, Brain, Code, 
  Users, Clock, CheckCircle, AlertTriangle,
  XCircle, ChevronDown, ChevronRight, TrendingUp,
  Target, Flag, MessageSquare, GitBranch,
  RefreshCw, Filter, Search, Plus, Edit, Trash2
} from 'lucide-react';
import { cn, formatDuration, formatNumber } from '../lib/utils';
import { useEventBus } from '../context/EventBusContext';

export function ProjectHall() {
  const { state } = useEventBus();
  const [activeProject, setActiveProject] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
  const [filterStatus, setFilterStatus] = useState<'all' | 'active' | 'paused' | 'completed'>('all');

  const projects = useMemo(() => [
    {
      id: 'power-ai',
      name: 'PowerAI',
      description: '企业级 AI 工作流自动化平台，支持多模型编排、技能市场、可视化编排',
      status: 'active' as const,
      progress: 65,
      assignee: 'CTO-Agent',
      team: ['CTO-Agent', 'Dev-Agent', 'UI-Agent', 'Security-Agent'],
      model: 'qwen2.5-coder:7b (本地) + nemotron-3-ultra:free (云)',
      repo: 'github.com/leo/power-ai',
      branch: 'main',
      lastCommit: 'Add workflow visual editor',
      commits: 342,
      lastUpdate: Date.now() - 1000 * 60 * 30,
      estimatedCompletion: Date.now() + 1000 * 60 * 60 * 24 * 14,
      tasks: [
        { id: 1, name: '核心编排引擎', status: 'completed', assignee: 'CTO-Agent' },
        { id: 2, name: '技能市场', status: 'completed', assignee: 'Dev-Agent' },
        { id: 3, name: '可视化编排器', status: 'in_progress', assignee: 'UI-Agent', progress: 60 },
        { id: 4, name: '多模型路由', status: 'in_progress', assignee: 'CTO-Agent', progress: 45 },
        { id: 5, name: '权限系统', status: 'pending', assignee: 'Security-Agent' },
        { id: 6, name: '部署流水线', status: 'pending', assignee: 'Dev-Agent' },
        { id: 7, name: '文档 & 示例', status: 'pending', assignee: 'UI-Agent' },
      ],
      metrics: {
        linesOfCode: 45600,
        testCoverage: 78,
        openIssues: 12,
        prsOpen: 3,
      },
      timeline: [
        { date: '2026-07-01', event: '项目立项', type: 'milestone' },
        { date: '2026-07-15', event: '架构设计完成', type: 'milestone' },
        { date: '2026-08-01', event: '核心引擎上线', type: 'release' },
        { date: '2026-08-15', event: '技能市场上线', type: 'release' },
      ],
    },
    {
      id: 'ai-drawing',
      name: 'AI 制图平台',
      description: '基于 Stable Diffusion + ControlNet 的企业级 AI 制图服务，支持批量生成、风格迁移、商业授权',
      status: 'active' as const,
      progress: 40,
      assignee: 'UI-Agent',
      team: ['UI-Agent', 'Dev-Agent', 'Research-Agent'],
      model: 'SDXL + ControlNet (本地 GPU) + nemotron-3-ultra (提示词优化)',
      repo: 'github.com/leo/ai-drawing',
      branch: 'develop',
      lastCommit: 'Add ControlNet tile upscaler',
      commits: 156,
      lastUpdate: Date.now() - 1000 * 60 * 60 * 2,
      estimatedCompletion: Date.now() + 1000 * 60 * 60 * 24 * 30,
      tasks: [
        { id: 1, name: 'SDXL 基础推理', status: 'completed', assignee: 'Dev-Agent' },
        { id: 2, name: 'ControlNet 集成', status: 'in_progress', assignee: 'UI-Agent', progress: 55 },
        { id: 3, name: '批量生成 API', status: 'pending', assignee: 'Dev-Agent' },
        { id: 4, name: '风格迁移模块', status: 'pending', assignee: 'Research-Agent' },
        { id: 5, name: '商业授权系统', status: 'pending', assignee: 'CTO-Agent' },
        { id: 6, name: '前端画廊', status: 'in_progress', assignee: 'UI-Agent', progress: 30 },
      ],
      metrics: {
        linesOfCode: 28900,
        testCoverage: 52,
        openIssues: 8,
        prsOpen: 2,
      },
      timeline: [
        { date: '2026-07-20', event: '项目立项', type: 'milestone' },
        { date: '2026-08-01', event: 'SDXL 本地部署完成', type: 'release' },
      ],
    },
    {
      id: 'token-platform',
      name: 'Token 充值平台',
      description: '多链 Token 充值聚合服务，支持 ETH/BSC/Arbitrum/Optimism/Base，自动汇率、Gas 优化、合规 KYC',
      status: 'planning' as const,
      progress: 10,
      assignee: 'CTO-Agent',
      team: ['CTO-Agent', 'Dev-Agent', 'Security-Agent', 'Trading-Agent'],
      model: 'nemotron-3-ultra:free (架构) + qwen2.5-coder:7b (实现)',
      repo: 'github.com/leo/token-platform',
      branch: 'main',
      lastCommit: 'Initial project structure',
      commits: 23,
      lastUpdate: Date.now() - 1000 * 60 * 60 * 24 * 3,
      estimatedCompletion: Date.now() + 1000 * 60 * 60 * 24 * 60,
      tasks: [
        { id: 1, name: '需求文档', status: 'in_progress', assignee: 'CTO-Agent', progress: 60 },
        { id: 2, name: '链适配器设计', status: 'pending', assignee: 'Dev-Agent' },
        { id: 3, name: '汇率聚合服务', status: 'pending', assignee: 'Trading-Agent' },
        { id: 3, name: 'Gas 优化引擎', status: 'pending', assignee: 'Dev-Agent' },
        { id: 4, name: 'KYC/AML 集成', status: 'pending', assignee: 'Security-Agent' },
        { id: 5, name: '管理后台', status: 'pending', assignee: 'UI-Agent' },
      ],
      metrics: {
        linesOfCode: 5400,
        testCoverage: 15,
        openIssues: 5,
        prsOpen: 1,
      },
      timeline: [
        { date: '2026-08-01', event: '项目立项', type: 'milestone' },
      ],
    },
    {
      id: 'translate-assistant',
      name: '翻译助手',
      description: '专业领域翻译工具，支持技术文档、代码注释、API 文档、法律合同多场景，术语库管理',
      status: 'active' as const,
      progress: 85,
      assignee: 'Dev-Agent',
      team: ['Dev-Agent', 'Research-Agent'],
      model: 'deepseek/deepseek-v4-flash (翻译) + qwen2.5:7b (术语提取)',
      repo: 'github.com/leo/translate-assistant',
      branch: 'main',
      lastCommit: 'Fix terminology sync bug',
      commits: 89,
      lastUpdate: Date.now() - 1000 * 60 * 45,
      estimatedCompletion: Date.now() + 1000 * 60 * 60 * 24 * 7,
      tasks: [
        { id: 1, name: '核心翻译引擎', status: 'completed', assignee: 'Dev-Agent' },
        { id: 2, name: '术语库管理', status: 'completed', assignee: 'Research-Agent' },
        { id: 3, name: '代码注释翻译', status: 'completed', assignee: 'Dev-Agent' },
        { id: 4, name: '批量文档翻译', status: 'in_progress', assignee: 'Dev-Agent', progress: 70 },
        { id: 5, name: '浏览器扩展', status: 'pending', assignee: 'UI-Agent' },
        { id: 6, name: '团队协作功能', status: 'pending', assignee: 'CTO-Agent' },
      ],
      metrics: {
        linesOfCode: 18400,
        testCoverage: 92,
        openIssues: 3,
        prsOpen: 0,
      },
      timeline: [
        { date: '2026-06-15', event: '项目立项', type: 'milestone' },
        { date: '2026-07-10', event: '核心引擎上线', type: 'release' },
        { date: '2026-08-01', event: '术语库上线', type: 'release' },
      ],
    },
  ], []);

  const statusColors = {
    active: 'bg-green-500/20 text-green-500 border-green-500/30',
    paused: 'bg-amber-500/20 text-amber-500 border-amber-500/30',
    completed: 'bg-blue-500/20 text-blue-500 border-blue-500/30',
    planning: 'bg-purple-500/20 text-purple-500 border-purple-500/30',
  };

  const filteredProjects = projects.filter(p => 
    filterStatus === 'all' || p.status === filterStatus
  );

  const stats = useMemo(() => ({
    total: projects.length,
    active: projects.filter(p => p.status === 'active').length,
    paused: projects.filter(p => p.status === 'paused').length,
    completed: projects.filter(p => p.status === 'completed').length,
    planning: projects.filter(p => p.status === 'planning').length,
    avgProgress: Math.round(projects.reduce((a, b) => a + b.progress, 0) / projects.length),
    totalLines: projects.reduce((a, b) => a + b.metrics.linesOfCode, 0),
    totalIssues: projects.reduce((a, b) => a + b.metrics.openIssues, 0),
  }), [projects]);

  return (
    <div className="p-4 lg:p-6 space-y-6">
      {/* 顶部统计 */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-8 gap-3"
      >
        <StatCard label="项目总数" value={stats.total} icon={<FolderGit2 className="w-5 h-5" />} color="ai-500" />
        <StatCard label="进行中" value={stats.active} icon={<Rocket className="w-5 h-5" />} color="green-500" />
        <StatCard label="暂停" value={stats.paused} icon={<AlertTriangle className="w-5 h-5" />} color="amber-500" />
        <StatCard label="已完成" value={stats.completed} icon={<CheckCircle className="w-5 h-5" />} color="blue-500" />
        <StatCard label="规划中" value={stats.planning} icon={<Target className="w-5 h-5" />} color="purple-500" />
        <StatCard label="平均进度" value={`${stats.avgProgress}%`} icon={<TrendingUp className="w-5 h-5" />} color="ai-500" />
        <StatCard label="总代码行" value={formatNumber(stats.totalLines)} icon={<Code className="w-5 h-5" />} color="amber-500" />
        <StatCard label="待解决问题" value={stats.totalIssues} icon={<AlertTriangle className="w-5 h-5" />} color="red-500" />
      </motion.div>

      {/* 工具栏 */}
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
              placeholder="搜索项目、描述、负责人..."
              className="w-full pl-10 pr-4 py-2 bg-surface-800/50 border border-surface-700 rounded-lg text-white placeholder-surface-500 focus:outline-none focus:border-ai-500"
            />
          </div>
          <select
            value={filterStatus}
            onChange={(e) => setFilterStatus(e.target.value as any)}
            className="px-4 py-2 bg-surface-800/50 border border-surface-700 rounded-lg text-white focus:outline-none focus:border-ai-500"
          >
            <option value="all">全部状态</option>
            <option value="active">进行中</option>
            <option value="paused">暂停</option>
            <option value="completed">已完成</option>
            <option value="planning">规划中</option>
          </select>
          <div className="flex gap-1">
            <button
              onClick={() => setViewMode('grid')}
              className={cn('p-2 rounded-lg', viewMode === 'grid' ? 'bg-ai-500/20 text-ai-500' : 'text-surface-400 hover:bg-surface-800/50')}
            >
              <div className="w-5 h-5 grid grid-cols-2 gap-1">
                <div className="bg-surface-600 rounded" /><div className="bg-surface-600 rounded" />
                <div className="bg-surface-600 rounded" /><div className="bg-surface-600 rounded" />
              </div>
            </button>
            <button
              onClick={() => setViewMode('list')}
              className={cn('p-2 rounded-lg', viewMode === 'list' ? 'bg-ai-500/20 text-ai-500' : 'text-surface-400 hover:bg-surface-800/50')}
            >
              <div className="w-5 h-5 flex flex-col gap-1">
                <div className="h-1 bg-surface-600 rounded w-full" /><div className="h-1 bg-surface-600 rounded w-full" />
                <div className="h-1 bg-surface-600 rounded w-full" />
              </div>
            </button>
          </div>
        </div>
        <div className="flex gap-2">
          <button className="btn-secondary">
            <RefreshCw className="w-4 h-4 mr-2" />
            刷新
          </button>
          <button className="btn-primary">
            <Plus className="w-4 h-4 mr-2" />
            新建项目
          </button>
        </div>
      </motion.div>

      {/* 项目网格/列表 */}
      <AnimatePresence mode="popLayout">
        {viewMode === 'grid' ? (
          <motion.div
            key="grid"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4"
          >
            {filteredProjects.map((project) => (
              <ProjectCard key={project.id} project={project} onClick={() => setActiveProject(project.id)} />
            ))}
          </motion.div>
        ) : (
          <motion.div
            key="list"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="glass-card overflow-hidden"
          >
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="text-left text-xs text-surface-500 uppercase tracking-wider bg-surface-800/50">
                    <th className="p-4">项目</th>
                    <th className="p-4">状态</th>
                    <th className="p-4">进度</th>
                    <th className="p-4">负责人</th>
                    <th className="p-4">模型</th>
                    <th className="p-4">代码行</th>
                    <th className="p-4">测试覆盖</th>
                    <th className="p-4">问题</th>
                    <th className="p-4">更新</th>
                    <th className="p-4">操作</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-surface-700/50">
                  {filteredProjects.map((project, i) => (
                    <tr key={project.id} className="hover:bg-surface-800/50">
                      <td className="p-4">
                        <div>
                          <p className="font-medium text-white truncate max-w-xs">{project.name}</p>
                          <p className="text-xs text-surface-500 truncate max-w-xs">{project.description}</p>
                        </div>
                      </td>
                      <td className="p-4">
                        <span className={`px-2 py-0.5 rounded text-xs font-medium ${statusColors[project.status]}`}>
                          {project.status === 'active' ? '进行中' : project.status === 'paused' ? '暂停' : project.status === 'completed' ? '已完成' : '规划中'}
                        </span>
                      </td>
                      <td className="p-4">
                        <div className="w-32 h-2 bg-surface-700 rounded-full overflow-hidden">
                          <motion.div
                            initial={{ width: 0 }}
                            animate={{ width: `${project.progress}%` }}
                            className="h-full bg-gradient-to-r from-ai-500 to-purple-500 rounded-full"
                            transition={{ duration: 0.5 }}
                          />
                        </div>
                        <span className="text-xs text-surface-500 ml-2">{project.progress}%</span>
                      </td>
                      <td className="p-4">
                        <div className="flex items-center gap-2">
                          <Bot className="w-4 h-4 text-ai-500" />
                          <span className="text-sm text-white">{project.assignee}</span>
                        </div>
                      </td>
                      <td className="p-4 text-sm text-surface-400 truncate max-w-[200px]">{project.model}</td>
                      <td className="p-4 font-mono text-surface-300">{formatNumber(project.metrics.linesOfCode)}</td>
                      <td className="p-4">
                        <span className={cn('px-2 py-0.5 rounded text-xs', 
                          project.metrics.testCoverage >= 80 ? 'bg-green-500/20 text-green-500' :
                          project.metrics.testCoverage >= 50 ? 'bg-amber-500/20 text-amber-500' : 'bg-red-500/20 text-red-500')}>
                          {project.metrics.testCoverage}%
                        </span>
                      </td>
                      <td className="p-4">
                        <span className={cn('px-2 py-0.5 rounded text-xs',
                          project.metrics.openIssues === 0 ? 'bg-green-500/20 text-green-500' :
                          project.metrics.openIssues <= 5 ? 'bg-amber-500/20 text-amber-500' : 'bg-red-500/20 text-red-500')}>
                          {project.metrics.openIssues}
                        </span>
                      </td>
                      <td className="p-4 text-xs text-surface-500">
                        {Math.round((Date.now() - project.lastUpdate) / 60000)} 分钟前
                      </td>
                      <td className="p-4">
                        <div className="flex items-center gap-1">
                          <button className="p-1.5 rounded hover:bg-surface-800 text-surface-400"><Edit className="w-4 h-4" /></button>
                          <button className="p-1.5 rounded hover:bg-surface-800 text-surface-400"><Trash2 className="w-4 h-4" /></button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* 项目详情模态框 */}
      <AnimatePresence>
        {activeProject && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm"
            onClick={() => setActiveProject(null)}
          >
            <motion.div
              initial={{ opacity: 0, scale: 0.95, y: 20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: 20 }}
              onClick={(e) => e.stopPropagation()}
              className="bg-surface-900/95 backdrop-blur-xl rounded-2xl border border-surface-700/50 w-full max-w-4xl max-h-[90vh] overflow-hidden flex flex-col"
            >
              <ProjectDetailModal project={projects.find(p => p.id === activeProject)!} onClose={() => setActiveProject(null)} />
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

function ProjectCard({ project, onClick }: { project: any; onClick: () => void }) {
  const statusColors = {
    active: 'bg-green-500/20 text-green-500 border-green-500/30',
    paused: 'bg-amber-500/20 text-amber-500 border-amber-500/30',
    completed: 'bg-blue-500/20 text-blue-500 border-blue-500/30',
    planning: 'bg-purple-500/20 text-purple-500 border-purple-500/30',
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={{ scale: 1.02, boxShadow: '0 10px 40px -10px rgba(6,182,212,0.2)' }}
      className={`glass-card p-5 cursor-pointer relative overflow-hidden ${statusColors[project.status]}`}
      onClick={onClick}
    >
      <div className="absolute top-0 right-0 w-2 h-full bg-gradient-to-b from-ai-500 to-purple-500 opacity-50" />
      
      <div className="flex items-start justify-between mb-4">
        <div className="p-3 rounded-xl bg-surface-800/50">
          <Bot className="w-6 h-6 text-ai-500" />
        </div>
        <span className={`px-2 py-1 rounded-full text-xs font-medium ${statusColors[project.status]}`}>
          {project.status === 'active' ? '进行中' : project.status === 'paused' ? '暂停' : project.status === 'completed' ? '已完成' : '规划中'}
        </span>
      </div>

      <h3 className="font-semibold text-white mb-1 truncate">{project.name}</h3>
      <p className="text-sm text-surface-500 mb-4 line-clamp-2">{project.description}</p>

      {/* 进度条 */}
      <div className="mb-4">
        <div className="flex items-center justify-between mb-1">
          <span className="text-xs text-surface-500">进度</span>
          <span className="text-xs font-mono text-ai-500">{project.progress}%</span>
        </div>
        <div className="h-2 bg-surface-700 rounded-full overflow-hidden">
          <motion.div
            initial={{ width: 0 }}
            animate={{ width: `${project.progress}%` }}
            className="h-full bg-gradient-to-r from-ai-500 to-purple-500 rounded-full"
            transition={{ duration: 0.5 }}
          />
        </div>
      </div>

      {/* 关键指标 */}
      <div className="grid grid-cols-3 gap-3 mb-4">
        <MetricMini label="代码行" value={formatNumber(project.metrics.linesOfCode)} color="amber-500" />
        <MetricMini label="测试覆盖" value={`${project.metrics.testCoverage}%`} color={project.metrics.testCoverage >= 80 ? 'green-500' : project.metrics.testCoverage >= 50 ? 'amber-500' : 'red-500'} />
        <MetricMini label="问题" value={project.metrics.openIssues} color={project.metrics.openIssues === 0 ? 'green-500' : project.metrics.openIssues <= 5 ? 'amber-500' : 'red-500'} />
      </div>

      {/* 团队与模型 */}
      <div className="space-y-2 text-sm">
        <div className="flex items-center gap-2 text-surface-400">
          <Bot className="w-4 h-4" />
          <span className="truncate max-w-[200px]">{project.model}</span>
        </div>
        <div className="flex items-center gap-2 text-surface-400">
          <Users className="w-4 h-4" />
          <span>{project.team.length} 人 · {project.assignee} 负责</span>
        </div>
        <div className="flex items-center gap-2 text-surface-400">
          <GitBranch className="w-4 h-4" />
          <span className="truncate max-w-[200px]">{project.repo} · {project.branch}</span>
        </div>
      </div>

      {/* 底部时间线 */}
      <div className="pt-4 border-t border-surface-700/50">
        <p className="text-xs text-surface-500">预计完成: {project.estimatedCompletion ? new Date(project.estimatedCompletion).toLocaleDateString() : '未设定'}</p>
      </div>
    </motion.div>
  );
}

function ProjectDetailModal({ project, onClose }: { project: any; onClose: () => void }) {
  return (
    <div className="flex flex-col h-full">
      {/* 头部 */}
      <div className="flex items-center justify-between p-6 border-b border-surface-700/50">
        <div className="flex items-center gap-4">
          <button onClick={onClose} className="p-2 rounded-lg hover:bg-surface-800 text-surface-400">
            <X className="w-5 h-5" />
          </button>
          <div>
            <div className="flex items-center gap-3">
              <div className="p-3 rounded-xl bg-surface-800/50">
                <Bot className="w-6 h-6 text-ai-500" />
              </div>
              <div>
                <h2 className="text-xl font-semibold text-white">{project.name}</h2>
                <span className={`px-3 py-1 rounded-full text-sm font-medium ${statusColors[project.status]}`}>
                  {project.status === 'active' ? '进行中' : project.status === 'paused' ? '暂停' : project.status === 'completed' ? '已完成' : '规划中'}
                </span>
              </div>
            </div>
            <p className="text-surface-400 mt-1">{project.description}</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <span className="px-3 py-1 text-xs bg-surface-800/50 text-surface-400 rounded">
            {formatNumber(project.metrics.linesOfCode)} 行
          </span>
          <span className="px-3 py-1 text-xs bg-surface-800/50 text-surface-400 rounded">
            {project.metrics.testCoverage}% 覆盖
          </span>
          <span className="px-3 py-1 text-xs bg-surface-800/50 text-surface-400 rounded">
            {project.metrics.openIssues} 问题
          </span>
        </div>
      </div>

      {/* 内容标签页 */}
      <div className="flex-1 overflow-y-auto p-6 space-y-6">
        <Tabs defaultValue="overview" onValueChange={setActiveTab}>
          <TabsList className="grid w-full grid-cols-5">
            <TabsTrigger value="overview">概览</TabsTrigger>
            <TabsTrigger value="tasks">任务 ({project.tasks.length})</TabsTrigger>
            <TabsTrigger value="timeline">时间线 ({project.timeline.length})</TabsTrigger>
            <TabsTrigger value="metrics">指标</TabsTrigger>
            <TabsTrigger value="team">团队</TabsTrigger>
          </TabsList>

          <TabsContent value="overview" className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <InfoCard label="仓库" value={<a href={`https://${project.repo}`} target="_blank" className="text-ai-500 hover:underline">{project.repo}</a>} icon={<GitBranch className="w-5 h-5" />} color="blue-500" />
              <InfoCard label="分支" value={project.branch} icon={<GitBranch className="w-5 h-5" />} color="ai-500" />
              <InfoCard label="最后提交" value={project.lastCommit} icon={<Clock className="w-5 h-5" />} color="amber-500" />
              <InfoCard label="提交数" value={project.commits} icon={<Zap className="w-5 h-5" />} color="purple-500" />
              <InfoCard label="预计完成" value={project.estimatedCompletion ? new Date(project.estimatedCompletion).toLocaleDateString() : '未设定'} icon={<Flag className="w-5 h-5" />} color="green-500" />
            </div>
            <div className="glass-card p-5">
              <h4 className="font-semibold mb-3">项目描述</h4>
              <p className="text-surface-300 whitespace-pre-wrap">{project.description}</p>
            </div>
          </TabsContent>

          <TabsContent value="tasks" className="space-y-4">
            <h4 className="font-semibold">任务列表 ({project.tasks.length})</h4>
            <div className="space-y-3">
              {project.tasks.map((task, i) => (
                <TaskRow key={i} task={task} index={i} />
              ))}
            </div>
          </TabsContent>

          <TabsContent value="timeline" className="space-y-4">
            <h4 className="font-semibold">时间线</h4>
            <Timeline events={project.timeline} />
          </TabsContent>

          <TabsContent value="metrics" className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <MetricCard label="代码行数" value={formatNumber(project.metrics.linesOfCode)} icon={<Code className="w-6 h-6" />} color="amber-500" />
            <MetricCard label="测试覆盖率" value={`${project.metrics.testCoverage}%`} icon={<CheckCircle className="w-6 h-6" />} color={project.metrics.testCoverage >= 80 ? 'green-500' : project.metrics.testCoverage >= 50 ? 'amber-500' : 'red-500'} />
            <MetricCard label="开放问题" value={project.metrics.openIssues} icon={<AlertTriangle className="w-6 h-6" />} color={project.metrics.openIssues === 0 ? 'green-500' : project.metrics.openIssues <= 5 ? 'amber-500' : 'red-500'} />
            <MetricCard label="打开 PR" value={project.metrics.prsOpen} icon={<GitBranch className="w-6 h-6" />} color="blue-500" />
          </TabsContent>

          <TabsContent value="team" className="space-y-4">
            <h4 className="font-semibold">团队成员 ({project.team.length})</h4>
            <div className="space-y-3">
              {project.team.map((member, i) => (
                <div key={i} className="flex items-center gap-4 p-3 glass-card">
                  <Bot className="w-8 h-8 text-ai-500" />
                  <div className="flex-1">
                    <p className="font-medium text-white">{member}</p>
                    <p className="text-xs text-surface-500">{member === project.assignee ? '项目负责人' : '团队成员'}</p>
                  </div>
                  {member === project.assignee && <span className="px-2 py-0.5 text-xs bg-ai-500/20 text-ai-500 rounded">Owner</span>}
                </div>
              ))}
            </div>
          </TabsContent>
        </TabsContent>
      </Tabs>
    </div>
  );
}

function TaskRow({ task, index }: { task: any; index: number }) {
  const statusStyles = {
    completed: 'bg-green-500/20 text-green-500 border-green-500/30',
    in_progress: 'bg-blue-500/20 text-blue-500 border-blue-500/30',
    pending: 'bg-surface-700/50 text-surface-400 border-surface-600',
  };
  const statusIcons = {
    completed: <CheckCircle className="w-4 h-4 text-green-500" />,
    in_progress: <Zap className="w-4 h-4 text-blue-500 animate-pulse" />,
    pending: <Clock className="w-4 h-4 text-surface-500" />,
  };

  return (
    <motion.div
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: index * 0.05 }}
      className="flex items-center gap-4 p-3 glass-card"
    >
      <div className={cn('w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0', statusStyles[task.status])}>
        {statusIcons[task.status]}
      </div>
      <div className="flex-1 min-w-0">
        <p className="font-medium text-white truncate">{task.name}</p>
        <div className="flex items-center gap-3 mt-1 text-xs">
          <span className="text-surface-400">{task.assignee}</span>
          {task.progress !== undefined && (
            <span className="text-ai-500">{task.progress}%</span>
          )}
        </div>
      </div>
      <span className={cn('px-3 py-1 rounded-full text-xs font-medium', statusStyles[task.status])}>
        {task.status === 'completed' ? '已完成' : task.status === 'in_progress' ? '进行中' : '待办'}
      </span>
    </motion.div>
  );
}

function Timeline({ events }: { events: any[] }) {
  return (
    <div className="relative pl-6 border-l border-surface-700/50">
      {events.map((event, i) => (
        <motion.div
          key={i}
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: i * 0.1 }}
          className="relative pb-8"
        >
          <div className="absolute left-[-22px] top-1 w-3 h-3 rounded-full bg-ai-500 border-2 border-surface-900" />
          <div className="ml-4">
            <p className="text-xs text-surface-500">{new Date(event.date).toLocaleDateString()}</p>
            <p className="font-medium text-white">{event.event}</p>
            <span className={cn('px-2 py-0.5 rounded text-xs', 
              event.type === 'milestone' && 'bg-purple-500/20 text-purple-500',
              event.type === 'release' && 'bg-green-500/20 text-green-500'
            )}>
              {event.type}
            </span>
          </div>
        </motion.div>
      ))}
    </div>
  );
}

function InfoCard({ label, value, icon, color }: { label: string; value: React.ReactNode; icon: React.ReactNode; color: string }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="glass-card p-5"
    >
      <div className="flex items-center gap-3 mb-2">
        <div className={cn('p-2 rounded-lg', `bg-${color}/20 text-${color}`)}>
          {icon}
        </div>
        <p className="text-xs text-surface-500 uppercase tracking-wide">{label}</p>
      </div>
      <div>{value}</div>
    </motion.div>
  );
}

function Tabs({ defaultValue, onValueChange, children }: { defaultValue: string; onValueChange: (v: string) => void; children: React.ReactNode }) {
  const [value, setValue] = useState(defaultValue);
  const ctx = { value, onValueChange: (v: string) => { setValue(v); onValueChange(v); } };
  return (
    <TabsContext.Provider value={ctx}>
      <div>{children}</div>
    </TabsContext.Provider>
  );
}

const TabsContext = React.createContext<{ value: string; onValueChange: (v: string) => void } | null>(null);

function TabsList({ children }: { children: React.ReactNode }) {
  return <div className="flex gap-1 bg-surface-800/50 rounded-lg p-1 mb-6">{children}</div>;
}

function TabsTrigger({ value, children }: { value: string; children: React.ReactNode }) {
  const { value: currentValue, onValueChange } = React.useContext(TabsContext)!;
  return (
    <button
      onClick={() => onValueChange(value)}
      className={cn(
        'px-4 py-2 rounded-lg text-sm font-medium transition-all',
        value === currentValue
          ? 'bg-ai-500/20 text-white border border-ai-500/30'
          : 'text-surface-400 hover:bg-surface-800/50 hover:text-white'
      )}
    >
      {children}
    </button>
  );
}

function TabsContent({ value, children }: { value: string; children: React.ReactNode }) {
  const { value: currentValue } = React.useContext(TabsContext)!;
  if (value !== currentValue) return null;
  return <div>{children}</div>;
}

function MetricMini({ label, value, color }: { label: string; value: string | number; color: string }) {
  return (
    <div className="text-center p-2 rounded-lg bg-surface-800/50">
      <p className="text-xs text-surface-500">{label}</p>
      <p className={cn('font-mono font-medium', `text-${color}`)}>{value}</p>
    </div>
  );
}

function StatCard({ label, value, icon, color }: { label: string; value: number; icon: React.ReactNode; color: string }) {
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