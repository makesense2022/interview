# Vue3 源码解读·第一讲：Reactivity 内核

目标：弄清楚 effect/track/trigger 的数据结构与执行链路，`reactive/ref/computed/watch` 的实现直觉，以及调度/flush 时机。

---

## 1. 核心数据结构（依赖图）

- 依赖图：`WeakMap<Target, Map<Key, Set<ReactiveEffect>>>`
  - targetMap: WeakMap，键是被代理的目标对象
  - depsMap: Map，键是具体的 key
  - dep: Set<ReactiveEffect>，订阅该 key 的副作用集合

示意：
```
state(user) ──▶ targetMap( user → depsMap )
                           ├─ 'name' → Set(effectA, effectB)
                           └─ 'age'  → Set(effectC)
```

## 2. ReactiveEffect 与 activeEffect

- `effect(fn)` 会创建一个 `ReactiveEffect` 实例并立即执行 fn。
- 在执行期间设置 `activeEffect = 当前 effect`，便于 `track()` 收集依赖。
- 支持 `scheduler`：当依赖变更触发时，不直接执行 fn，而是把任务交给调度器（如去重队列、nextTick 批量）。

伪码：
```ts
class ReactiveEffect {
  deps: Set<Dep>[] = []
  constructor(public fn:()=>any, public scheduler?:()=>void){}
  run(){ activeEffect = this; try { return this.fn() } finally { activeEffect = undefined }
  }
}
```

## 3. track 与 trigger

- track：在 `get` 拦截时，如果存在 `activeEffect`，把它加入 `dep`；并把 dep 记录到 effect.deps，便于后续清理。
- trigger：在 `set` 拦截时，找到对应 dep，遍历触发，每个 effect 交给其 `scheduler` 或直接 `run()`。

伪码：
```ts
function track(target,key){
  if(!activeEffect) return
  const depsMap = targetMap.get(target) || targetMap.set(target, new Map()).get(target)!
  const dep = depsMap.get(key) || depsMap.set(key, new Set()).get(key)!
  if(!dep.has(activeEffect)) { dep.add(activeEffect); activeEffect.deps.push(dep) }
}

function trigger(target,key){
  const depsMap = targetMap.get(target); if(!depsMap) return
  const dep = depsMap.get(key); if(!dep) return
  for(const effect of dep){ effect.scheduler ? effect.scheduler() : effect.run() }
}
```

## 4. reactive 与 ref

- reactive(obj)：返回 `new Proxy(obj, handlers)`；在 `get` 时 `track(target,key)`，在 `set` 时 `trigger(target,key)`。
- ref(value)：返回带有 `get value/set value` 的对象；内部有独立的 `dep` 集合，`value` 为对象时会转为 `reactive`。

关键区别：ref 以“值容器”为中心，适合整体替换；reactive 以“对象属性”为中心，适合就地修改。

## 5. computed（带脏标记）

- `ComputedRefImpl` 内部持有一个 `effect`（lazy），并维护 `dirty` 标志与 `cachedValue`。
- 首次 `get` 或 `dirty` 为真时执行 `effect.run()` 计算并缓存；其依赖触发时只把 `dirty=true`，并触发外部使用者。

伪码：
```ts
class ComputedRefImpl {
  private dirty = true
  private value: any
  private effect = new ReactiveEffect(getter, ()=>{ this.dirty = true; trigger(this,'value') })
  get value(){ if(this.dirty){ this.value = this.effect.run(); this.dirty = false } track(this,'value'); return this.value }
}
```

## 6. watch 与 watchEffect（清理与 flush）

- `watch(source, cb, { flush })`：
  - 将 `source` 规范化为“读取函数”（读取时会触发 track，建立依赖）。
  - 变更时调度 `job`：根据 `flush` 在 pre/post/sync 时机运行。
  - 支持 `onCleanup(fn)`：下一次执行前先调用上一次的清理函数，常用于取消未完成的异步。

示例（竞态处理）：
```ts
watch(q, async (v, _, onCleanup) => {
  const ctrl = new AbortController(); onCleanup(()=>ctrl.abort())
  const res = await fetch(`/api?q=${v}`, { signal: ctrl.signal })
  list.value = await res.json()
}, { flush: 'post' })
```

## 7. 调度器与 flush 时机

- Vue 内部维护一个微任务队列，`scheduler` 将 effect 推入队列并去重；在 nextTick 时机统一 flush，避免抖动。
- `flush: 'pre'`：渲染前执行（默认）；`'post'`：渲染后执行（读取 DOM 布局更安全）；`'sync'`：立即同步（少用）。

## 8. 解构 reactive 失去响应 & 用 toRefs

- 直接解构：得到的是“普通值”，后续不再受 Proxy 追踪。
- 解决：`toRefs(state)` 或 `toRef(state,'a')`，保持到源对象字段的引用链。

## 9. 小探针：打印依赖表（练习）

```ts
import { reactive, effect } from 'vue'
// 练习思路：在自定义的 track/trigger 中 console.log 路径与依赖集合大小，观察依赖如何建立与触发。
```

---

结语：理解 reactivity 的关键是“依赖图 + 调度器”。掌握后，`ref/reactive/computed/watch` 都只是这些原语之上的语法/形态。
