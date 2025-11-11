# React 架构与高级主题·详解版（题 1–10）

说明：每题遵循固定结构，便于速读与深挖：
- TL;DR
- 心智模型/流程
- 为什么需要（痛点/收益）
- 核心原理
- 典型场景
- 最小可运行代码
- 常见坑与边界
- 性能与体验建议
- 对比/相关概念
- 结论与决策建议
- 进一步阅读

---

## 1) React 18 并发渲染与优先级、startTransition

- TL;DR：并发渲染让渲染阶段可被打断与重做；`startTransition` 将非紧急更新降级，保证输入流畅。

- 心智模型/流程：
  1. 触发 setState → 更新被标注优先级（紧急/非紧急）。
  2. 渲染阶段可中断：高优更新打断低优渲染；可丢弃已计算的结果，稍后重做。
  3. 提交阶段（commit）仍是同步整块提交，保证一致性。

- 为什么需要：
  - 传统同步渲染：大列表/重计算会卡输入。
  - 并发让“人机交互优先”，页面复杂时仍保持丝滑。

- 核心原理：
  - 时间切片（cooperative scheduling）+ 可中断 fiber 渲染。
  - 调度器（scheduler）给不同更新分配优先级队列。

- 典型场景：
  - 关键字过滤、排序大列表；路由切换后的重渲染；搜索建议。

- 最小可运行代码：
  ```jsx
  import { useState, useTransition } from 'react'

  export default function FilteredList({ items }) {
    const [q, setQ] = useState('')
    const [list, setList] = useState(items)
    const [pending, startTransition] = useTransition()

    function onChange(e){
      const v = e.target.value
      setQ(v) // 紧急：输入立即回显
      startTransition(() => {
        setList(items.filter(x => x.includes(v))) // 非紧急：可被打断
      })
    }
    return <>
      <input value={q} onChange={onChange} />
      {pending && <span>更新中…</span>}
      <ul>{list.map((x,i)=><li key={i}>{x}</li>)}</ul>
    </>
  }
  ```

- 常见坑与边界：
  - Transition 不能“加速”，只是“让高优先”。
  - 不要把受控输入本身放进 transition。
  - 优先减少无谓重渲染（拆分组件、选择性订阅）。

- 对比：`useDeferredValue` 是对“值”的延迟派生；`startTransition` 是对“更新”的优先级标注。

- 结论：交互优先、重计算次之；在明确“非紧急”的更新上使用 transition。

- 进一步阅读：React 官方 concurrent features；Dan Abramov 关于时间切片的文章。

---

## 2) Suspense for Code/Data：为什么要“throw Promise”？如何设计边界与 fallback？

- TL;DR：组件/数据未就绪时在渲染阶段“抛 Promise”，React 捕获后显示就近 fallback，待 Promise resolve 再继续渲染，统一“加载中”体验。

- 心智模型/流程：
  1. 渲染组件 → 依赖未就绪 → 组件抛出 Promise（挂起）。
  2. React 捕获挂起，使用最近的 `<Suspense fallback>` 占位。
  3. Promise 解决 → React 重试渲染 → 提交替换 fallback。

- 为什么需要：
  - 手写 `isLoading` 到处 if-else，分散且易错。
  - Suspense 把“加载中策略”集中在边界，提升一致性与可组合性。

- 核心原理：
  - 渲染阶段禁止“等待”，通过 throw Promise 的协定告诉 React：稍后再试。
  - 代码分割（`React.lazy`）和数据加载库（如 React Query suspense 模式）皆遵守此协定。

- 典型场景：
  - 路由/模块懒加载；慢接口的局部骨架；图表数据等待；RSC 流式拼接客户端边界。

- 最小可运行：代码分割
  ```jsx
  import { Suspense } from 'react'
  const Card = React.lazy(() => import('./Card'))
  export default () => (
    <Suspense fallback={<div>Loading…</div>}>
      <Card/>
    </Suspense>
  )
  ```

