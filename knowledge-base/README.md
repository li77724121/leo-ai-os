# 📚 Hermes 知识库流水线

> 把微信收藏/链接/PDF/文本 自动变成 Obsidian 双链笔记
> 源自文章: 极空间+微信快存+Hermes 自动把网页变成双链笔记

## 工作流

```
inbox/ (放资料)
   ├── .pdf     → pdfplumber 提取文本
   ├── .url     → 抓取网页 (微信文章提取 js_content)
   ├── .txt/.md → 直接读取
   └── 图片      → 标记待视觉解析
        ↓
OpenRouter 免费模型 (默认) / Ollama llama3.2:1b (兜底)
   ↓ 提炼: 摘要 + 标签 + 关键词 + 要点
        ↓
notes/ (Obsidian 双链 Markdown)
   ├── YAML frontmatter (title/date/type/source/summary/tags)
   ├── 摘要 + 双链标签 [[tag]]
   └── 原文摘录
        ↓
原文件移入 processed/ (归档)
```

## 使用

```bash
# 放资料到 inbox
cp article.pdf ~/leo-ai-os/knowledge-base/inbox/
echo "https://example.com" > ~/leo-ai-os/knowledge-base/inbox/网页链接.url

# 手动处理
cd ~/leo-ai-os/knowledge-base
python3 knowledge_pipeline.py           # 云端免费模型 (推荐)
python3 knowledge_pipeline.py --local   # 本地模型 (0 成本但质量低)
python3 knowledge_pipeline.py --dry     # 试运行
python3 knowledge_pipeline.py --force   # 忽略已处理记录
```

## 定时任务

- cron: **知识库增量整理** (每 30 分钟)
- 检查 inbox 是否有新文件, 有则自动处理
- 已处理文件记录在 processed.json, 不会重复

## 目录结构

```
~/leo-ai-os/knowledge-base/
├── inbox/          # 待处理资料 (放这里)
├── notes/          # 生成的 Obsidian 笔记
├── processed/      # 已处理归档
├── logs/           # 运行日志
├── processed.json  # 已处理状态
└── knowledge_pipeline.py
```

## 模型策略

| 模型 | 成本 | 质量 | 场景 |
|------|------|------|------|
| OpenRouter 免费 (默认) | ¥0 | 高 | 正常提炼 |
| Ollama llama3.2:1b | ¥0 | 低 | 云端不可用兜底 |

## 用 Obsidian 打开

1. Obsidian → Open folder as vault → 选 `~/leo-ai-os/knowledge-base/notes/`
2. 双链笔记自动显示标签关系图
3. 或同步到 GitHub 私有仓库做多端访问
