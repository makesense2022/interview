# 源码阅读学习

> 一起阅读优秀开源项目的源码，提升技术能力

## 项目列表

### 1. Zustand
- **路径**: `./zustand/`
- **仓库**: https://github.com/pmndrs/zustand
- **描述**: 轻量级状态管理库
- **核心代码**: `src/vanilla.ts`, `src/react.ts`
- **代码量**: ~500 行
- **难度**: ⭐⭐ (入门)

### 2. VueUse
- **路径**: `./vueuse/`
- **仓库**: https://github.com/vueuse/vueuse
- **描述**: Vue 组合式函数集合
- **核心代码**: `packages/core/` 下的各个函数
- **代码量**: 模块化，每个函数独立
- **难度**: ⭐⭐ (入门)

### 3. nanoid
- **路径**: `./nanoid/`
- **仓库**: https://github.com/ai/nanoid
- **描述**: 轻量级 ID 生成器
- **核心代码**: `index.js`, `async.js`
- **代码量**: ~100 行
- **难度**: ⭐ (非常简单)

---

## 阅读顺序建议

### 第 1 周：nanoid（最简单）
从最简单的项目开始，建立信心。

**学习目标：**
- 理解 ID 生成算法
- 学习如何使用 crypto API
- 理解同步和异步版本的区别

**核心文件：**
1. `index.js` - 同步版本
2. `async.js` - 异步版本
3. `url-alphabet/index.js` - URL 安全字符集

### 第 2-3 周：Zustand（核心）
深入理解状态管理的实现。

**学习目标：**
- 理解发布订阅模式
- 学习如何设计简洁的 API
- 理解 React 集成的实现

**核心文件：**
1. `src/vanilla.ts` - 核心状态管理（约 100 行）
2. `src/react.ts` - React 集成（约 50 行）
3. `src/middleware/` - 中间件实现

### 第 4-6 周：VueUse（实践）
学习实用工具函数的设计。

**学习目标：**
- 学习组合式函数的设计模式
- 理解响应式系统的应用
- 学习如何处理各种实际场景

**推荐函数（从简单到复杂）：**
1. `useToggle` - 布尔值切换
2. `useCounter` - 计数器
3. `useLocalStorage` - 本地存储
4. `useFetch` - 数据请求
5. `useIntersectionObserver` - 交叉观察器

---

## 学习方法

### 1. 运行项目

```bash
# Zustand
cd zustand
pnpm install
pnpm dev

# nanoid
cd nanoid
pnpm install
pnpm test

# VueUse
cd vueuse
pnpm install
pnpm dev
```

### 2. 调试代码

在 VS Code 中打开项目，设置断点，单步调试。

### 3. 记录笔记

在每个项目下创建 `LEARNING.md`，记录学习笔记。

### 4. 尝试修改

尝试修改代码，添加功能，观察效果。

---

## 下一步

1. 从 nanoid 开始，快速建立信心
2. 深入学习 Zustand，理解状态管理
3. 实践 VueUse，学习实用工具函数
4. 记录学习笔记，分享经验

*开始阅读源码吧！* 📖

