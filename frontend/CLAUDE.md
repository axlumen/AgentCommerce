# 前端开发指引

## 重要：Next.js 16

本项目使用 Next.js 16，与你训练数据中的版本可能不同。写代码前先读 `node_modules/next/dist/docs/` 中的指南，注意破坏性变更和弃用通知。

## 架构

- **App Router**：`app/` 下每页一个 `page.tsx`，布局用 `layout.tsx`
- **组件**：`components/ui/`（shadcn，不要手动修改）、`components/layout/`、`components/product/`、`components/chat/`
- **状态**：Zustand（`store/`）管客户端状态，TanStack Query（`lib/query-client.ts`）管服务端状态
- **API**：所有后端调用走 `lib/api.ts`，不要在组件里直接 fetch
- **样式**：Tailwind CSS 4，不要写自定义 CSS

## 命令

```bash
npm install        # 安装依赖
npm run dev        # 启动开发服务器
npm run build      # 构建生产版本
npm run lint       # ESLint 检查
npx shadcn@latest add <component>  # 添加 shadcn/ui 组件
```

## API 代理

开发环境通过 `next.config.ts` 的 `rewrites` 将 `/api/*` 代理到 `http://localhost:8000/api/*`，前端代码中 `fetch('/api/...')` 即可。
