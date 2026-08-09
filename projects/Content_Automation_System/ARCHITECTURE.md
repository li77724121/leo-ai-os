# Content Automation System - Architecture

> 版本：v1.0
> 目标：跑通「选题→生产→分发→变现」全自动化闭环
> 核心原则：MVP 优先、低成本验证、可复制、可规模化

---

## 1. 系统总览

```
┌─────────────────────────────────────────────────────────────────┐
│                  CONTENT AUTOMATION SYSTEM                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │  IDEATION    │  │  PRODUCTION  │  │ DISTRIBUTION │          │
│  │  (选题策划)   │──│  (内容生产)   │──│  (多渠道分发) │          │
│  │              │  │              │  │              │          │
│  │ • Trend Radar│  │ • Script Gen │  │ • TikTok     │          │
│  │ • Keyword    │  │ • Video Edit │  │ • Instagram  │          │
│  │   Research   │  │ • Thumbnail  │  │ • YouTube    │          │
│  │ • Topic      │  │ • Caption    │  │ • X/Twitter  │          │
│  │   Scoring    │  │ • Hashtags   │  │ • LinkedIn   │          │
│  │ • Calendar   │  │ • Schedule   │  │ • Cross-post │          │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘          │
│         │                 │                 │                   │
│         └─────────────────┼─────────────────┘                   │
│                           ▼                                     │
│              ┌────────────────────────┐                         │
│              │    MONETIZATION        │                         │
│              │    (变现闭环)           │                         │
│              │                        │                         │
│              │ • Affiliate Links      │                         │
│              │ • Digital Products     │                         │
│              │ • Course Sales         │                         │
│              │ • Community Membership │                         │
│              │ • Ad Revenue Share     │                         │
│              └───────────┬────────────┘                         │
│                          │                                       │
│                           ▼                                     │
│              ┌────────────────────────┐                         │
│              │    ANALYTICS & OPT     │                         │
│              │    (数据复盘优化)       │                         │
│              │                        │                         │
│              │ • Performance Dash     │                         │
│              │ • A/B Test Framework   │                         │
│              │ • ROI Attribution      │                         │
│              │ • Auto Parameter Tune  │                         │
│              └────────────────────────┘                         │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. 赛道选择框架

### 2.1 评估维度 (1-10分)

| 维度 | 权重 | 说明 |
|------|------|------|
| **市场需求** | 25% | 搜索量、趋势增长、竞品密度 |
| **变现路径** | 25% | 客单价、转化率、复购率、LTV |
| **内容护城河** | 20% | 技术门槛、品牌壁垒、数据积累 |
| **生产效率** | 15% | AI 可替代度、批量化程度、边际成本 |
| **个人契合度** | 15% | 知识储备、兴趣持续度、资源获取 |

### 2.2 候选赛道评估

| 赛道 | 需求(25%) | 变现(25%) | 护城河(20%) | 效率(15%) | 契合(15%) | 总分 | 备注 |
|------|-----------|-----------|-------------|-----------|-----------|------|------|
| **AI 工具评测/教程** | 9 | 8 | 6 | 9 | 9 | **8.2** | ✅ 首选 |
| **加密货币教育/工具** | 8 | 9 | 7 | 7 | 8 | **7.9** | ✅ 备选 |
| **语言学习/陪练** | 7 | 7 | 8 | 6 | 9 | **7.4** | Bandu 协同 |
| **AI 编程/提示词工程** | 8 | 8 | 7 | 8 | 9 | **8.0** | ✅ 强相关 |
| **数字游民/远程工作** | 6 | 6 | 5 | 7 | 7 | **6.2** | 观望 |
| **个人知识管理/PKM** | 7 | 6 | 7 | 8 | 8 | **7.1** | 长尾 |

### 2.3 决策：**主攻 AI 工具评测/教程 + AI 编程/提示词工程，辅以加密教育**

理由：
1. 与现有技术栈（Hermes、Ollama、MCP、OKX）强关联
2. AI 可高度自动化生产（脚本、代码、截图、视频剪辑）
3. 变现路径清晰：Affiliate + 数字产品 + 社群 + 课程
4. 可复用 Bandu 的多语言能力做国际化

---

## 3. 内容生产流水线

### 3.1 标准化内容单元

```yaml
# 单条内容完整规格
content_unit:
  id: "ai_tool_review_2025_001"
  type: "video_short"  # video_short / video_long / article / carousel / thread
  topic: "Claude Code vs Cursor 深度对比"
  angle: "实战测试：用 AI 写一个完整的交易系统"
  
  # 生产要素
  production:
    script: "scripts/claude_vs_cursor.md"
    raw_footage: "footage/claude_cursor_test/*.mp4"
    b_roll: "assets/broll/coding/*.mp4"
    screenshots: "assets/screenshots/claude_cursor/*.png"
    thumbnail: "thumbnails/claude_vs_cursor_v1.png"
    caption: "captions/claude_vs_cursor.md"
    hashtags: ["#AIcoding", "#ClaudeCode", "#Cursor", "#程序员效率"]
    
  # 分发配置
  distribution:
    tiktok:
      aspect: "9:16"
      duration_limit: 180
      hook_first_3s: true
    instagram_reels:
      aspect: "9:16"
      duration_limit: 90
    youtube_shorts:
      aspect: "9:16"
      duration_limit: 60
    youtube_long:
      aspect: "16:9"
      duration_limit: 1200
      chapters: true
    x_thread:
      format: "thread"
      tweet_count: 8
    linkedin:
      format: "article"
      professional_tone: true
      
  # 变现挂载
  monetization:
    affiliate_links:
      - platform: "cursor"
        url: "https://cursor.sh/?ref=leo"
        commission: "20% first year"
      - platform: "anthropic"
        url: "https://console.anthropic.com/?ref=leo"
    digital_product: "AI编程提示词库 v3.0"
    course_upsell: "AI全栈开发实战营"
    community_cta: "加入 AI Builder 社群"
    
  # 追踪指标
  tracking:
    utm_source: "tiktok|ig|yt|x|li"
    utm_medium: "organic"
    utm_campaign: "ai_tool_review_2025_q3"
    utm_content: "claude_vs_cursor_v1"
