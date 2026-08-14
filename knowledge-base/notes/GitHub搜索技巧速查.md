# 🧰 GitHub 百宝箱 — 搜索技巧速查

> 来源: William说 GitHub百宝箱教程 + Leo 分享技巧
> 用途: 用 GitHub 搜索找项目/资源/平替软件

## 核心搜索语法

| 语法 | 作用 | 示例 |
|------|------|------|
| `in:name 关键词` | 仓库名匹配 | `in:name trading-bot` |
| `in:description 关键词` | 描述匹配 | `in:description ai agent` |
| `in:readme 关键词` | README 匹配 | `in:readme openclaw` |
| `stars:>500` | 星数过滤(高质量) | `in:description 网格交易 stars:>500` |
| `language:Python` | 语言过滤 | `topic:crypto language:Python` |
| `topic:xxx` | 主题标签 | `topic:quant-trading` |
| `pushed:>2025-01-01` | 最近更新 | `in:name bot pushed:>2025-01-01` |
| `user:xxx` | 指定用户 | `user:li77724121` |
| `org:xxx` | 指定组织 | `org:okx` |

## 组合使用（精准搜索）

```
# 找高质量的 AI 抄币机器人
in:description crypto trading bot stars:>1000 language:Python pushed:>2024

# 找 Hermes/OpenClaw 技能
in:name hermes skill stars:>10

# 找收费软件平替
in:readme 替代 photoshop OR illustrator

# 找刚更新的大项目
topic:ai-agent pushed:>2026-06-01 stars:>200
```

## 链接

- GitHub 官网: https://github.com
- HelloGitHub (每月精选): https://hellogithub.com
- William说工具箱: https://r.williamsays.site/links

## 小技巧

- GitHub 不支持中文名搜索 → 用浸泡翻译插件, 连点3个空格直接翻译英文
- `in:name+搜名字` = 精准搜仓库名
- 高星 = 高质量, 优先看 stars:>500
