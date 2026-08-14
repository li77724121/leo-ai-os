// ============================================================
// Preload Script
// 安全暴露 Electron API 给渲染进程
// ============================================================

import { contextBridge, ipcRenderer, IpcRendererEvent } from 'electron';
import type { DashboardConfig, ApprovalRequest, Alert } from '@shared/types';

// 类型安全的 IPC 调用
const invoke = <T>(channel: string, ...args: unknown[]): Promise<T> =>
  ipcRenderer.invoke(channel, ...args);

const on = <T>(channel: string, listener: (event: IpcRendererEvent, ...args: unknown[]) => void) => {
  ipcRenderer.on(channel, listener);
  return () => ipcRenderer.removeListener(channel, listener);
};

const off = (channel: string, listener: (...args: unknown[]) => void) => {
  ipcRenderer.removeListener(channel, listener);
};

// 安全暴露的 API
contextBridge.exposeInMainWorld('electron', {
  // 配置
  config: {
    get: () => invoke<DashboardConfig>('config:get'),
    set: (partial: Partial<DashboardConfig>) => invoke<DashboardConfig>('config:set', partial),
  },

  // 系统
  system: {
    getMetrics: () => invoke<any>('system:getMetrics'),
  },

  // Shell
  shell: {
    openExternal: (url: string) => invoke<void>('shell:openExternal', url),
  },

  // 对话框
  dialog: {
    showMessageBox: (options: Electron.MessageBoxOptions) =>
      invoke<Electron.MessageBoxReturnValue>('dialog:showMessageBox', options),
  },

  // 审批
  governance: {
    approve: (requestId: string, approver: string) =>
      invoke<{ success: boolean }>('governance:approve', requestId, approver),
    reject: (requestId: string, approver: string, reason: string) =>
      invoke<{ success: boolean }>('governance:reject', requestId, approver, reason),
  },

  // 窗口控制
  window: {
    minimize: () => invoke<void>('window:minimize'),
    maximize: () => invoke<void>('window:maximize'),
    close: () => invoke<void>('window:close'),
    isMaximized: () => invoke<boolean>('window:isMaximized'),
  },

  // 事件总线统计
  eventBus: {
    getStats: () => invoke<any>('eventbus:stats'),
  },

  // 开发工具
  dev: {
    toggleDevTools: () => invoke<void>('dev:toggleDevTools'),
  },

  // 事件监听（单向：主进程 -> 渲染进程）
  on: {
    governanceRequest: (listener: (request: ApprovalRequest) => void) =>
      on('governance:request', (_e, request) => listener(request)),
    alert: (listener: (alert: Alert) => void) =>
      on('alert:created', (_e, alert) => listener(alert)),
    metricsUpdate: (listener: (data: any) => void) =>
      on('metrics:update', (_e, data) => listener(data)),
  },

  off: (channel: string, listener: (...args: any[]) => void) => off(channel, listener),
});

// 类型声明
export type ElectronAPI = typeof electronAPI;
declare global {
  interface Window {
    electron: ElectronAPI;
  }
}

// 防止被篡改
Object.freeze(window.electron);