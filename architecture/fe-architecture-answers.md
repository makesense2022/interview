# 前端架构设计·参考答案（对应题 21–30）

- 【21】模块联邦（MF）架构
  - 运行时共享依赖（shared），通过 singleton/strictVersion/fallback 防冲突。
  - 边界：独立发布、语义版本、对等依赖一致性；远程失效时的降级路径（占位、回退）。
  - 隔离：样式（CSS Modules/Shadow DOM）、全局对象安全、跨应用通信（事件总线/自定义协议）。

- 【22】Monorepo 设计
  - pnpm workspaces/Nx/Turborepo；TS Project References + build 缓存；按包 version/publishConfig 管理发布。
  - 依赖约束：对等依赖（peerDependencies）、版本冻结（pnpm overrides）。
  - CI：受影响图（affected）增量构建、变更集发布（changesets）。

- 【23】构建与产物切分
  - Vite/Rollup 的 manualChunks 策略、路由级代码分割、动态 import。
  - 预加载/预取：<link rel="preload|prefetch"> 与路由预取；长缓存：带 contenthash 与 runtime chunk。
  - CDN 缓存与 HTTP/2/3 连接复用；分包命名稳定性。

- 【24】性能预算与监控
  - 指标：LCP/CLS/INP/TTFB/TTI/Long Tasks；RUM 上报与采样。
  - Source map 上传与错误指纹；去抖与归并；采样率按流量与严重度动态调整。
  - 性能预算：JS/CSS/图片体积阈值、路由级耗时、慢接口 SLO。

- 【25】安全架构
  - CSP（script-src/nonce/hash）、Trusted Types 防 XSS；SRI 校验第三方脚本。
  - CSRF：同站策略 + SameSite Cookie/双重提交；依赖审计（npm audit/osv）。

- 【26】i18n 与可访问性
  - 词库拆分与懒加载；多语言路由与 SEO；数值/日期/复数规则（Intl）。
  - a11y：可聚焦顺序、语义标签、对比度主题、键盘与读屏支持。

- 【27】资源与图片策略
  - 响应式图片（srcset/sizes）、现代格式（WebP/AVIF）、懒加载与占位（LQIP/Blurhash）。
  - 图标：Icon Font/SVG Sprite/组件库；按需生成（unplugin-icons）。

- 【28】API 层架构
  - REST/GraphQL/tRPC：契约与演进；BFF 聚合；缓存策略（SWR、stale-while-revalidate）。
  - 可靠性：重试/指数退避、请求去重、超时与中断（AbortController）。

- 【29】离线与可靠性
  - Service Worker：缓存优先/网络优先/预缓存；后台同步（Background Sync）。
  - 数据冲突：客户端队列 + 乐观更新 + 回滚；PWA 清单与更新提示。

- 【30】微前端路由与集成
  - 跨应用路由同步（history 代理/事件桥）与全局状态（共享 store 或消息总线）。
  - CSS 隔离与样式基线统一；监控统一上报与会话关联；性能边界与配额管理。