```

### 3.2 AI 自动化生产链

```
选题输入 → [LLM] → 选题评分/大纲 → [人工确认] → 
剧本生成 → [LLM + 模板] → 完整分镜脚本 → 
素材收集 → [自动化] → 屏幕录制/截图/素材库检索 → 
视频剪辑 → [模板+参数] → 剪映/Shotcut/Remotion 自动剪辑 → 
包装输出 → [批量] → 多规格导出(9:16/16:9/1:1) + 字幕/封面/标题 → 
分发排期 → [API] → 多平台定时发布 + 评论区挂链 → 
数据回收 → [API] → 统一看板 → 复盘优化
```

---

## 4. 工具链选型

| 环节 | 首选工具 | 备选 | 自动化程度 |
|------|----------|------|------------|
| **选题雷达** | Google Trends API + TikTok Creative Center + 爆款库 | Exploding Topics, Glimpse | 80% |
| **关键词挖掘** | Ahrefs/SEMrush API + AnswerThePublic | KeywordTool.io | 70% |
| **剧本生成** | Claude 3.5 Sonnet / GPT-4o + 结构化模板 | 本地 qwen2.5-coder | 90% |
| **屏幕录制** | macOS 自带 + OBS 自动化脚本 | CleanShot X | 60% |
| **AI 视频剪辑** | **Remotion (React+代码剪辑)** → 首选 | 剪映国际版 API / Shotcut MLT XML | **95%** |
| **缩略图生成** | DALL-E 3 / Midjourney + 模板合成 | Canva API | 85% |
| **字幕/翻译** | Whisper + VideoLingo | 火山引擎/腾讯云 | 90% |
| **多平台发布** | **自建发布器 (Playwright/Puppeteer)** | Buffer/Hootsuite/Later API | **80%** |
| **数据聚合** | 各平台官方 API + Webhook | Social Blade / Phlanx | 70% |

**核心决策：Remotion 作为视频剪辑核心** —— 代码即配置、版本可控、批量渲染、参数化模板、CI/CD 集成。

---

## 5. 变现产品矩阵

| 产品类型 | 具体形态 | 定价 | 边际成本 | 交付自动化 |
|----------|----------|------|----------|------------|
| **引流免费品** | AI工具对比表、提示词模板、Notion模板 | Free | 0 | 100% |
| **低价数字产品** | 《AI编程提示词库》PDF/Notion | $9.9-$29.9 | 0 | 100% |
| **中价课程** | 《AI全栈开发实战营》录播+社群 | $99-$299 | 低 | 90% |
| **高价服务** | 1v1 AI工作流定制咨询 | $500+/hr | 高 | 30% |
| **持续订阅** | AI Builder 社群（月费/年费） | $29/mo | 低 | 80% |
| **Affiliate** | Cursor/Claude/Notion/各类SaaS | 佣金 | 0 | 100% |

**漏斗设计**：
```
短视频 (百万曝光) 
    → 免费资源领取 (转化 3-5%) 
        → 邮件序列/私域 (打开率 40%) 
            → 低价产品 (转化 5-10%) 
                → 中价课程 (转化 10-20%) 
                    → 高价服务/社群 (转化 5-10%)
