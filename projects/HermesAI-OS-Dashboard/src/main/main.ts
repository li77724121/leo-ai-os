// ============================================================
// Electron Main Process
// Hermes AI OS Dashboard - 主进程
// ============================================================

import { app, BrowserWindow, ipcMain, dialog, shell, Menu, Tray, nativeImage } from 'electron';
import { join, resolve } from 'path';
import { existsSync, readFileSync, writeFileSync, mkdirSync } from 'fs';
import { spawn, ChildProcess } from 'child_process';
import { eventBus } from '@shared/eventBus';
import type { DashboardConfig, SystemMetrics, OKXMetrics, OpenRouterMetrics, NASMetrics, VSCodeMetrics, ApprovalRequest, Alert } from '@shared/types';

const isDev = process.env.NODE_ENV === 'development';
const configPath = join(app.getPath('userData'), 'dashboard-config.json');

// ---- 配置管理 ----
function loadConfig(): DashboardConfig {
  try {
    if (existsSync(configPath)) {
      return JSON.parse(readFileSync(configPath, 'utf-8'));
    }
  } catch {}
  return DEFAULT_CONFIG;
}

function saveConfig(config: DashboardConfig): void {
  try {
    const dir = join(configPath, '..');
    if (!existsSync(dir)) mkdirSync(dir, { recursive: true });
    writeFileSync(configPath, JSON.stringify(config, null, 2));
  } catch (e) {
    console.error('Failed to save config:', e);
  }
}

let config = loadConfig();
let mainWindow: BrowserWindow | null = null;
let tray: Tray | null = null;

// ---- 数据源监控进程 ----
interface MonitorProcess {
  type: string;
  process: ChildProcess;
  lastData: unknown;
  connected: boolean;
}

const monitors = new Map<string, MonitorProcess>();

// 启动监控子进程
function startMonitor(type: string, script: string): void {
  const proc = spawn('tsx', [script], {
    cwd: resolve(__dirname, '../..'),
    env: { ...process.env, NODE_ENV: isDev ? 'development' : 'production' },
    stdio: ['ignore', 'pipe', 'pipe'],
  });

  const monitor: MonitorProcess = { type, process: proc, lastData: null, connected: false };
  monitors.set(type, monitor);

  proc.stdout?.on('data', (data) => {
    try {
      const lines = data.toString().trim().split('\n');
      for (const line of lines) {
        if (!line) continue;
        const parsed = JSON.parse(line);
        monitor.lastData = parsed;
        monitor.connected = true;
        // 通过 EventBus 分发
        eventBus.emitSync(`metrics:${type}` as any, parsed);
      }
    } catch (e) {
      // 忽略非 JSON 行
    }
  });

  proc.stderr?.on('data', (data) => {
    console.error(`[Monitor:${type}]`, data.toString());
  });

  proc.on('close', (code) => {
    monitor.connected = false;
    console.log(`[Monitor:${type}] exited with code ${code}`);
    // 自动重启
    setTimeout(() => startMonitor(type, script), 5000);
  });

  proc.on('error', (err) => {
    console.error(`[Monitor:${type}] spawn error:`, err);
  });
}

