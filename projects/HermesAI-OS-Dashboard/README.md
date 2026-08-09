# Leo AI Command Center V1

**企业级 AI 公司实时监控大屏 — 数字孪生指挥中心**

## 🚀 快速启动

```bash
# 1. 安装依赖（首次）
npm install

# 2. 启动开发服务器
npm run dev

# 或使用启动脚本
./start.sh
```

访问: http://localhost:5173 （开发模式）

## 📊 功能模块

| 大厅 | 功能 |
|------|------|
| **Command** | 指挥中心 — 核心指标 + 数据源状态 + OKX 仓位 + OpenRouter 模型 |
| **3D 孪生** | 3D 数字公司地图 — CEO办公室/CTO研发中心/AI数据中心 |
| **Hermes** | Agent 实时监控 — 状态/任务/Token/工具调用 |
| **VS Code** | 开发环境 — Workspace/Git/Terminal/Build/Debug/Test |
| **OKX** | 交易监控 — 仓位/策略/风控/信号/历史（只读+人工确认） |
| **Project** | 项目中心 — PowerAI/AI制图/Token平台/翻译助手 |

## 🏗 架构

```
Dashboard (React + Vite + Tailwind + Three.js + Framer Motion)
    ↓
Event Bus (事件总线 - 类型安全)
    ↓
数据源适配器 (Hermes / VSCode / OKX / OpenRouter / Ollama / NAS / System)
    ↓
WebSocket / REST API / Log Stream
```

## 🛡 安全设计

- **Governance 审批队列**: 高风险动作（资金/删除/系统修改）必须人工批准
- **只读监控**: OKX 只做分析/提醒/统计，真实交易需 Telegram 人工确认
- **低资源占用**: 事件驱动 + 虚拟列表 + 懒加载，适配 8GB MacBook

## 📁 项目结构

```
HermesAI-OS-Dashboard/
├── src/
│   ├── main/           # Electron 主进程
│   ├── renderer/       # React 前端
│   │   ├── pages/      # 六大屏页面
│   │   ├── components/ # 3D 孪生等组件
│   │   ├── context/    # EventBus/Config
│   │   └── lib/        # 工具函数
│   └── shared/         # 类型定义 + 事件总线
├── start.sh            # 启动脚本
└── package.json
```

## 🧠 技术栈

- React 18 + TypeScript
- Vite 5
- TailwindCSS 3
- Three.js + React Three Fiber（3D）
- Framer Motion（动画）
- Zustand + EventBus（状态管理）
- Electron 31（桌面打包）