```

---

## 6. 实施路线图

### Phase 1: MVP 验证 (Week 1-2)
- [ ] 搭建 Remotion 视频剪辑模板系统
- [ ] 制作 3 条 AI 工具对比短视频（Claude vs Cursor / 本地模型部署 / MCP 实战）
- [ ] 手动发布到 TikTok/Reels/Shorts/X
- [ ] 验证：单条视频 1k+ 播放、完播率 > 30%、引流转化

### Phase 2: 自动化生产 (Week 3-4)
- [ ] 选题→剧本→剪辑参数 全自动化流水线
- [ ] 批量渲染多规格视频（9:16/16:9/1:1）
- [ ] 自动生成标题/标签/封面/字幕
- [ ] 定时发布器（Playwright 无头浏览器）

### Phase 3: 变现闭环 (Week 5-6)
- [ ] 搭建 Gumroad/LemonSqueezy 数字产品交付
- [ ] 邮件自动化序列（ConvertKit/Beehiiv）
- [ ] 免费资源→低价产品漏斗
- [ ] Affiliate 链接追踪体系

### Phase 4: 规模化 (Week 7-12)
- [ ] 多账号矩阵（主号+垂类号+切片号）
- [ ] A/B 测试框架（钩子/封面/标题/时长/发布时间）
- [ ] 数据驱动选题（复盘爆款特征→反哺选题雷达）
- [ ] 国际化：VideoLingo 多语言配音 → 全球发布

---

## 7. 关键指标仪表盘

### 北极星指标
- **MRR (Monthly Recurring Revenue)** - 核心业务健康度

### 领先指标
| 指标 | 目标 | 统计周期 |
|------|------|----------|
| 视频产出量 | 21 条/周 (3条/天) | 周 |
| 平均完播率 | > 35% (短视频) | 条 |
| 互动率 (赞+评+藏/播放) | > 5% | 条 |
| 引流点击率 (简介链接/评论区) | > 2% | 条 |
| 邮件订阅转化 | > 3% (播放→订阅) | 周 |

### 滞后指标
| 指标 | 目标 | 统计周期 |
|------|------|----------|
| 免费资源下载量 | > 100/周 | 周 |
| 低价产品销量 | > 20 单/周 | 周 |
| 课程销售额 | > $1,000/月 | 月 |
| 社群付费成员 | > 50 人 | 月 |
| MRR | > $3,000 | 月 |

---

## 8. 文件结构规划

```
/Users/leo/Desktop/leohermes/02_Projects/Content_Automation_System/
├── ARCHITECTURE.md              # 本文件
├── README.md                    # 使用指南
├── config/
│   ├── topics.yaml              # 选题库与评分
│   ├── channels.yaml            # 渠道配置
│   ├── monetization.yaml        # 变现产品配置
│   └── schedule.yaml            # 发布排期
├── content/
│   ├── ideation/                # 选题/大纲/剧本
│   ├── scripts/                 # 结构化剧本模板
│   ├── raw/                     # 原始素材
│   └── final/                   # 成品视频
├── products/
│   ├── freebies/                # 免费引流品
│   ├── digital/                 # 数字产品
│   ├── courses/                 # 课程大纲/素材
│   └── community/               # 社群运营
├── distribution/
│   ├── publisher/               # 发布器核心代码
│   ├── scheduler/               # 定时任务
│   └── adapters/                # 各平台适配器
├── analytics/
│   ├── dashboard/               # 看板代码
│   ├── ab_test/                 # A/B 测试框架
│   └── attribution/             # 归因分析
├── prompts/                     # 提示词库
│   ├── ideation/                # 选题/大纲 prompts
│   ├── script/                  # 剧本生成 prompts
│   ├── caption/                 # 文案/标签 prompts
│   └── thumbnail/               # 缩略图 prompts
├── scripts/                     # 运维/批量脚本
│   ├── batch_render.py
│   ├── batch_publish.py
│   └── sync_analytics.py
└── remotion/                    # Remotion 视频项目
    ├── src/
    │   ├── templates/           # 视频模板组件
    │   ├── compositions/        # 合成配置
│   └── package.json
```

---

## 9. 下一步行动

1. **今日**：初始化 Remotion 项目，制作第一个通用视频模板（标题+正文+代码展示+结尾CTA）
2. **明日**：完成 3 个选题的剧本生成（用 Claude + 结构化 Prompt）
3. **后天**：录制素材 + Remotion 批量渲染 + 手动发布验证
4. **本周末**：复盘数据，决定是否进入 Phase 2 自动化开发

---

*本系统遵循「先验证、再扩张，先赚钱、再完善」原则。所有自动化投入必须有数据支撑 ROI。*