- 最小可运行：数据加载（React Query）
  ```bash
  pnpm add @tanstack/react-query
  ```
  ```jsx
  import { QueryClient, QueryClientProvider, useQuery } from '@tanstack/react-query'
  import { Suspense } from 'react'
  const qc = new QueryClient({ defaultOptions: { queries: { suspense: true } } })
  function Profile(){
    const { data } = useQuery({ queryKey:['me'], queryFn:()=>fetch('/api/me').then(r=>r.json()) })
    return <div>{data.name}</div>
  }
  export default () => (
    <QueryClientProvider client={qc}>
      <Suspense fallback={<div>Loading profile…</div>}>
        <Profile/>
      </Suspense>
    </QueryClientProvider>
  )
  ```

- 边界与 fallback：
  - 就近边界：只包“慢块”，避免整页白屏/闪烁。
  - 嵌套：外骨架（布局）+ 内骨架（模块），减少大面积跳变。
  - 预取/缓存：路由 hover 预取，React Query `prefetchQuery` + `keepPreviousData`。
  - 错误边界：失败走 ErrorBoundary，Suspense 只管“加载中”。

- 常见坑：
  - 光有 Suspense 不会自动发请求，需要库配合。
  - 整页单一边界导致“闪烁”与“空窗期”。
  - SSR/流式需要框架支持（Next.js）。

- 对比：手写 loading vs Suspense → 后者集中化、组合度高。

- 结论：局部慢块 + 就近 Suspense + 合理骨架 + 预取与缓存 + ErrorBoundary。

- 延伸：React 文档 Suspense；TanStack Query suspense；Next.js streaming。

---

## 3) RSC（React Server Components）vs SSR

- TL;DR：SSR 把 HTML 送到客户端再 hydrate；RSC 允许一部分组件只在服务端渲染且不下发 JS，显著减少客户端 JS 与水合成本。

- 心智模型：
  - Server 组件：只能在服务端执行（可直连 DB/FS），输出序列化片段。
  - Client 组件：浏览器交互，需要打包到客户端。
  - 边界通过 props 拼接，框架负责流式传输与合并。

- 为什么需要：
  - 大量“纯展示/数据重”的区域没必要下载 JS。

- 核心原理：
  - 特殊打包通道 + 协议把 Server 组件输出与 Client 组件产物拼起来（Next.js App Router）。

- 场景：
  - 列表/详情/富展示；报表；内容站点。

- 最小示例（Next.js）：
  ```tsx
  // app/page.tsx (Server Component)
  import { getPosts } from '@/lib/api'
  export default async function Page(){
    const posts = await getPosts()
    return <PostList posts={posts}/>
  }
  // app/components/Chart.tsx (Client Component)
  'use client';
  export default function Chart({data}){ /* 浏览器交互 */ return <canvas/> }
  ```

- 坑：
  - Server 组件不可用浏览器 API/状态 Hook；只能经 props 传到客户端组件。
  - 跨界过多会抵消收益；需要缓存策略与部署条件。

- 结论：展示/数据重用 Server；交互重用 Client；循序渐进迁移。

---

## 4) 状态管理选型（Context/RTK/Zustand/Recoil/Jotai）

- TL;DR：根据“订阅粒度/心智负担/生态”选型；高频全局状态用可选择性订阅的库（Zustand/Recoil），复杂业务流用 RTK，简单跨层传递用 Context。

- 对比要点：
  - Context：简单但更新会向下广播，适合配置、主题、登录信息。
  - RTK：规范化、可审计、生态完整，适合中大型与多人协作。
  - Zustand：极轻、按 selector 订阅，减少重渲染，学习成本低。
  - Recoil/Jotai：原子化依赖图、细粒度订阅，利于复杂派生。

- 场景建议：
  - 少量全局配置 → Context
  - 中大型、需要流水线与审计 → RTK
  - 中小项目/局部全局 → Zustand
  - 复杂派生 → Recoil/Jotai

