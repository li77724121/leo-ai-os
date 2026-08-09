import React, { createContext, useContext, useEffect, useRef, useState, ReactNode } from 'react';
import { eventBus, hooks } from '@shared/eventBus';
import type { SystemMetrics, OKXMetrics, OpenRouterMetrics, NASMetrics, ApprovalRequest, Alert } from '@shared/types';

interface EventBusState {
  systemMetrics: any;
  okxMetrics: any;
  openRouterMetrics: any;
  nasMetrics: any;
  governanceRequests: any[];
  alerts: any[];
  lastUpdate: number;
}

const initialState: EventBusState = {
  systemMetrics: null,
  okxMetrics: null,
  openRouterMetrics: null,
  nasMetrics: null,
  governanceRequests: [],
  alerts: [],
  lastUpdate: 0,
};

const EventBusContext = createContext<{
  state: EventBusState;
  subscribe: () => void;
  unsubscribe: () => void;
} | null>(null);

export function EventBusProvider({ children }: { children: React.ReactNode }) {
  const [state, setState] = useState<EventBusState>(() => ({
    systemMetrics: null,
    okxMetrics: null,
    openRouterMetrics: null,
    nasMetrics: null,
    governanceRequests: [],
    alerts: [],
    lastUpdate: 0,
  }));

  const unsubRefs = useRef<(() => void)[]>([]);

  const subscribe = useRef(() => {
    // 系统指标
    const unsubSystem = hooks.onSystemMetrics((data) => {
      setState(s => ({ ...s, systemMetrics: data, lastUpdate: Date.now() }));
    }).subscribe();

    // OKX 指标
    const unsubOKX = hooks.onOKXMetrics((data) => {
      setState(s => ({ ...s, okxMetrics: data, lastUpdate: Date.now() }));
    }).subscribe();

    // OpenRouter 指标
    const unsubOR = hooks.onOpenRouterMetrics((data) => {
      setState(s => ({ ...s, openRouterMetrics: data, lastUpdate: Date.now() }));
    }).subscribe();

    // NAS 指标
    const unsubNAS = hooks.onNASMetrics((data) => {
      setState(s => ({ ...s, nasMetrics: data, lastUpdate: Date.now() }));
    }).subscribe();

    // 治理请求
    const unsubGov = hooks.onGovernanceRequest((data) => {
      setState(s => ({
        ...s,
        governanceRequests: [data, ...s.governanceRequests.slice(0, 49)],
        lastUpdate: Date.now(),
      }));
    }).subscribe();

    // 告警
    const unsubAlert = hooks.onAlert((data) => {
      setState(s => ({
        ...s,
        alerts: [data, ...s.alerts.slice(0, 99)],
        lastUpdate: Date.now(),
      }));
    }).subscribe();

    // Agent 状态变化
    const unsubAgent = hooks.onAgentStatusChange((data) => {
      setState(s => ({ ...s, lastUpdate: Date.now() }));
    }).subscribe();

    unsubRefs.current = [
      () => unsubSystem(),
      () => unsubOKX(),
      () => unsubOR(),
      () => unsubNAS(),
      () => unsubGov(),
      () => unsubAlert(),
      () => unsubAgent(),
    ];
  }, []);

  const unsubscribe = useRef(() => {
    unsubRefs.current.forEach(unsub => unsub());
    unsubRefs.current = [];
  }, []);

  useEffect(() => {
    subscribe.current();
    return () => unsubscribe.current();
  }, []);

  return (
    <EventBusContext.Provider value={{ state, subscribe: subscribe.current, unsubscribe: unsubscribe.current }}>
      {children}
    </EventBusContext.Provider>
  );
}

export function useEventBus() {
  const context = useContext(EventBusContext);
  if (!context) throw new Error('useEventBus must be used within EventBusProvider');
  return context;
}

// 专用 Hook
export function useSystemMetrics() {
  const { state } = useEventBus();
  return state.systemMetrics;
}

export function useOKXMetrics() {
  const { state } = useEventBus();
  return state.okxMetrics;
}

export function useOpenRouterMetrics() {
  const { state } = useEventBus();
  return state.openRouterMetrics;
}

export function useNASMetrics() {
  const { state } = useEventBus();
  return state.nasMetrics;
}

export function useGovernanceRequests() {
  const { state } = useEventBus();
  return state.governanceRequests;
}

export function useAlerts() {
  const { state } = useEventBus();
  return state.alerts;
}