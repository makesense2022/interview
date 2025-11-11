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

*后续思考和解答* 🤔

