// ============================================================
// Event Bus - 核心事件总线
// 统一事件分发，支持同步/异步、优先级、重试、死信队列
// ============================================================

import type { EventMap, UUID, Timestamp } from '@shared/types';
import { EventEmitter } from 'eventemitter3';

type EventName = keyof EventMap;
type EventData<T extends EventName> = EventMap[T];

type Listener<T extends EventName> = (data: EventData<T>) => void | Promise<void>;
type Middleware = (event: string, data: unknown, next: () => void) => void;

interface Subscription {
  id: UUID;
  event: EventName;
  listener: Listener<EventName>;
  priority: number;
  once: boolean;
  filter?: (data: unknown) => boolean;
}

interface DeadLetterEntry {
  event: string;
  data: unknown;
  error: Error;
  timestamp: Timestamp;
  retries: number;
}

export class EventBus extends EventEmitter<EventMap> {
  private subscriptions = new Map<EventName, Subscription[]>();
  private middlewares: Middleware[] = [];
  private deadLetterQueue: DeadLetterEntry[] = [];
  private maxDeadLetterSize = 1000;
  private processing = false;
  private eventLog: Array<{ event: string; data: unknown; timestamp: Timestamp }> = [];
  private maxEventLogSize = 10000;

  // 优先级常量
  static PRIORITY_HIGH = 100;
  static PRIORITY_NORMAL = 50;
  static PRIORITY_LOW = 10;

  // 发射事件（支持中间件、过滤、优先级、异常处理）
  async emit<T extends EventName>(
    event: T,
    data: EventData<T>
  ): Promise<number> {
    const timestamp = Date.now();
    const fullEvent = `event:${event}` as const;

    // 记录事件日志
    this.eventLog.push({ event, data, timestamp });
    if (this.eventLog.length > this.maxEventLogSize) {
      this.eventLog.shift();
    }

    // 执行中间件链
    let cancelled = false;
    const next = () => { cancelled = true; };
    for (const mw of this.middlewares) {
      mw(event, data, next);
      if (cancelled) return 0;
    }

    // 获取订阅者，按优先级排序
    const subs = this.subscriptions.get(event) || [];
    if (subs.length === 0) {
      // 也触发原生 EventEmitter（向后兼容）
      super.emit(event, data);
      return 0;
    }

    const sortedSubs = [...subs].sort((a, b) => b.priority - a.priority);
    let executed = 0;

    for (const sub of sortedSubs) {
      try {
        // 过滤器检查
        if (sub.filter && !sub.filter(data)) continue;

        await sub.listener(data);
        executed++;

        // once 订阅执行后移除
        if (sub.once) {
          this.unsubscribe(sub.id);
        }
      } catch (error) {
        console.error(`[EventBus] Listener error for ${event}:`, error);
        this.addToDeadLetter(event, data, error as Error);
      }
    }

    // 也触发原生 EventEmitter
    super.emit(event, data);

    return executed;
  }

  // 同步发射（不等待异步 listener）
  emitSync<T extends EventName>(event: T, data: EventData<T>): number {
    const subs = this.subscriptions.get(event) || [];
    if (subs.length === 0) {
      super.emit(event, data);
      return 0;
    }

    let executed = 0;
    for (const sub of subs) {
      if (sub.filter && !sub.filter(data)) continue;
      try {
        const result = sub.listener(data);
        if (result instanceof Promise) {
          // 异步 listener 在同步模式下不等待
          result.catch(err => console.error(`[EventBus] Async listener error:`, err));
        }
        executed++;
        if (sub.once) this.unsubscribe(sub.id);
      } catch (error) {
        console.error(`[EventBus] Sync listener error for ${event}:`, error);
        this.addToDeadLetter(event, data, error as Error);
      }
    }
    super.emit(event, data);
    return executed;
  }

  // 订阅事件
  subscribe<T extends EventName>(
    event: T,
    listener: Listener<T>,
    options: {
      priority?: number;
      once?: boolean;
      filter?: (data: EventData<T>) => boolean;
    } = {}
  ): UUID {
    const id = crypto.randomUUID() as UUID;
    const sub: Subscription = {
      id,
      event,
      listener: listener as Listener<EventName>,
      priority: options.priority ?? EventBus.PRIORITY_NORMAL,
      once: options.once ?? false,
      filter: options.filter as ((data: unknown) => boolean) | undefined,
    };

    const existing = this.subscriptions.get(event) || [];
    existing.push(sub);
    this.subscriptions.set(event, existing);

    return id;
  }

