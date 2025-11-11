# Vue 3 架构与高级主题·详解版（题 11–20）

说明：每题固定结构，便于速读与落地。

---

## 11) 响应式系统：Proxy/Ref/Reactive 与相关 API

- TL;DR：Vue 3 以 Proxy 实现深层响应式，`ref` 用于基本类型或需要 .value 的容器；`toRef(s)` 保持与源对象同引用；`markRaw/readonly` 控制代理与只读。

- 心智模型：依赖收集（track）→ 触发（trigger）。`effect` 在读取时被收集；写入时触发对应依赖执行。

- 核心原理：
  - `reactive(obj)`：返回 `Proxy(obj, handlers)`，在 `get/set` 拦截里做 track/trigger，嵌套对象在访问时惰性代理。
  - `ref(v)`：返回 `{ value: v }` 的代理容器，对 `value` 的 `get/set` 做 track/trigger；对象值内部仍会被 `reactive` 化。
  - `shallowReactive/shallowRef`：仅第一层响应；适合大型不可变数据或第三方实例。
  - `toRef(obj, key)`/`toRefs(obj)`：为响应式对象的字段创建“按引用的 ref”，解构后仍保持响应。
  - `markRaw(obj)`：禁止代理（如大图、第三方实例）；`readonly(obj)`：只读视图，写入时报 warn。

- 典型场景：
  - 表单：基本类型用 `ref`，对象聚合用 `reactive`。
  - 懒加载大数据：`shallowRef` + 手动替换，避免深层遍历成本。
  - 第三方库对象：`markRaw` 防止被代理导致不兼容。

- 最小片段：
  ```ts
  const state = reactive({ user: { name: 'A' } })
  const name = toRef(state.user, 'name')
  name.value = 'B' // 同步到 state.user.name
  ```

- 常见坑：
  - 直接解构 `reactive` 导致失去响应 → 用 `toRefs`。
  - 数组/Map/Set 的方法触发：由代理拦截，注意不可直接替换内部原型方法。

---

## 12) computed vs watch/watchEffect

- TL;DR：`computed` 是“可缓存派生值”；`watch` 是“订阅源变化执行副作用”；`watchEffect` 自动依赖收集、无新旧值。

- 核心原理：
  - `computed` 有内部 `effect` 且具备“脏标记 + 惰性求值”，只有被读取时且脏才重新计算。
  - `watch(source, cb, { deep, flush })`：`source` 可为 `ref`、函数或数组；`flush` 决定回调相对渲染的时机（pre/post/sync）。
  - 取消/清理：`cb` 的第三个参数 `onCleanup(fn)`，异步请求时用于取消上一次。

- 场景：
  - 复杂派生：`computed`；
  - 监听多个源或执行副作用：`watch`；
  - 快速试验/调试副作用：`watchEffect`。

- 片段：
  ```ts
  const q = ref('')
  const list = ref<string[]>([])
  watch(q, async (v, _, onCleanup) => {
    const ctrl = new AbortController()
    onCleanup(() => ctrl.abort())
    const res = await fetch(`/api?q=${v}`, { signal: ctrl.signal })
    list.value = await res.json()
  }, { flush: 'post' })
  ```

---

## 13) Composable 设计与 provide/inject

- TL;DR：组合式函数“纯粹可复用”，避免隐藏状态；跨层共享用 provide/inject 并配合 InjectionKey 与默认实现。

- 原则：
  - 输入驱动、无单例副作用；
  - 返回最小 API；
  - 可测试（对外暴露纯函数与可替换依赖）。

- provide/inject：
  ```ts
  // tokens.ts
  export const AuthKey = Symbol('auth') as InjectionKey<AuthService>
  // root
  provide(AuthKey, createAuthService())
  // child
  const auth = inject(AuthKey, createMockAuth())
  ```

- 场景：主题/i18n/鉴权/全局服务。

---

## 14) 组件通信与暴露

- TL;DR：`defineProps/defineEmits` 明确契约；多 v-model 对应 `modelValue + update:modelValue`；`defineExpose` 暴露少量必要的命令式方法。

- 片段：
  ```vue
  <script setup lang="ts">
  const props = defineProps<{ modelValue: string }>()
  const emit = defineEmits<{ (e:'update:modelValue', v:string): void }>()
  function focus() { inputRef.value?.focus() }
  defineExpose({ focus })
  </script>
  ```

