# 浏览器原理面试题

> 待思考和解答的浏览器相关问题

## 题目 1：浏览器渲染流程
**问题描述：**
从输入 URL 到页面渲染完成，浏览器经历了哪些主要步骤？请详细说明：
1. DNS 解析、TCP 连接、HTTP 请求等网络过程
2. HTML 解析、DOM 树构建、CSSOM 树构建
3. 渲染树（Render Tree）的生成
4. 布局（Layout）和绘制（Paint）
5. 重排（Reflow）和重绘（Repaint）的区别

**实际场景：** 理解渲染流程有助于优化页面性能，避免不必要的重排和重绘。

**考察点：** 浏览器渲染机制、关键渲染路径、性能优化


# 从输入 URL 到页面渲染：全流程与关键事件

## 总览路径
- **地址栏阶段**：补全/纠错、搜索或导航判断、HSTS 升级为 HTTPS
- **网络阶段**：DNS 解析 → TCP/QUIC 握手 → TLS/ALPN → 发送 HTTP 请求（可能预检/重定向）
- **导航阶段**：浏览器进程创建/复用渲染进程、跨站隔离、站点沙箱/CSP检查
- **资源获取**：Service Worker 拦截、HTTP 缓存/磁盘缓存、按优先级/协议复用拉取
- **解析构建**：HTML 解析构建 DOM、下载与解析 CSS/CSSOM、JS 执行、预加载扫描器
- **渲染流水线**：样式计算 → 布局（Layout）→ 分层 → 绘制（Paint）→ 合成（Composite）
- **交互与后续**：事件绑定、图片懒加载、额外资源请求、可见性/历史缓存（bfcache）
---

## 1. 地址栏与安全策略
- **URL 规范化**：补全协议、编码；判断是“搜索”还是“导航”
- **HSTS**：命中列表则强制 HTTPS
- **预连接/提示**：解析 `<link rel=preconnect|dns-prefetch|preload>` 或浏览器启发式

## 2. 网络与传输
- **DNS 解析**：浏览器缓存 → OS 缓存 → hosts → 递归解析（可能 DoH）
- **连接建立**：
  - TCP 三次握手；TLS 握手（ALPN 协商 HTTP/1.1、HTTP/2）
  - 或 QUIC/HTTP/3（UDP，0-RTT/1-RTT，内置加密）
- **请求发送**：
  - 附带 Cookie、`Accept-Language`、`Referer`、`Client Hints` 等
  - 命中 **Service Worker** `fetch` 拦截可走本地缓存/自定义响应
  - **CORS** 预检（`OPTIONS`）/ **Preload**/ **Early Hints(103)**
- **缓存/重定向**：
  - 强缓存（`Cache-Control: max-age`）/ 协商缓存（`ETag/If-None-Match`）
  - `301/302/307/308` 重定向链处理

## 3. 导航与进程模型
- **浏览器进程** 统筹导航，决定是否新建渲染进程（站点隔离）
- **安全检查**：CSP、CORP/COEP、混合内容、权限策略、SameSite Cookie

## 4. HTML 解析与阻塞规则
- **流式解析**：字节 → 文本 → Token → DOM 节点
- **CSS 阻塞渲染**：外链 CSS 阻塞首绘与 JS 执行顺序（影响 CRP）
- **JS 执行**：
  - 普通 `<script>` 阻塞解析；`defer` 延至 DOM 完成前执行；`async` 独立下载/就绪即执行
  - ES Module 并行下载、依赖解析、按图执行
- **预加载扫描器**：并行发现 `<img><script><link>` 等资源提前请求

## 5. 构建与渲染流水线（主线程为主）
- **样式计算（Style）**：DOM + CSSOM → 计算样式
- **布局（Layout）**：生成布局树、计算盒模型与几何
- **分层与栅格化**：创建合成层、位图栅格化（GPU 线程）
- **绘制与合成（Paint/Composite）**：绘制列表 → GPU 合成显示
- **增量更新**：样式/布局/绘制的最小化重排与重绘

## 6. 关键浏览器/DOM 事件时间点
- **`navigation`**：新导航开始（PerformanceEntry）
- **`DOMContentLoaded`**：初始 HTML 解析完成、`defer` 脚本执行完毕
- **`load`**：页面及其所有子资源（图片等）加载完成
- **`pageshow/pagehide`**：进入/离开页面；bfcache 恢复时 `pageshow.persisted = true`
- **`visibilitychange`**：可见性切换（后台/前台）
- **Service Worker**：`install` → `activate` → `fetch`
- **`beforeunload/unload`**：离开（不建议重逻辑）

