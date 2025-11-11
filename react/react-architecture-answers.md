# React 架构与高级主题·参考答案（对应题 1–10）
解释 React 18 并发渲染：渲染阶段为何可中断？提交阶段与优先级如何协作？startTransition 适用场景与误用风险是什么？
Suspense for Code/Data 的工作机制是什么？为什么需要“throw Promise”？如何设计合理的边界与 fallback 策略？
对比 RSC 与 SSR：各自的渲染/传输/水合路径怎么走？RSC 在哪些场景能显著降低客户端 JS？
状态管理选型：Context、Redux Toolkit、Zustand、Recoil/Jotai 各自的订阅粒度、心智负担与典型使用边界？
重渲染优化：React.memo、useMemo、useCallback 各自的缓存粒度与代价？列表虚拟化与稳定 key 的作用？
表单架构设计：受控 vs 非受控的优缺点？为何 react-hook-form 能减少重渲染？大表单的性能与可用性策略？
路由与代码拆分：如何在路由级做按需加载与预取？如何处理错误边界与骨架屏以优化切页体验？
SSR/SSG/ISR 与 Hydration/Streaming：何时选择哪种模式？Streaming 对 TTFB/TTI 的影响与注意点？
错误边界与可观测性：ErrorBoundary 的捕获边界在哪？如何结合 window.onerror/unhandledrejection 与 Source Map 做端到端定位？
微前端与 Module Federation：如何共享依赖并避免多版本冲突？远程模块异常或超时的降级方案如何设计？
======

- 【1】React 18 并发渲染与优先级、startTransition
  - 并发渲染：允许在渲染过程中被中断、丢弃与重做，以保证高优任务（输入/交互）优先。渲染结果只有在提交阶段（commit）才会生效。
  - setState 可能被打断：渲染阶段是可中断的，React 会根据调度器优先级（如连续输入）打断低优任务。
  - startTransition：将状态更新标记为“非紧急”，使其成为低优任务，不阻塞输入；典型场景：过滤/排序列表、路由切换后的大列表渲染。
  - 注意：Transition 只影响渲染优先级，不影响网络/副作用；搭配 Suspense 体验更佳。

- 【2】Suspense for Data/Code 的原理与实践
  - 原理：在渲染阶段若遇到“挂起”（throw promise），React 暂存渲染并显示 fallback；待 promise 解决后继续渲染。
  - 代码分割：React.lazy(() => import('...')) + <Suspense fallback>。
  - 数据加载：与 React Query（suspense 模式）或 RSC 配合；为慢资源设置合理的 fallback 与超时（尾部骨架/分屏)。
  - 边界策略：就近边界避免整页闪烁；嵌套边界（外骨架 + 内部局部）提升感知速度。

- 【3】RSC（React Server Components）vs SSR
  - SSR：在服务端把 UI 渲染为 HTML，再在客户端 hydrate 绑定事件；客户端必须下载组件 JS。
  - RSC：部分组件仅在服务端渲染，无需发送其 JS 到客户端（零 JS 开销），通过服务器流与客户端组件边界拼接。
  - 优点：减少客户端 JS 体积、天然数据靠近服务端、可直接调用服务器资源。
  - 限制：只能在 Server 组件里执行服务端能力；边界与客户端组件通信通过 props；需要框架支持（Next.js app router）。

- 【4】状态管理选型（Context/Redux Toolkit/Zustand/Recoil/Jotai）
  - Context：轻量跨层传递，适合低频、结构稳定的配置/主题/当前用户；频繁更新会引发大范围重渲染。
  - Redux Toolkit：规范化数据流（单向、可追踪）、中大型项目、可串接 devtools/中间件；心智成本较高。
  - Zustand：极轻、无样板、选择性订阅减少重渲染，适合中小项目/局部全局状态。
  - Recoil/Jotai：原子化状态、可组合；利于复杂依赖图；需评估生态与 SSR 兼容。
  - 原则：全局稀疏+高频→选择性订阅的库，复杂过程→RTK；简单共享→Context。

- 【5】重渲染优化：memo/useMemo/useCallback & 列表优化
  - React.memo：按 props 浅比较跳过重渲；避免过度使用（比较成本、错误缓存）。
  - useMemo/useCallback：缓存计算/函数引用，依赖项必须正确；优先消除重渲染根因（拆分组件、选择性订阅、稳定 props）。
  - 列表：稳定 key、行内函数抽出、虚拟化（react-window/virtual）、避免在父级存放大对象导致子项反复变更。

- 【6】表单架构：受控 vs 非受控，react-hook-form
  - 受控：值受 state 驱动，易联动与验证但重渲染多；非受控：ref 读取，性能好但逻辑分散。
  - react-hook-form：基于原生表单注册 + 受控/非受控混合，按字段订阅、惰性校验，显著降低重渲染。
  - 大表单策略：分段/虚拟化、延迟校验、批量提交、脏字段跟踪。

- 【7】路由与代码拆分
  - 路由级动态 import，配合 Suspense + 预加载（鼠标悬停/可视区预取）优化首屏与切页体验。
  - 错误边界与路由边界结合，防止整页崩溃；细分 bundle，长缓存 + runtime chunk。

- 【8】SSR/SSG/ISR 与 Hydration、Streaming
  - SSR：首字节快、交互需等待 hydrate；SSG：构建期产出静态页；ISR：按间隔再生。
  - Hydration：将事件/状态绑定到服务端生成的 HTML；注意同构副作用隔离。
  - Streaming：拆分边界流式输出，搭配 Suspense 提升 TTFB/TTI；谨慎处理 SEO 和缓存。

- 【9】错误边界与可观测性
  - Error Boundary 捕获 render/生命周期/constructor 的同步错误，不捕获事件处理器/异步/SSR 错误。
  - 结合 window.onerror/unhandledrejection、source map、错误指纹与采样；提供降级 UI 与重试。

- 【10】微前端与 Module Federation（MF）
  - shared：声明共享依赖（react/react-dom），使用 singleton/requiredVersion；避免重复打包与多实例冲突。
  - 版本冲突：采用严格版本、fallback 或运行时隔离（iframe/Shadow DOM/CSS 隔离）。
  - 路由集成：主应用统一路由/布局/鉴权；远程模块懒加载与错误兜底。