- 建议：避免把所有内部方法都暴露；保持单向数据流，使用事件透传 `$attrs`。

---

## 15) 性能优化

- TL;DR：利用编译期优化（静态提升、patch flags）、结构优化（拆分子树）、运行时缓存（v-memo）、缓存/复用（KeepAlive）。

- 关键点：
  - `<script setup>`：静态分析 props/emit，提升编译优化空间。
  - `v-once` 跳过更新；`v-memo` 根据依赖缓存子树；
  - `KeepAlive`：缓存路由视图/组件，配合 `include/exclude/max` 与稳定 `key`；
  - `Teleport`：将子树渲染到 DOM 其他位置（弹层）。

- 列表：虚拟滚动（vue-virtual-scroller）、稳定 key、避免在父组件存放大对象。

---

## 16) 异步组件与 Suspense

- TL;DR：`defineAsyncComponent` 提供 loading/error/超时；`<Suspense>` 汇聚多个异步依赖并提供 fallback。

- 片段：
  ```ts
  const AsyncCard = defineAsyncComponent({
    loader: () => import('./Card.vue'),
    loadingComponent: Loading,
    errorComponent: LoadError,
    delay: 200,
    timeout: 30_000,
    suspensible: true,
  })
  ```
  ```vue
  <Suspense>
    <template #default>
      <AsyncCard/>
    </template>
    <template #fallback>
      <Skeleton/>
    </template>
  </Suspense>
  ```

- SSR：在 Nuxt3 中与 `Suspense`/`async setup` 协同，服务器端先等待数据再输出或采用流式分段。

---

## 17) 路由与缓存

- TL;DR：路由级按需，`KeepAlive` 管理页面缓存；使用 `include/exclude/max` 与 key 控制失效。

- 片段：
  ```vue
  <keep-alive :include="['List','Detail']" :max="5">
    <router-view v-slot="{ Component, route }">
      <component :is="Component" :key="route.fullPath" />
    </router-view>
  </keep-alive>
  ```

- 建议：
  - 重要页面缓存、搜索/筛选使用 `fullPath` 作为 key；
  - 定期清理缓存；注意缓存占用内存。

---

## 18) Pinia vs Vuex4

- TL;DR：Pinia API 简洁、TS 友好、支持组合式 store 与插件；Vuex4 更适合维护旧项目。

- Pinia 片段：
  ```ts
  // store/counter.ts
  import { defineStore } from 'pinia'
  export const useCounter = defineStore('c', {
    state: () => ({ count: 0 }),
    getters: { double: s => s.count * 2 },
    actions: { inc(){ this.count++ } },
  })
  ```

- SSR：Pinia 支持“每请求一个新实例”，在脱水/注水时序上更友好。

---

## 19) SSR / Nuxt3

- TL;DR：服务端渲染 + 脱水/注水；Nuxt3 基于 Nitro，提供 `useAsyncData/useFetch`、路由与文件系统约定。

- 片段：
  ```ts
  // pages/index.vue
  <script setup>
  const { data } = await useFetch('/api/posts', { lazy: false })
  </script>
  ```

- 建议：
  - 启用缓存（HTTP/应用级）；
  - Islands/Partial Hydration：只为交互区注入客户端 JS。

---

## 20) 自定义指令/渲染函数/JSX

- TL;DR：指令聚焦 DOM 行为封装（懒加载、权限）；渲染函数/JSX 提供更强的可组合性（如表单生成器）。

- 指令片段（懒加载）：
  ```ts
  const vLazy: Directive<HTMLImageElement, string> = {
    mounted(el, { value }) {
      const io = new IntersectionObserver(entries => {
        if (entries[0].isIntersecting) { el.src = value; io.disconnect() }
      })
      io.observe(el)
    }
  }
  ```

- 渲染函数示例：
  ```ts
  import { h } from 'vue'
  export default {
    props: { cols: Array },
    render(){
      return h('table', this.cols.map(c => h('th', c.title)))
    }
  }
  ```

- 建议：在渲染函数中避免重计算；抽入 composable；与 TS 类型配合保证可维护。