- 代码（Zustand 最小示例）：
  ```bash
  pnpm add zustand
  ```
  ```jsx
  import { create } from 'zustand'
  const useStore = create(set=>({ count:0, inc:()=>set(s=>({count:s.count+1})) }))
  function Counter(){
    const count = useStore(s=>s.count)
    const inc = useStore(s=>s.inc)
    return <button onClick={inc}>{count}</button>
  }
  ```

---

## 5) 重渲染优化（memo/useMemo/useCallback & 列表）

- TL;DR：先从“数据流与订阅粒度”解决根因，再用缓存与 `memo` 抑制无谓渲染；列表用虚拟化与稳定 key。

- 建议顺序：
  1. 拆分组件、向下只传最小 props；
  2. 选择性订阅（Zustand selector / RTK memoized selector）；
  3. React.memo 包裹稳定子树；
  4. useMemo/useCallback 缓存“昂贵计算/稳定回调”；
  5. 大列表虚拟化（react-window）。

- 坑：
  - 过度 memo 反增成本；
  - 依赖项错误导致缓存脏或无效；
  - key 不稳定导致整体重建。

---

## 6) 表单架构（受控/非受控、react-hook-form）

- TL;DR：受控便于联动与规则，但重渲染多；react-hook-form 以“原生注册 + 字段级订阅”降低渲染成本。

- 最小示例（RHF）：
  ```bash
  pnpm add react-hook-form
  ```
  ```jsx
  import { useForm } from 'react-hook-form'
  export default function Form(){
    const { register, handleSubmit, formState:{errors} } = useForm()
    return <form onSubmit={handleSubmit(console.log)}>
      <input {...register('email', {required:true})} />
      {errors.email && '必填'}
      <button>提交</button>
    </form>
  }
  ```

- 建议：分段/延迟校验/脏字段跟踪/虚拟化长表单。

---

## 7) 路由与代码拆分策略

- TL;DR：路由级按需 + 预取/预加载 + Suspense 骨架；错误边界隔离崩溃；长缓存 + runtime chunk 稳定缓存命中。

- 代码片段（React Router + lazy）：
  ```jsx
  const User = lazy(()=>import('./pages/User'))
  <Routes>
    <Route path="/user" element={<Suspense fallback={<Skeleton/>}><User/></Suspense>} />
  </Routes>
  ```

---

## 8) SSR/SSG/ISR 与 Hydration/Streaming

- TL;DR：SSR 首字节快、需 hydrate；SSG 适合静态内容；ISR 介于二者。Streaming 将可用内容尽快流出并与 Suspense 协作。

- 建议：
  - 频繁变动 → SSR + 缓存；
  - 多静态页 → SSG/ISR；
  - 大量异步模块 → Streaming + 多 Suspense 边界。

---

## 9) 错误边界与可观测性

- TL;DR：ErrorBoundary 捕获渲染期同步错误；异步/事件需 window.onerror / unhandledrejection；配合 Source Map、指纹与采样。

- 片段：
  ```jsx
  class EB extends React.Component{
    state={error:null}
    static getDerivedStateFromError(e){return {error:e}}
    componentDidCatch(e,info){/* 上报 */}
    render(){ return this.state.error ? <Fallback/> : this.props.children }
  }
  ```

---

## 10) 微前端与 Module Federation

- TL;DR：运行时装载远程模块并共享依赖；要解决“依赖冲突、路由集成、降级回退”。

- Webpack 配置要点：
  ```js
  // host webpack.config.js
  new ModuleFederationPlugin({
    remotes:{ user:'userApp@https://cdn/appUser/remoteEntry.js' },
    shared:{ react:{singleton:true, requiredVersion:'^18'}, 'react-dom':{singleton:true} }
  })
  ```

- 策略：
  - 严格版本/回退；影子 DOM/CSS Modules 降低样式污染；
  - 远程失败 → 占位/降级页面；统一监控与会话关联。
