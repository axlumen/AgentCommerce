/**
 * 页脚组件
 */

export function Footer() {
  return (
    <footer className="border-t py-6 md:py-0">
      <div className="container flex flex-col items-center justify-between gap-4 md:h-24 md:flex-row px-4 mx-auto max-w-7xl">
        <div className="flex flex-col items-center gap-4 px-8 md:flex-row md:gap-2 md:px-0">
          <span className="text-lg">🛒</span>
          <p className="text-center text-sm leading-loose text-muted-foreground md:text-left">
            © 2026 AgentCommerce. 基于 AI 的智能导购电商平台
          </p>
        </div>
        <div className="flex items-center space-x-4">
          <a
            href="https://github.com/axlumen/AgentCommerce"
            target="_blank"
            rel="noopener noreferrer"
            className="text-sm text-muted-foreground hover:text-primary"
          >
            GitHub
          </a>
          <a
            href="/docs"
            target="_blank"
            rel="noopener noreferrer"
            className="text-sm text-muted-foreground hover:text-primary"
          >
            API 文档
          </a>
        </div>
      </div>
    </footer>
  );
}