## 7. 性能度量（Core Web Vitals 与关键指标）
- **`TTFB`**：首字节到达
- **`FP/FCP`**：首次/首内容绘制
- **`LCP`**：最大内容绘制（核心）
- **`CLS`**：累计位移（稳定性）
- **`FID/INP`**：首次输入延迟/交互响应（交互性）
- **`TTI/Long Task`**：可交互时间/长任务阻塞
- 观测：`PerformanceObserver`、`performance.getEntriesByType('navigation','resource')`

## 8. 影响渲染的策略与优化点
- **协议**：优先 HTTP/2 或 HTTP/3，合理复用与优先级
- **缓存**：`Cache-Control/ETag` + Service Worker 离线缓存
- **关键渲染路径**：内联首屏关键 CSS、`defer` JS、`async` 第三方
- **预加载**：`<link rel="preload">` 关键资源，`preconnect/dns-prefetch`
- **图片**：`loading="lazy"`、`decoding="async"`、`srcset/sizes`、现代格式（WebP/AVIF）
- **字体**：`font-display: swap`、子集化
- **安全与隔离**：CSP、COOP/COEP（可启用跨源隔离加速某些 API）

---

# 关键事件时间线速览
- 导航开始 → DNS/TCP/TLS → 请求发送 → 首字节到达（TTFB）
- HTML 流式解析/CSS 阻塞/JS 执行 → 首次绘制（FP/FCP）
- 最大内容绘制（LCP）→ `DOMContentLoaded` → 资源加载完毕 → `load`
- 交互与后续请求 → 可见性/历史缓存事件（`pageshow/pagehide`）

---

任务状态：已概述从 URL 输入到页面渲染的完整过程，并列出关键事件与性能指标。需要我给出一张“首屏关键渲染路径优化清单”或结合你项目做针对性建议吗？
---

## 题目 2：事件循环（Event Loop）
**问题描述：**
```javascript
console.log('1');

setTimeout(() => {
  console.log('2');
}, 0);

Promise.resolve().then(() => {
  console.log('3');
}).then(() => {
  console.log('4');
});

console.log('5');
```

1. 输出顺序是什么？为什么？
2. 什么是宏任务（Macro Task）和微任务（Micro Task）？
3. 浏览器的事件循环机制是如何工作的？
4. requestAnimationFrame 在事件循环中的位置是什么？

**实际场景：** 理解事件循环有助于编写正确的异步代码，避免性能问题。

**考察点：** 事件循环、宏任务、微任务、执行顺序

---

## 题目 3：浏览器缓存机制
**问题描述：**
1. 浏览器有哪些缓存机制？（强缓存、协商缓存）
2. Cache-Control、Expires、ETag、Last-Modified 的作用和区别？
3. 强缓存和协商缓存的执行流程是什么？
4. 如何设置合理的缓存策略？

**实际场景：** 合理的缓存策略可以显著提升页面加载速度，减少服务器压力。

**考察点：** HTTP 缓存、缓存策略、性能优化

---

## 题目 4：跨域问题
**问题描述：**
1. 什么是同源策略（Same-Origin Policy）？为什么需要同源策略？
2. 有哪些跨域解决方案？（CORS、JSONP、代理等）
3. CORS 的工作原理是什么？简单请求和复杂请求的区别？
4. 为什么 JSONP 只支持 GET 请求？

**实际场景：** 在前后端分离的开发中，跨域问题是常见的，需要理解其原理和解决方案。

**考察点：** 同源策略、CORS、跨域解决方案

---

## 题目 5：浏览器存储
**问题描述：**
1. Cookie、LocalStorage、SessionStorage、IndexedDB 的区别？
2. Cookie 的属性有哪些？（Domain、Path、Expires、HttpOnly、Secure、SameSite）
3. 什么时候应该使用 Cookie？什么时候使用 LocalStorage？
4. LocalStorage 和 SessionStorage 的容量限制是多少？

**实际场景：** 选择合适的存储方式可以提升用户体验，避免安全问题。

**考察点：** 浏览器存储、Cookie、LocalStorage、SessionStorage

