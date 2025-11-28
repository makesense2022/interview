# Web Worker 通俗讲解与使用场景

> 一句话：把“耗时计算”丢到浏览器的后台线程做，避免卡住页面的主线程，从而让滚动和点击更流畅（提升 INP）。

## 它是什么
- 浏览器提供的**后台线程**，用来在不阻塞 UI 的情况下执行 JS 代码。
- 主线程与 Worker 之间通过**消息**通信：`postMessage` / `onmessage`。
- 有自己的全局对象（`self`），没有 DOM。

## 能/不能做什么
- 能做：计算密集任务、数据处理、`fetch`/网络请求、WebCrypto、WASM、`OffscreenCanvas` 绘制等。
- 不能做：直接操作 DOM、`alert/confirm`、同步 XHR、访问主线程变量（必须消息传递）。

## 基本用法（模块 Worker 推荐）
主线程：
```js
// Vite/Webpack 等支持这种写法（生成静态 URL）
const worker = new Worker(new URL('./worker.js', import.meta.url), { type: 'module' });

worker.onmessage = (e) => {
  console.log('来自 worker 的结果:', e.data);
};

worker.postMessage({ n: 5_000_000 }); // 发计算任务

// 用完记得关闭
// worker.terminate();
```

worker.js：
```js
// 模块 Worker 内可用 ESM import
self.onmessage = (e) => {
  const { n } = e.data;
  const sum = heavySum(n);
  // 将结果发回主线程
  self.postMessage({ sum });
};

function heavySum(n) {
  let s = 0;
  for (let i = 0; i < n; i++) s += i;
  return s;
}
```

## 传输数据（性能关键）
- 结构化克隆：默认方式，拷贝对象；简单但**大数据会慢**。
- 可转移对象（Transferable）：不拷贝，**零拷贝**把所有权转移，适合大数据。
  - 支持：`ArrayBuffer`、`MessagePort`、`ImageBitmap`、`OffscreenCanvas` 等。
```js
// 传输二进制大数据（推荐）
const buffer = new ArrayBuffer(1024 * 1024);
worker.postMessage(buffer, [buffer]); // buffer 所有权被转移，主线程不可再用
```

## 什么时候要用 Web Worker（高价值场景）
- **计算密集**：图像处理（滤镜、缩略图）、音视频编解码、加密/哈希、PDF/Office 解析、地图投影。
- **大数据处理**：CSV/日志解析、搜索索引构建、排序/聚合、Diff/Patch（如虚拟表格）。
- **WASM/AI**：本地 ML 推理、压缩/解压（zstd/wasm）、语法高亮/格式化器（如 Prettier）。
- **绘制与可视化**：`OffscreenCanvas` 在 Worker 内绘制图表/游戏渲染。
- **避免长任务**：把 >50ms 的长任务拆分或丢到 Worker，降低主线程卡顿（优化 INP）。

## 与其他 Worker 的区别
- **Dedicated Worker**（最常用）：一个页面独占。
- **Shared Worker**：多个同源页面共享，适合多个标签页共享连接/状态。
- **Service Worker**：网络代理层，拦截请求、离线缓存、后台同步（不直接跑业务计算）。

## 最佳实践
- 模块化：使用 `type: 'module'`，在 worker 内写 ESM `import`。
- 通信协议：定义清晰的消息结构（`{type, payload}`），必要时使用 **Comlink** 简化 RPC。
- 数据传输：大对象用 Transferable；避免高频小消息（批量/节流）。
- 生命周期：任务完成及时 `terminate`；复杂场景使用**线程池**（如 `workerize`/`piscina`）。
- 错误处理：监听 `worker.onerror` 和 `worker.onmessageerror`。
- 监控：对计算时间、失败率打点；回退策略（任务过慢时在后台降级）。

## 与构建工具
- Vite/webpack 支持 `new URL('./worker.js', import.meta.url)` 静态分析产物。
- TypeScript：给 worker 单独的 `tsconfig` 或使用 `*.worker.ts` 约定简化配置。

## 小示例：使用 OffscreenCanvas 在 Worker 绘制
主线程：
```js
const canvas = document.querySelector('canvas');
const off = canvas.transferControlToOffscreen();
const worker = new Worker(new URL('./paint.js', import.meta.url), { type: 'module' });
worker.postMessage({ canvas: off }, [off]);
```

paint.js：
```js
self.onmessage = (e) => {
  const { canvas } = e.data;
  const ctx = canvas.getContext('2d');
  // 在 worker 线程里绘图
  ctx.fillStyle = 'orange';
  ctx.fillRect(0, 0, canvas.width, canvas.height);
};
```

## FAQ
- 能请求网络吗？可以（`fetch`、WebSocket）。
- 能用第三方库吗？可以（建议 ESM 版本）。
- 能访问 DOM 吗？不行；用消息把结果回传主线程更新 DOM。
- Safari/移动端支持？主流现代浏览器均支持模块 Worker；具体特性（如 OffscreenCanvas）按版本差异。

---

结论：当页面存在“可感知卡顿”的重计算或大数据处理时，把它搬到 Web Worker，可以显著提升交互流畅度和稳定性；结合可转移对象与线程池，进一步获得可观的性能收益。
