---
title: "链接: https://mp.weixin.qq.com/s/l54lcYwsYYZAvWWJUv4Qsw"
date: 2026-08-06
type: link
source: "极空间微信快存Hermes知识库.url"
summary: "A complete, low‑maintenance knowledge‑base workflow that automates collecting articles, links, and files into Jike Space, converting them to PDF, extracting summaries, tags, and double‑linked notes via Hermes Agent, and syncing everything into Obsidian (or via free alternatives). Users only need to forward content and check results, while scheduled tasks let Hermes incrementally update the knowledge base."
tags: ["knowledge base", "automation", "Jike Space", "WeChat Quick Save", "Hermes Agent", "Obsidian", "private cloud", "PDF conversion", "double‑linked notes", "AI assistant", "sync", "cron tasks"]
keywords: ["knowledge base automation", "Jike Space private cloud", "WeChat Quick Save PDF", "Hermes Agent extraction", "Obsidian Headless", "Feishu CLI", "SMB/WebDav mount", "double‑link notes", "incremental sync", "Skill automation"]
---

# 链接: https://mp.weixin.qq.com/s/l54lcYwsYYZAvWWJUv4Qsw

## 📝 摘要
A complete, low‑maintenance knowledge‑base workflow that automates collecting articles, links, and files into Jike Space, converting them to PDF, extracting summaries, tags, and double‑linked notes via Hermes Agent, and syncing everything into Obsidian (or via free alternatives). Users only need to forward content and check results, while scheduled tasks let Hermes incrementally update the knowledge base.

## 🔖 标签
[[knowledge base]]
[[automation]]
[[Jike Space]]
[[WeChat Quick Save]]
[[Hermes Agent]]

## 🎯 要点
1. Use **WeChat Quick Save** (Jike Space app) to archive articles, links, and files; it auto‑generates PDFs with original formatting.
2. Deploy **Hermes Agent** via Jike Space’s App Center: set a storage path, configure as Feishu Agent, and let it read PDFs to produce Markdown notes with summaries, semantic tags, and association discovery in a double‑linked format.
3. Store notes in **Obsidian** (or via free alternatives) for a searchable, editable knowledge‑base UI; sync options include Obsidian subscription + Headless, SMB/WebDav mounting, or Feishu CLI sync.
4. Schedule a cron job for Hermes to run daily, automatically ingesting new PDFs and updating the Obsidian repo—no manual processing required.
5. Turn successful extraction patterns into reusable Hermes **Skills** for repeatable pipelines (e.g., extracting YAML, feature lists, keyword tags).
6. The whole system needs only content forwarding from the user; Hermes handles storage, processing, and syncing, turning scattered collections into a structured, AI‑ready knowledge asset.

## 📄 原文摘录
各位极友，我是小极君 📚  
   你是不是也这样：微信里收藏了一堆“干货文章”，电脑里存了无数 PDF，手机相册全是截图……等到真正想用的时候，却翻不到、记不住、理不清？  
    
   今天  @可爱的小cherry&nbsp;  给大家分享一套完整的知识库自动化工作流——     极空间 + 微信快存 + Hermes Agent + Obsidian     。  
      微信快存     ：把公众号文章、链接、文件一键转存到极空间，自动生成 PDF  

     Hermes Agent     ：读取 PDF，自动提炼摘要、打标签、生成双链笔记  

     Obsidian     ：作为知识库的展示和编辑终端，笔记自动同步、随时检索  

     
   最棒的是，整套流程可以设置     定时任务     ，让 Hermes 每天自动增量整理，你只需要负责“转发”和“查看结果”。如果想让收藏夹里的资料真正变成你的知识资产，这篇教程值得一看。👇  
    
  最近，我试了一下基于极空间私有云的完整知识库工作流搭建。流程包括从资料收集，到知识库搭建，到 AI 专属知识库助手，走下来非常顺畅，而且不需要维护，Hermes 可以自动获取资料来生成双链笔记，并进行同步。 
       这一套流程，今天分享出来，希望可以为大家日常使用极空间私有云搭建知识库，提供一种新的思路和参考。 
  整套流程使用的工具如下： 
       • 极空间 —— 应用中心 微信快存    
     • 极空间 —— 应用中心 Hermes Agent    
     • 飞书 CLI（方案A）    
     • Obsidian Headless （方案B）    
    其中关于飞书 CLI、Obsidian 在极空间的 Hermes 里如何持久化存储，可以看我前面写的一篇关于 Hermes 利用 Hook 优化环境变量的文章。 
   一、安装 Hermes Agent  
  如果你之前安装过 Openclaw、Hermes 等通用型 Agent 的，那么这一步就不用看了，直接往下拉。 
  如果你没安装过，那么建议直接部署极空间应用中心自带的 Hermes Agent。 
       安装的时候会让你选一个存储路径，后续我们所有的知识库也同样会存放在这个 Hermes 的路径下面。 
       接着点击 SSH 界面，输入&nbsp;   Hermes Setup   &nbsp;进行 Agent 配置，默认第一个选择&nbsp;   Quick   &nbsp;回车，然后模型里根据你现在购买的 Code Plan 套餐选择对应的 Provider 。 
       然后剩下的都是默认的回车一直下去，直到来到&nbsp;   Message Configure   &nbsp;这栏选择&nbsp;   Feishu/lark   。 
       选第一个，然后飞书客户端打开扫一下就可以创建对应的飞书 Agent 智能体。 
        二、知识库资料采集方案  
  这一步主要依赖极空间内的    微信快存    应用。它是一个基于企业微信会话存档功能定制开发的服务。安装以后可以通过企业微信将资料存档到极空间 NAS 里。 
       安装完成以后需要进入微信快存的配置页面，这里最重要的是要把文件存储位置修改到 Hermes 的存储路径里，我单独取了一个名字就叫&nbsp;   wechat   

---
*由 Hermes 知识库流水线自动生成 · 2026-08-06 13:34*