---

## 题目 6：性能优化
**问题描述：**
以下代码有什么性能问题？如何优化？

```javascript
// 场景1：频繁操作 DOM
for (let i = 0; i < 1000; i++) {
  const div = document.createElement('div');
  div.textContent = i;
  document.body.appendChild(div);
}

// 场景2：频繁读取布局信息
for (let i = 0; i < 100; i++) {
  const width = element.offsetWidth;
  element.style.width = width + 10 + 'px';
}

// 场景3：滚动事件
window.addEventListener('scroll', () => {
  console.log('scrolling');
});
```

**实际场景：** 性能优化是前端开发的重要技能，需要理解浏览器的渲染机制。

**考察点：** DOM 操作优化、重排重绘、事件节流防抖

---

## 题目 7：V8 引擎和垃圾回收
**问题描述：**
1. V8 引擎是如何执行 JavaScript 代码的？（解析、编译、执行）
2. 什么是 JIT（Just-In-Time）编译？
3. V8 的垃圾回收机制是什么？（新生代、老生代、标记清除、引用计数）
4. 什么情况下会导致内存泄漏？如何避免？

**实际场景：** 理解 V8 引擎有助于编写高性能的 JavaScript 代码，避免内存泄漏。

**考察点：** V8 引擎、垃圾回收、内存管理

---

## 题目 8：DNS 缓存
**问题描述：**
什么是 DNS 缓存？有哪些层级？TTL 如何影响缓存有效期？如何清理或绕过缓存？

**解答：**

- **定义**：把“域名 → 解析结果（A/AAAA/CNAME 等）”在多级节点上暂存一段时间，减少重复解析、降低延迟与上游负载。
- **作用**：显著加速访问、减少权威/递归 DNS 查询次数、提升可用性（部分实现支持短暂过期容忍）。

**缓存层级**
- **浏览器缓存**：浏览器进程内命中表（不同浏览器策略不同）。
- **操作系统缓存**：系统解析器/守护进程（如 macOS 的 mDNSResponder）。
- **本地/边缘设备**：路由器、企业 DNS、CDN 边缘递归器。
- **递归解析器**：ISP/公共 DNS（8.8.8.8、1.1.1.1、DoH 服务器等）。
说明：`hosts` 不是缓存，而是静态映射，通常优先于 DNS 查询。

**生命周期与 TTL**
- **TTL（Time To Live）**：权威 DNS 为各记录设置的有效期（秒）。在 TTL 内各层可直接返回缓存，不再向上游查询。
- **负缓存（Negative Caching）**：对 NXDOMAIN/NODATA 的“无此记录”也会缓存，TTL 来自权威区 SOA（RFC 2308）。
- **策略差异**：递归器可能设置最小/最大 TTL，或支持 serve-stale（上游故障时短期继续用过期记录）。

**命中与失效**
- **键值维度**：按“名称 + 记录类型（A/AAAA/TXT…）”区分；A 与 AAAA 分开缓存。
- **失效条件**：TTL 到期、显式清空、网络/服务重启、策略变更。
- **变更生效延迟**：全网多级缓存需等待旧 TTL 过期；变更前应先将 TTL 降低（如 3600s → 60s），变更完成后再回升。

**常见问题与建议**
- 变更不生效：多级缓存未过期。对策：提前降 TTL，改后等待，必要时引导清缓存。
- IPv6 相关：客户端常先查 AAAA，若链路不佳会超时；评估 A/AAAA 策略或启用 Happy Eyeballs。
- 分流与污染：公共递归器与本地递归器可能返回不同；重要业务考虑自建/权威 DoH、EDNS 客户端子网等。

**实用排查与清理（macOS）**
- 查询：`dig example.com A +trace`（链路跟踪）、`dig example.com A`（看 TTL）。
- 查看系统解析配置：`scutil --dns`。
- 清空系统 DNS 缓存：
  - `sudo dscacheutil -flushcache`
  - `sudo killall -HUP mDNSResponder`
- 浏览器层：重启浏览器或等待 TTL；部分浏览器提供内部网络调试页面可清理（实现差异较大）。

**一句话总结**
DNS 缓存是分层的“解析结果”短期存储，由权威 DNS 设置的 TTL 控制生命周期；它提升性能，但变更时需考虑全网缓存逐步失效带来的传播延迟。
