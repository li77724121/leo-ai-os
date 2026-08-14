// ============================================================
// Hermes AI OS Dashboard - Shared Types
// 核心类型定义，全项目共享
// ============================================================

// ---- 基础类型 ----
export type UUID = string & { readonly __brand: unique symbol };
export const uuid = (): UUID => crypto.randomUUID() as UUID;

export type Timestamp = number; // Unix ms

// ---- 状态枚举 ----
export enum AgentStatus {
  Working = 'working',
  Waiting = 'waiting',
  Idle = 'idle',
  Error = 'error',
  Learning = 'learning',
}

export enum ConnectionStatus {
  Connected = 'connected',
  Connecting = 'connecting',
  Disconnected = 'disconnected',
  Error = 'error',
}

// ---- 核心实体 ----
export interface Agent {
  id: UUID;
  name: string;
  role: string;
  status: AgentStatus;
  currentTask?: Task;
  model: string;
  provider: string;
  tokenUsage: TokenUsage;
  tools: ToolCall[];
  metrics: AgentMetrics;
  lastUpdate: Timestamp;
}

export interface Task {
  id: UUID;
  name: string;
  description: string;
  progress: number; // 0-100
  startedAt: Timestamp;
  estimatedEnd?: Timestamp;
}

export interface TokenUsage {
  prompt: number;
  completion: number;
  total: number;
  cost: number; // USD
  cacheHit?: number;
}

export interface ToolCall {
  id: UUID;
  name: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  startedAt: Timestamp;
  endedAt?: Timestamp;
  error?: string;
}

export interface AgentMetrics {
  cpu: number;      // %
  ram: number;      // MB
  callsPerMin: number;
  avgLatency: number; // ms
  errorRate: number;  // %
}

// ---- 数据源连接 ----
export interface DataSource {
  id: string;
  name: string;
  type: DataSourceType;
  status: ConnectionStatus;
  lastSync: Timestamp;
  config: Record<string, unknown>;
}

export enum DataSourceType {
  Hermes = 'hermes',
  VSCode = 'vscode',
  OpenRouter = 'openrouter',
  Ollama = 'ollama',
  OKX = 'okx',
  NAS = 'nas',
  System = 'system',
}

// ---- 监控数据 ----
export interface SystemMetrics {
  cpu: number;           // %
  ram: { used: number; total: number }; // MB
  disk: { used: number; total: number }; // GB
  network: { up: number; down: number }; // MB/s
  gpu?: { usage: number; memory: number };
  battery?: { level: number; charging: boolean };
  temperature?: number; // °C
  timestamp: Timestamp;
}

export interface OpenRouterMetrics {
  currentModel: string;
  fallbackModel: string;
  providers: ProviderStatus[];
  requestsPerMin: number;
  latency: { p50: number; p95: number; p99: number };
  rateLimits: RateLimitInfo;
  timestamp: Timestamp;
}

export interface ProviderStatus {
  name: string;
  status: ConnectionStatus;
  latency: number;
  models: string[];
}

export interface RateLimitInfo {
  remaining: number;
  resetAt: Timestamp;
  limit: number;
}

export interface OKXMetrics {
  positions: Position[];
  totalPnL: number;
  dailyPnL: number;
  riskLevel: 'low' | 'medium' | 'high' | 'critical';
  apiStatus: ConnectionStatus;
  strategies: StrategyStatus[];
  timestamp: Timestamp;
}

export interface Position {
  symbol: string;
  side: 'long' | 'short';
  size: number;
  entryPrice: number;
  markPrice: number;
  pnl: number;
  pnlPct: number;
  liquidationPrice?: number;
}

export interface StrategyStatus {
  name: string;
  status: 'running' | 'paused' | 'error';
  signals: Signal[];
}

export interface Signal {
  symbol: string;
  action: 'buy' | 'sell' | 'hold';
  confidence: number;
  price: number;
  timestamp: Timestamp;
}

export interface NASMetrics {
  cpu: number;
  ram: { used: number; total: number };
  disk: { used: number; total: number };
  docker: DockerContainer[];
  syncStatus: 'synced' | 'syncing' | 'error';
  backupStatus: BackupStatus;
  knowledgeBase: { documents: number; size: number };
  timestamp: Timestamp;
}

export interface DockerContainer {
  id: string;
  name: string;
  status: 'running' | 'exited' | 'paused' | 'restarting';
  cpu: number;
  memory: number;
  ports: string[];
}

export interface BackupStatus {
  lastBackup: Timestamp;
  nextBackup: Timestamp;
  status: 'completed' | 'running' | 'failed';
  size: number;
}

export interface VSCodeMetrics {
  workspace: string;
  git: { branch: string; status: string; ahead: number; behind: number };
  terminal: TerminalOutput[];
  build: BuildStatus;
  debug: DebugStatus;
  test: TestStatus;
  aiEdits: AIEdit[];
  currentFile: string;
  timestamp: Timestamp;
}

export interface TerminalOutput {
  id: UUID;
  command: string;
  output: string;
  exitCode: number;
  timestamp: Timestamp;
}

export interface BuildStatus {
  status: 'idle' | 'building' | 'success' | 'failed';
  lastBuild: Timestamp;
  duration?: number;
  errors: string[];
}

export interface DebugStatus {
  active: boolean;
  breakpoints: number;
  watchExpressions: string[];
}