// ---- IPC 处理 ----
function setupIPC(): void {
  // 配置
  ipcMain.handle('config:get', () => config);
  ipcMain.handle('config:set', async (_e, partial: Partial<DashboardConfig>) => {
    config = { ...config, ...partial };
    saveConfig(config);
    return config;
  });

  // 系统信息
  ipcMain.handle('system:getMetrics', async () => {
    // 这里返回最新缓存或实时采集
    const sysMon = monitors.get('system');
    return sysMon?.lastData || null;
  });

  // 打开外部链接
  ipcMain.handle('shell:openExternal', async (_e, url: string) => {
    await shell.openExternal(url);
  });

  // 显示对话框
  ipcMain.handle('dialog:showMessageBox', async (_e, options: Electron.MessageBoxOptions) => {
    if (!mainWindow) return { response: 0 };
    return dialog.showMessageBox(mainWindow, options);
  });

  // 审批请求
  ipcMain.handle('governance:approve', async (_e, requestId: string, approver: string) => {
    eventBus.emit('governance:approved', { requestId, approvedBy: approver });
    return { success: true };
  });

  ipcMain.handle('governance:reject', async (_e, requestId: string, approver: string, reason: string) => {
    eventBus.emit('governance:rejected', { requestId, rejectedBy: approver, reason });
    return { success: true };
  });

  // 获取事件总线统计
  ipcMain.handle('eventbus:stats', () => eventBus.getStats());

  // 窗口控制
  ipcMain.handle('window:minimize', () => mainWindow?.minimize());
  ipcMain.handle('window:maximize', () => {
    if (mainWindow?.isMaximized()) mainWindow.unmaximize();
    else mainWindow?.maximize();
  });
  ipcMain.handle('window:close', () => mainWindow?.close());
  ipcMain.handle('window:isMaximized', () => mainWindow?.isMaximized() ?? false);

  // 开发工具
  ipcMain.handle('dev:toggleDevTools', () => {
    mainWindow?.webContents.toggleDevTools();
  });
}

// ---- 创建主窗口 ----
function createMainWindow(): BrowserWindow {
  const iconPath = resolve(__dirname, '../../assets/icon.png');

  mainWindow = new BrowserWindow({
    width: 1600,
    height: 1000,
    minWidth: 1200,
    minHeight: 800,
    title: 'Hermes AI OS - Command Center',
    icon: existsSync(iconPath) ? iconPath : undefined,
    webPreferences: {
      preload: join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: true,
      webSecurity: true,
    },
    titleBarStyle: 'hiddenInset',
    trafficLightPosition: { x: 16, y: 16 },
    backgroundColor: '#020617',
    show: false,
  });

  // 加载页面
  if (isDev) {
    mainWindow.loadURL('http://localhost:5173');
    mainWindow.webContents.openDevTools({ mode: 'detach' });
  } else {
    mainWindow.loadFile(join(__dirname, '../renderer/index.html'));
  }

  mainWindow.once('ready-to-show', () => {
    mainWindow?.show();
  });

  mainWindow.on('closed', () => {
    mainWindow = null;
  });

  return mainWindow;
}

// ---- 系统托盘 ----
function createTray(): void {
  const icon = nativeImage.createEmpty(); // 占位，实际需提供图标
  tray = new Tray(icon);
  tray.setToolTip('Hermes AI OS');

  const contextMenu = Menu.buildFromTemplate([
    { label: '显示面板', click: () => mainWindow?.show() },
    { label: '最小化到托盘', click: () => mainWindow?.hide() },
    { type: 'separator' },
    { label: '退出', click: () => app.quit() },
  ]);

  tray.setContextMenu(contextMenu);
  tray.on('double-click', () => mainWindow?.show());
}

// ---- 应用生命周期 ----
app.whenReady().then(() => {
  setupIPC();
  createMainWindow();
  createTray();

  // 启动监控进程（生产环境）
  if (!isDev) {
    // TODO: 实际部署时启动各监控脚本
    // startMonitor('system', 'src/monitors/system.ts');
    // startMonitor('okx', 'src/monitors/okx.ts');
    // startMonitor('openrouter', 'src/monitors/openrouter.ts');
    // startMonitor('nas', 'src/monitors/nas.ts');
    // startMonitor('vscode', 'src/monitors/vscode.ts');
  }

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) createMainWindow();
  });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit();
});

app.on('before-quit', () => {
  // 清理监控进程
  for (const [, monitor] of monitors) {
    monitor.process.kill();
  }
});

// 单实例锁
const gotTheLock = app.requestSingleInstanceLock();
if (!gotTheLock) {
  app.quit();
} else {
  app.on('second-instance', () => {
    if (mainWindow) {
      if (mainWindow.isMinimized()) mainWindow.restore();
      mainWindow.focus();
    }
  });
}

// 导出配置用于预加载脚本
export { config, eventBus };