  // 取消订阅
  unsubscribe(id: UUID): boolean {
    for (const [event, subs] of this.subscriptions.entries()) {
      const idx = subs.findIndex(s => s.id === id);
      if (idx !== -1) {
        subs.splice(idx, 1);
        if (subs.length === 0) {
          this.subscriptions.delete(event);
        }
        return true;
      }
    }
    return false;
  }

  // 取消某事件的所有订阅
  unsubscribeAll(event?: EventName): void {
    if (event) {
      this.subscriptions.delete(event);
    } else {
      this.subscriptions.clear();
    }
  }

  // 添加中间件
  use(middleware: Middleware): () => void {
    this.middlewares.push(middleware);
    return () => {
      const idx = this.middlewares.indexOf(middleware);
      if (idx !== -1) this.middlewares.splice(idx, 1);
    };
  }

  // 死信队列
  private addToDeadLetter(event: string, data: unknown, error: Error): void {
    this.deadLetterQueue.push({
      event,
      data,
      error,
      timestamp: Date.now(),
      retries: 0,
    });
    if (this.deadLetterQueue.length > this.maxDeadLetterSize) {
      this.deadLetterQueue.shift();
    }
  }

  getDeadLetterQueue(): DeadLetterEntry[] {
    return [...this.deadLetterQueue];
  }

  retryDeadLetter(index: number): boolean {
    const entry = this.deadLetterQueue[index];
    if (!entry) return false;

    entry.retries++;
    if (entry.retries > 3) return false;

    this.emit(entry.event as EventName, entry.data).catch(console.error);
    return true;
  }

  clearDeadLetter(): void {
    this.deadLetterQueue = [];
  }

  // 事件日志
  getEventLog(limit = 100): Array<{ event: string; data: unknown; timestamp: Timestamp }> {
    return this.eventLog.slice(-limit);
  }

  clearEventLog(): void {
    this.eventLog = [];
  }

  // 调试信息
  getStats(): {
    subscriptions: number;
    events: string[];
    middlewares: number;
    deadLetterSize: number;
    eventLogSize: number;
  } {
    return {
      subscriptions: Array.from(this.subscriptions.values()).reduce((a, b) => a + b.length, 0),
      events: Array.from(this.subscriptions.keys()),
      middlewares: this.middlewares.length,
      deadLetterSize: this.deadLetterQueue.length,
      eventLogSize: this.eventLog.length,
    };
  }
}

// 单例实例
export const eventBus = new EventBus();

// 类型安全的订阅钩子（React 用）
export function createEventHook<T extends EventName>(
  event: T,
  listener: (data: EventMap[T]) => void,
  options?: { priority?: number; once?: boolean; filter?: (data: EventMap[T]) => boolean }
) {
  let subscriptionId: UUID | null = null;

  const subscribe = () => {
    if (subscriptionId) return;
    subscriptionId = eventBus.subscribe(event, listener, options);
  };

  const unsubscribe = () => {
    if (subscriptionId) {
      eventBus.unsubscribe(subscriptionId);
      subscriptionId = null;
    }
  };

  return { subscribe, unsubscribe, get id() { return subscriptionId; } };
}

// 常用事件的快捷钩子
export const hooks = {
  onAgentUpdate: (listener: (data: EventMap['agent:updated']) => void, opts?: { filter?: (d: EventMap['agent:updated']) => boolean }) =>
    createEventHook('agent:updated', listener, { priority: EventBus.PRIORITY_HIGH, ...opts }),

  onSystemMetrics: (listener: (data: EventMap['metrics:system']) => void) =>
    createEventHook('metrics:system', listener, { priority: EventBus.PRIORITY_NORMAL }),

  onOKXMetrics: (listener: (data: EventMap['metrics:okx']) => void) =>
    createEventHook('metrics:okx', listener, { priority: EventBus.PRIORITY_HIGH }),

  onOpenRouterMetrics: (listener: (data: EventMap['metrics:openrouter']) => void) =>
    createEventHook('metrics:openrouter', listener, { priority: EventBus.PRIORITY_HIGH }),

  onNASMetrics: (listener: (data: EventMap['metrics:nas']) => void) =>
    createEventHook('metrics:nas', listener, { priority: EventBus.PRIORITY_NORMAL }),

  onAlert: (listener: (data: EventMap['alert:created']) => void) =>
    createEventHook('alert:created', listener, { priority: EventBus.PRIORITY_HIGH }),

  onGovernanceRequest: (listener: (data: EventMap['governance:request']) => void) =>
    createEventHook('governance:request', listener, { priority: EventBus.PRIORITY_HIGH }),

  onAgentStatusChange: (listener: (data: EventMap['agent:status-changed']) => void) =>
    createEventHook('agent:status-changed', listener, { priority: EventBus.PRIORITY_HIGH }),
};