export interface TestStatus {
  total: number;
  passed: number;
  failed: number;
  skipped: number;
  lastRun: Timestamp;
}

export interface AIEdit {
  file: string;
  type: 'insert' | 'delete' | 'replace';
  lines: number;
  timestamp: Timestamp;
}

// ---- 事件系统 ----
export type EventMap = {
  // 核心系统事件
  'system:startup': { timestamp: Timestamp };
  'system:shutdown': { timestamp: Timestamp };
  'system:error': { error: Error; context: string };

  // Agent 事件
  'agent:created': { agent: Agent };
  'agent:updated': { agent: Agent; changes: Partial<Agent> };
  'agent:deleted': { agentId: UUID };
  'agent:status-changed': { agentId: UUID; oldStatus: AgentStatus; newStatus: AgentStatus };
  'agent:task-started': { agentId: UUID; task: Task };
  'agent:task-progress': { agentId: UUID; progress: number };
  'agent:task-completed': { agentId: UUID; task: Task };
  'agent:token-update': { agentId: UUID; usage: TokenUsage };
  'agent:tool-call': { agentId: UUID; tool: ToolCall };
  'agent:error': { agentId: UUID; error: Error };

  // 数据源事件
  'datasource:connected': { source: DataSource };
  'datasource:disconnected': { sourceId: string; reason: string };
  'datasource:data': { sourceId: string; data: unknown };
  'datasource:error': { sourceId: string; error: Error };

  // 监控数据事件
  'metrics:system': { metrics: SystemMetrics };
  'metrics:openrouter': { metrics: OpenRouterMetrics };
  'metrics:okx': { metrics: OKXMetrics };
  'metrics:nas': { metrics: NASMetrics };
  'metrics:vscode': { metrics: VSCodeMetrics };

  // OKX 交易事件
  'okx:position-opened': { position: Position };
  'okx:position-closed': { position: Position; pnl: number };
  'okx:signal': { signal: Signal };
  'okx:strategy-status': { strategy: StrategyStatus };

  // Governance 审批事件
  'governance:request': { request: ApprovalRequest };
  'governance:approved': { requestId: UUID; approvedBy: string };
  'governance:rejected': { requestId: UUID; rejectedBy: string; reason: string };
  'governance:executed': { requestId: UUID; result: unknown };

  // 告警事件
  'alert:created': { alert: Alert };
  'alert:acknowledged': { alertId: UUID; by: string };
  'alert:resolved': { alertId: UUID };
}

// ---- 审批系统 ----
export enum ApprovalType {
  DeleteFile = 'delete_file',
  ReadSecret = 'read_secret',
  ModifySystem = 'modify_system',
  ExecuteShell = 'execute_shell',
  GitPush = 'git_push',
  RealTrade = 'real_trade',
  ThirdPartyInstall = 'third_party_install',
  FundOperation = 'fund_operation',
}

export enum ApprovalStatus {
  Pending = 'pending',
  Approved = 'approved',
  Rejected = 'rejected',
  Executed = 'executed',
  Expired = 'expired',
}

export interface ApprovalRequest {
  id: UUID;
  type: ApprovalType;
  title: string;
  description: string;
  riskLevel: 'low' | 'medium' | 'high' | 'critical';
  requestedBy: string; // agent name or 'user'
  requestedAt: Timestamp;
  expiresAt: Timestamp;
  status: ApprovalStatus;
  context: Record<string, unknown>;
  approvers: string[]; // 可批准的角色/人员
  approvals: ApprovalRecord[];
}

export interface ApprovalRecord {
  approver: string;
  decision: 'approve' | 'reject';
  reason?: string;
  timestamp: Timestamp;
}

// ---- 告警系统 ----
export enum AlertSeverity {
  Info = 'info',
  Warning = 'warning',
  Critical = 'critical',
}

export enum AlertStatus {
  Active = 'active',
  Acknowledged = 'acknowledged',
  Resolved = 'resolved',
}

export interface Alert {
  id: UUID;
  severity: AlertSeverity;
  title: string;
  message: string;
  source: string; // datasource or component
  metadata: Record<string, unknown>;
  status: AlertStatus;
  createdAt: Timestamp;
  acknowledgedAt?: Timestamp;
  acknowledgedBy?: string;
  resolvedAt?: Timestamp;
}

// ---- 配置 ----
export interface DashboardConfig {
  refreshIntervals: {
    system: number;      // ms
    agents: number;
    metrics: number;
    logs: number;
  };
  websocket: {
    url: string;
    reconnectInterval: number;
    maxRetries: number;
  };
  ui: {
    theme: 'dark' | 'light' | 'system';
    animations: boolean;
    compactMode: boolean;
  };
  alerts: {
    sound: boolean;
    desktop: boolean;
    retentionDays: number;
  };
}

// ---- 默认配置 ----
export const DEFAULT_CONFIG: DashboardConfig = {
  refreshIntervals: {
    system: 5000,
    agents: 2000,
    metrics: 3000,
    logs: 1000,
  },
  websocket: {
    url: 'ws://localhost:8765',
    reconnectInterval: 5000,
    maxRetries: 10,
  },
  ui: {
    theme: 'dark',
    animations: true,
    compactMode: false,
  },
  alerts: {
    sound: true,
    desktop: true,
    retentionDays: 30,
  },
};