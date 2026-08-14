# Leo AI Website

Leo AI 公司官方网站 - 一人 AI 公司操作系统

## 在线访问

- **正式站**: https://leoai-2ml.pages.dev
- **备用**: Cloudflare Pages 全球 CDN，免费 SSL

## 技术栈

- 纯静态 HTML + CSS（单文件着陆页）
- Cloudflare Pages 托管
- 全球 CDN 加速，0 成本

## 本地预览

```bash
cd website
python3 -m http.server 4444
# 访问 http://localhost:4444
```

## 部署

```bash
npx wrangler pages deploy website --project-name leoai
```

## 页面内容

- Hero: 一人 AI 公司操作系统
- 产品特性: Hermes 大脑 / Mac mini 研发 / 极空间运营
- 三节点架构图
- CTA + 页脚
