#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
📚 Hermes 知识库流水线 (Knowledge Pipeline)
把 inbox 里的资料 (PDF/链接/文本/图片) 自动提炼为 Obsidian 双链笔记

流程:
  1. 扫描 inbox/ 目录
  2. 解析文件类型 (PDF / URL链接 / txt / md)
  3. 提取正文内容
  4. 本地 Ollama 提炼: 摘要 + 标签 + 关联发现
  5. 生成 Obsidian 格式 Markdown (YAML frontmatter + 双链)
  6. 移入 notes/ 并记录 processed 状态

用法:
  python3 knowledge_pipeline.py          # 处理 inbox 全部资料
  python3 knowledge_pipeline.py --dry    # 只解析不生成
  python3 knowledge_pipeline.py --force  # 忽略已处理记录
"""
import os
import re
import sys
import json
import time
import uuid
import shutil
import urllib.request
from pathlib import Path
from datetime import datetime

# ========== 配置 ==========
BASE = Path.home() / "leo-ai-os" / "knowledge-base"
INBOX = BASE / "inbox"
NOTES = BASE / "notes"
LOGS = BASE / "logs"
STATE_FILE = BASE / "processed.json"
LOG_FILE = LOGS / "pipeline.log"

# 本地提炼模型 (Ollama, 0 成本)
LOCAL_MODEL = "llama3.2:1b"
OLLAMA_URL = "http://127.0.0.1:11434/api/generate"

# 支持的文件类型
PDF_EXTS = {".pdf"}
TEXT_EXTS = {".txt", ".md", ".markdown"}
LINK_EXTS = {".url", ".webloc"}
IMG_EXTS = {".png", ".jpg", ".jpeg", ".webp"}

MAX_CHARS = 6000   # 喂给模型的正文上限


def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    try:
        LOGS.mkdir(parents=True, exist_ok=True)
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass


def load_state():
    try:
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_state(state):
    try:
        STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception as e:
        log(f"⚠️ 状态保存失败: {e}")


# ========== 文件解析 ==========
def parse_pdf(path):
    """提取 PDF 文本"""
    import pdfplumber
    text_parts = []
    try:
        with pdfplumber.open(path) as pdf:
            for page in pdf.pages[:10]:  # 最多前 10 页
                t = page.extract_text()
                if t:
                    text_parts.append(t)
    except Exception as e:
        log(f"⚠️ PDF 解析失败 {path.name}: {e}")
        return ""
    return "\n".join(text_parts)


def parse_link(path):
    """解析 .url/.webloc 链接文件, 返回 URL"""
    try:
        content = path.read_text(encoding="utf-8", errors="ignore")
        m = re.search(r"(https?://[^\s\"'<>]+)", content)
        if m:
            return m.group(1)
    except Exception:
        pass
    return ""


def fetch_url(url):
    """抓取网页正文, 微信文章提取 js_content 正文"""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"})
        with urllib.request.urlopen(req, timeout=15) as r:
            html = r.read().decode("utf-8", errors="ignore")

        # 微信文章: 提取 js_content 正文 (动态渲染但正文在 HTML 中)
        if "mp.weixin.qq.com" in url:
            m = re.search(r'<div[^>]*id="js_content"[^>]*>(.*?)</div>', html, re.S)
            if m:
                body = m.group(1)
                # 保留段落结构
                body = re.sub(r"<(script|style)[^>]*>.*?</\\1>", " ", body, flags=re.S | re.I)
                body = re.sub(r"<br\\s*/?>", "\\n", body, flags=re.I)
                body = re.sub(r"</p>|</h[1-6]>|</li>|</blockquote>", "\\n", body, flags=re.I)
                text = re.sub(r"<[^>]+>", " ", body)
                text = re.sub(r"\\s+", " ", text)
                return text.strip()[:MAX_CHARS]

        # 通用网页: 去 script/style
        html = re.sub(r"<(script|style)[^>]*>.*?</\\1>", " ", html, flags=re.S | re.I)
        text = re.sub(r"<[^>]+>", " ", html)
        text = re.sub(r"\\s+", " ", text)
        return text.strip()[:MAX_CHARS]
    except Exception as e:
        log(f"⚠️ 网页抓取失败 {url}: {e}")
        return ""


def parse_text(path):
    return path.read_text(encoding="utf-8", errors="ignore")


def extract_content(path):
    """按类型提取正文, 返回 (title, content, source_type)"""
    ext = path.suffix.lower()
    source_type = ext.lstrip(".")
    title = path.stem.replace("_", " ").replace("-", " ")

    if ext in PDF_EXTS:
        content = parse_pdf(path)
        source_type = "pdf"
    elif ext in LINK_EXTS:
        url = parse_link(path)
        content = fetch_url(url) if url else ""
        source_type = "link"
        if url:
            title = f"链接: {url[:60]}"
    elif ext in TEXT_EXTS:
        content = parse_text(path)
        source_type = "text"
    else:
        content = f"[图片文件 {path.name} - 需要视觉模型进一步解析]"
        source_type = "image"

    return title, content[:MAX_CHARS], source_type


# ========== Ollama 提炼 ==========
def summarize_local(content, title):
    """本地模型提炼: 摘要 + 标签 + 要点"""
    prompt = f"""你是知识库整理助手。阅读下面的文章，输出 JSON 格式的提炼结果。

文章标题: {title}
文章内容:
{content[:3000]}

