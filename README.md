# 🦞 Leo AI OS — 开源协作项目

> 一个人 + AI 的完整操作系统: 多任务监控大屏、知识库流水线、AI 抄币网格机器人
> 欢迎大家一起开发！🤝

## 📦 项目列表

### 1. 🖥️ ops-dashboard — 多任务监控可视化大屏
5 屏实时监控: Hermes / 极空间NAS / VS Code+Cline / 实时事件流 / 控制中台(OKX交易)
- Flask + WebSocket + 多进程采集器
- CSS 动画显示系统活跃状态 (呼吸/扫描/雷达)
- 一键部署, launchd 守护

**技术栈**: Python, Flask, WebSocket, vanilla JS

### 2. 📚 knowledge-base — 知识库流水线
把微信收藏/链接/PDF 自动提炼为 Obsidian 双链笔记
- inbox → 提取正文 → AI 提炼(摘要/标签/要点) → 双链 Markdown
- 微信文章专属解析 (js_content)
- OpenRouter 免费模型 / Ollama 本地兜底

**技术栈**: Python, pdfplumber, Ollama, OpenRouter API

### 3. 💰 trading_bot — AI 网格抄币机器人 (OKX)
SOL/USDT 网格交易, 自动低买高卖
- 7层网格 $70-85, 每层 $15 (可配置)
- 风控: 止损 8% / 止盈 25% / 最大持仓限制
- 每笔成交 Telegram 实时提醒
- 完整日志 + 监控大屏

**技术栈**: Python, OKX API v5, Telegram Bot

## 🚀 快速开始

```bash
# 1. 克隆仓库
git clone https://github.com/li77724121/leo-ai-os.git
cd leo-ai-os

# 2. 配置环境变量 (复制模板, 填入你的 key)
cp trading_bot/.env.example trading_bot/.env

# 3. 启动监控大屏
cd ops-dashboard && python3 server.py
# 打开 http://localhost:8800

# 4. 启动知识库流水线
cd ../knowledge-base && python3 knowledge_pipeline.py

# 5. 启动网格机器人 (需要 OKX API key)
cd ../trading_bot && python3 grid_trader.py
```

## 🤝 如何参与开发

1. **Fork** 这个仓库
2. **Clone** 到本地: `git clone https://github.com/你的名字/leo-ai-os.git`
3. **创建分支**: `git checkout -b feature/你的功能`
4. **提交**: `git commit -m "✨ 添加XX功能"`
5. **Push**: `git push origin feature/你的功能`
6. **提 PR**: 在 GitHub 上创建 Pull Request

## 📋 待开发功能 (欢迎认领)

- [ ] 大屏: 极空间深度监控 (CPU/Docker/存储)
- [ ] 大屏: Cline 任务进度条
- [ ] 大屏: 控制中台一键启停各系统
- [ ] 知识库: 支持更多文件类型 (Word/网页存档)
- [ ] 交易: 多币种网格 (ETH/BTC)
- [ ] 交易: K线趋势判断增强
- [ ] 交易: 移动端远程控制

## 🛡️ 安全说明

- 所有 API key / 密码 / token **永不明文提交**
- 使用 `.env` 文件存储敏感信息 (已 gitignore)
- 代码中只用环境变量引用

## 📄 License

MIT License — 自由使用, 注明出处即可
