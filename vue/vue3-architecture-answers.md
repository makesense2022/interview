# Vue 3 架构与高级主题·参考答案（对应题 11–20）

响应式系统：reactive/ref/shallow* 的差异？为何解构 reactive 会“失去响应”？何时使用 markRaw/readonly？
computed vs watch/watchEffect：依赖收集与缓存策略的区别？flush: pre/post/sync 的使用时机？
Composable 设计：如何避免单例副作用？provide/inject 用在什么跨层场景？如何保障可测试性与类型安全？
组件通信：defineProps/defineEmits、多 v-model 语义、defineExpose 提供 imperative API 的注意事项？
性能优化：<script setup> 的静态分析优势？v-once/v-memo 的适用边界？Teleport/KeepAlive 的最佳实践？
异步组件与 <Suspense>：defineAsyncComponent 的 loading/error/timeout 策略？如何避免并发请求的竞态与重复加载？
路由与缓存：KeepAlive 的 include/exclude/max 与动态 key 如何控制缓存失效？配合路由 meta 做权限与标题？
Pinia vs Vuex4：组合式 Store 的组织方式、插件扩展点、与 SSR 的配合？何时仍选 Vuex/RTK？
SSR / Nuxt3：服务器渲染、注水/脱水流程；islands/partial hydration 如何降低 JS 注入范围？
自定义指令/渲染函数/JSX：何时从模板转为渲染函数？封装复杂 DOM 行为（懒加载/拖拽/权限）的指令注意点？*

- 【11】响应式系统：Proxy/Ref/Reactive 与相关 API
  - reactive 返回 Proxy 深层响应；ref 包装基本类型/对象（.value）；shallowRef/shallowReactive 只跟踪浅层。
  - toRef/toRefs：从 reactive 对象中按引用创建 ref（与解构保持响应），避免丢失响应式。
  - markRaw：标记对象不被代理（大型第三方实例、图数据）；readonly：只读视图。
  - 陷阱：解构 reactive 会失去响应；ref 的对象值内部仍会被代理。

- 【12】computed vs watch/watchEffect
  - computed：基于依赖图的缓存 getter；惰性求值、可写（带 setter）。
  - watch：显式侦听源（ref/函数/数组），提供 new/old 值；深度/flush（pre/post/sync）可调。
  - watchEffect：自动依赖收集，无 new/old；适合副作用。
  - 清理：回调参数 onCleanup(fn)；避免竞态（异步请求时取消旧任务）。

- 【13】Composable 设计与 provide/inject
  - 组合式函数应“无单例副作用、只依赖入参/上下文”，返回最小 API。
  - provide/inject 作为依赖注入通道，适合跨层级共享实例（i18n、主题、服务）；避免隐式耦合，提供默认实现与类型约束。

- 【14】组件通信与暴露
  - defineProps/defineEmits：单向数据流与事件契约；支持多 v-model（modelValue + update:modelValue）。
  - defineExpose：对外显式暴露方法（适合封装组件的 imperative API）。
  - 事件透传：$attrs、v-bind="$attrs"、emits 校验，避免未知属性泄漏到根 DOM。

- 【15】性能优化
  - <script setup> 带来静态分析与编译期优化（props/emit 摘出、hoist 静态）。
  - v-once/v-memo：跳过/缓存子树；谨慎使用。
  - Teleport/KeepAlive：跨层渲染与缓存；KeepAlive 的 include/exclude、max 与 key 管理。

- 【16】异步组件与 Suspense
  - defineAsyncComponent 支持 loading/error/超时；<Suspense> 提供 fallback 与并行等待多个异步依赖。
  - 并发请求合并：在 composable 内做缓存/去重；与 onServerPrefetch 配合 SSR。

- 【17】路由与缓存
  - 路由级按需加载、基于 meta 的权限与标题管理。
  - KeepAlive 缓存策略：按路由 name include/exclude、动态 key 控制失效；注意缓存资源占用。

- 【18】Pinia vs Vuex4
  - Pinia：API 简洁、TS 友好、组合式 store、插件扩展；天然支持模块化与 SSR。
  - Vuex4：兼容历史项目；经典 mutation/action 模式。
  - 选型：新项目倾向 Pinia；需严格时序/审计的可用 Vuex/RTK。

- 【19】SSR / Nuxt3
  - 渲染流水线：server render → 注水（serialize state）→ 客户端脱水与挂载。
  - islands/partial hydration：仅为交互岛屿注入 JS，降低体积。
  - 数据获取：useAsyncData/useFetch，注意请求去重与缓存、跨端 cookie。

- 【20】自定义指令/渲染函数/JSX
  - 自定义指令：聚焦 DOM 行为（懒加载/拖拽/权限显示）。
  - 渲染函数/JSX：当需要更强的可组合/动态渲染（表单生成器、动态表格列）。
  - 与模板优化：避免在渲染函数中做昂贵计算，抽入 composable。
