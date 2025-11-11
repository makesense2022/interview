# uni-app 小程序最小对照示例：Vue 源码 → 小程序产物 → setData 补丁

目的：把“Vue3 响应式 → VDOM diff → mp-runtime → setData”的链路具体化，方便形成直觉。

## 1) Vue 源码（SFC 极简示例）

```vue
<template>
  <view class="wrap">
    <text class="title">Hello, {{ user.name }}</text>
    <button @tap="inc">count: {{ count }}</button>

    <view>
      <view v-for="(todo, i) in list" :key="todo.id" @tap="toggle(i)">
        <text>{{ i }}. {{ todo.text }} - {{ todo.done ? '✓' : '○' }}</text>
      </view>
    </view>
  </view>
</template>

<script setup>
import { ref, reactive } from 'vue'

const count = ref(0)
const user = reactive({ name: 'Tom' })
const list = ref([
  { id: 1, text: 'Eat', done: false },
  { id: 2, text: 'Code', done: true },
])

function inc() { count.value++ }
function toggle(i) { list.value[i].done = !list.value[i].done }
</script>

<style scoped>
.wrap { padding: 12rpx; }
.title { font-weight: bold; }
</style>
```

要点：
- 使用了 ref/reactive、事件绑定（@tap）、v-for、:key。

## 2) 小程序端产物（核心结构示意）

说明：以下为“概念化示意”，真实生成会更长，这里只展示关键映射。

- pages/index/index.wxml（模板）
```xml
<view class="wrap">
  <text class="title">Hello, {{ user.name }}</text>
  <button bindtap="__e" data-eid="inc">count: {{ count }}</button>

  <view>
    <block wx:for="{{ list }}" wx:key="id" wx:for-item="todo" wx:for-index="i">
      <view bindtap="__e" data-eid="toggle" data-args="{{ i }}">
        <text>{{ i }}. {{ todo.text }} - {{ todo.done ? '✓' : '○' }}</text>
      </view>
    </block>
  </view>
</view>
```

- pages/index/index.js（逻辑层，简化）
```js
Page({
  data: {
    count: 0,
    user: { name: 'Tom' },
    list: [
      { id: 1, text: 'Eat', done: false },
      { id: 2, text: 'Code', done: true },
    ],
  },
  // 事件统一入口（mp-runtime 注入/生成的桥）
  __e(e) {
    const eid = e.currentTarget.dataset.eid
    const args = e.currentTarget.dataset.args
    // 路由到 Vue 组件实例中的对应方法（inc/toggle）
    this.__uni_invoke(eid, args)
  }
})
```

- pages/index/index.json（页面配置）
```json
{
  "usingComponents": {}
}
```

- app.json / app.js / app.wxss：全局配置与样式（由 pages.json/样式聚合生成）。

- 运行时代码（common/** 或 vendor/**）：包含 mp-runtime 桥接、工具函数、事件派发等。

要点：
- 模板里的 @tap 被转为 bindtap，事件 id/参数通过 data-* 传入。
- data 为“可绑定的数据树”，对应 Vue 组件的响应式状态。

## 3) setData 补丁示例（mp-runtime 生成）

当响应式状态变化时，mp-runtime 不“操作 DOM”，而是生成“最小数据补丁”，并合并后调用 setData。

- 场景 A：点击 inc（count++）
  - 响应式变更：count: 0 → 1
  - 可能的补丁：
    ```js
    this.setData({ count: 1 })
    ```

- 场景 B：点击第二项 todo 的 toggle（list[1].done 翻转）
  - 响应式变更：list[1].done: true → false
  - 可能的补丁（使用稳定 keypath）：
    ```js
    this.setData({ 'list[1].done': false })
    ```

- 场景 C：整体替换 list（不推荐直接用新数组覆盖）
  - 如果写了 `list.value = [...list.value]`，且未做细粒度更新，可能导致较大的补丁：
    ```js
    this.setData({ list: /* 整个新数组 */ })
    ```
  - 建议：细粒度更新（如指定索引路径）以减小 setData 体积。

## 4) mp-runtime 在其中做了什么？（职责清单）

- 运行 Vue runtime-core（不依赖 DOM），接收响应式变更 → VNode diff。
- 将 VNode diff 转换为“小程序 data keypath 补丁”：
  - 维护节点与数据的“路径映射”（如 user.name、list[1].done）。
  - 聚合节流，控制 setData 的频次与体积。
- 事件桥接：把 bindtap 等事件路由回对应的 Vue 组件方法。
- 生命周期映射：将小程序的 onLoad/onShow 等绑定到 Vue 组件/页面钩子。

## 5) 性能与工程实践

- 细粒度更新：优先更新具体路径（如 `list[1].done`），避免整对象/整数组覆盖。
- 稳定 key：列表使用唯一且稳定的 :key，避免无谓重建。
- 数据扁平化：深层嵌套 path 会增加补丁路径复杂度，尽量保持合理结构。
- 批量更新：在一个 tick 内合并多处变更，减少 setData 次数（mp-runtime 会处理，但代码层同样要避免抖动）。
- 条件编译：用 `#ifdef MP-WEIXIN` 移除不兼容的 DOM/BOM 依赖。

---

有需要，我可以继续扩展示例：增加子组件（编译为小程序自定义组件）、跨组件事件传递、分包页面，以及 H5 与微信端产物的并排对照。