请输出 JSON (不要输出其他文字):
{{
  "summary": "50字以内的核心摘要",
  "tags": ["标签1", "标签2", "标签3"],
  "keywords": ["关键词1", "关键词2"],
  "key_points": ["要点1", "要点2", "要点3"]
}}"""

    try:
        body = json.dumps({
            "model": LOCAL_MODEL,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0.3, "num_predict": 500},
        }).encode("utf-8")
        req = urllib.request.Request(OLLAMA_URL, data=body, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=120) as r:
            d = json.loads(r.read())
        raw = d.get("response", "")
        # 提取 JSON 部分
        m = re.search(r"\{.*\}", raw, re.S)
        if m:
            return json.loads(m.group(0))
    except Exception as e:
        log(f"⚠️ 本地模型调用失败: {e}")
    return {"summary": "", "tags": [], "keywords": [], "key_points": []}


def summarize_remote(content, title):
    """云端免费模型提炼 (OpenRouter 免费, 兜底)"""
    # 读取 OpenRouter key
    env = {}
    try:
        for line in Path.home().joinpath(".hermes/.env").read_text().splitlines():
            if "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip().strip('"')
    except Exception:
        pass
    key = env.get("OPENROUTER_API_KEY")
    if not key:
        return summarize_local(content, title)

    prompt = f"""阅读文章《{title}》, 提炼摘要、标签、要点。
文章: {content[:3000]}
输出 JSON: {{"summary":"50字摘要","tags":["标签"],"keywords":["词"],"key_points":["要点"]}}"""

    try:
        body = json.dumps({
            "model": "openrouter/free",
            "messages": [{"role": "user", "content": prompt}],
        }).encode("utf-8")
        req = urllib.request.Request("https://openrouter.ai/api/v1/chat/completions", data=body, headers={
            "Authorization": "Bearer " + key,
            "Content-Type": "application/json",
        })
        with urllib.request.urlopen(req, timeout=60) as r:
            d = json.loads(r.read())
        raw = d["choices"][0]["message"]["content"]
        m = re.search(r"\{.*\}", raw, re.S)
        if m:
            return json.loads(m.group(0))
    except Exception as e:
        log(f"⚠️ 云端模型失败, 回退本地: {e}")
    return summarize_local(content, title)


# ========== 笔记生成 ==========
def generate_note(title, content, source_type, source_name, meta):
    """生成 Obsidian 双链 Markdown"""
    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    slug = re.sub(r"[^\w\u4e00-\u9fff-]+", "-", title)[:50].strip("-")
    if not slug:
        slug = str(uuid.uuid4())[:8]
    filename = f"{date_str}-{slug}.md"
    filepath = NOTES / filename

    summary = meta.get("summary", "")
    tags = meta.get("tags", [])
    keywords = meta.get("keywords", [])
    points = meta.get("key_points", [])

    # 双链: 标签即笔记名
    links = "\n".join(f"[[{t}]]" for t in tags[:5])

    tags_quoted = ", ".join('"' + t + '"' for t in tags)
    kws_quoted = ", ".join('"' + k + '"' for k in keywords)

    frontmatter = f"""---
title: "{title}"
date: {date_str}
type: {source_type}
source: "{source_name}"
summary: "{summary}"
tags: [{tags_quoted}]
keywords: [{kws_quoted}]
---

# {title}

## 📝 摘要
{summary}

## 🔖 标签
{links}

## 🎯 要点
"""
    for i, p in enumerate(points, 1):
        frontmatter += f"{i}. {p}\n"

    frontmatter += """
## 📄 原文摘录
""" + content[:1500] + """

---
*由 Hermes 知识库流水线自动生成 · %s*
""" % now.strftime("%Y-%m-%d %H:%M")
    filepath.write_text(frontmatter, encoding="utf-8")
    return filepath


# ========== 主流程 ==========
def main():
    dry = "--dry" in sys.argv
    force = "--force" in sys.argv
    state = {} if force else load_state()

    if not INBOX.exists():
        log("📭 inbox 目录不存在")
        return

    files = [p for p in INBOX.iterdir() if p.is_file()]
    if not files:
        log("📭 inbox 为空, 无需处理")
        return

    log(f"📥 发现 {len(files)} 个文件")
    processed = 0

    for path in files:
        key = path.name
        if key in state and not force:
            continue  # 已处理

        log(f"🔄 处理: {path.name}")
        title, content, source_type = extract_content(path)

        if not content:
            log(f"  ⚠️ 内容为空, 跳过: {path.name}")
            state[key] = {"status": "empty", "time": time.strftime("%Y-%m-%d %H:%M:%S")}
            continue

        # 提炼: 默认云端免费模型 (效果好), --local 强制本地, 云端失败自动回退本地
        if "--local" in sys.argv:
            meta = summarize_local(content, title)
        else:
            meta = summarize_remote(content, title)

        if dry:
            log(f"  🧪 [DRY] 将生成: {title} | 标签: {meta.get('tags', [])}")
            state[key] = {"status": "dry", "time": time.strftime("%Y-%m-%d %H:%M:%S")}
            processed += 1
            continue

        # 生成笔记
        try:
            note_path = generate_note(title, content, source_type, path.name, meta)
            log(f"  ✅ 笔记生成: {note_path.name}")
            # 移动原文件到 processed (保留归档)
            archive = INBOX / ".." / "processed"
            archive.mkdir(exist_ok=True)
            shutil.move(str(path), str(archive / path.name))
            state[key] = {"status": "done", "note": note_path.name,
                          "time": time.strftime("%Y-%m-%d %H:%M:%S")}
            processed += 1
        except Exception as e:
            log(f"  ❌ 生成失败 {path.name}: {e}")
            state[key] = {"status": "error", "error": str(e)}

    save_state(state)
    log(f"🎉 完成: 处理 {processed} 个文件")


if __name__ == "__main__":
    main()
