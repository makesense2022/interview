# React 知识盲区复习

> 本文档记录在面试测试中发现的知识盲区和需要加强的部分

## 1. useState 的设计原理和闭包陷阱

### 问题
在 useEffect 中使用 setState 时，为什么会出现闭包陷阱？useState 是如何实现的？

### 闭包陷阱示例

```javascript
function Counter() {
  const [count, setCount] = useState(0);
  
  useEffect(() => {
    const timer = setInterval(() => {
      setCount(count + 1);  // ❌ 问题：count 永远是初始值 0
    }, 1000);
    
    return () => clearInterval(timer);
  }, []);  // 依赖数组为空
  
  return <div>{count}</div>;
}
```

**问题原因：**
- useEffect 的依赖数组为空，只在组件挂载时执行一次
- 闭包捕获了初始的 `count` 值（0）
- 每次 setInterval 回调执行时，使用的都是闭包中的 `count`（始终是 0）
- 所以 `count + 1` 永远是 `0 + 1 = 1`，不会递增

### useState 的设计原理

#### 基本实现（简化版）

```javascript
let state;  // 存储状态值
let setters = [];  // 存储 setter 函数
let stateIndex = 0;  // 当前 hook 的索引

function useState(initialValue) {
  const currentIndex = stateIndex;
  stateIndex++;
  
  // 初始化状态
  if (state[currentIndex] === undefined) {
    state[currentIndex] = initialValue;
  }
  
  // 创建 setter 函数
  const setState = (newValue) => {
    state[currentIndex] = newValue;
    // 触发重新渲染
    render();
  };
  
  setters[currentIndex] = setState;
  
  return [state[currentIndex], setState];
}
```

#### 函数式更新

```javascript
// useState 的 setter 可以接收函数
const setState = (newValue) => {
  if (typeof newValue === 'function') {
    // 函数式更新：使用最新的状态值
    state[currentIndex] = newValue(state[currentIndex]);
  } else {
    state[currentIndex] = newValue;
  }
  render();
};
```

### 如何修复闭包陷阱

#### 方法 1：使用函数式更新（推荐）

```javascript
useEffect(() => {
  const timer = setInterval(() => {
    setCount(prevCount => prevCount + 1);  // ✅ 使用函数式更新
  }, 1000);
  
  return () => clearInterval(timer);
}, []);  // 依赖数组可以为空
```

**原理：**
- 函数式更新 `prevCount => prevCount + 1` 中的 `prevCount` 是 React 传入的**最新状态值**
- 不依赖闭包中的 `count`，所以能获取到最新值

#### 方法 2：使用 useRef

```javascript
function Counter() {
  const [count, setCount] = useState(0);
  const countRef = useRef(count);
  
  // 保持 ref 和 state 同步
  useEffect(() => {
    countRef.current = count;
  }, [count]);
  
  useEffect(() => {
    const timer = setInterval(() => {
      setCount(countRef.current + 1);  // ✅ 使用 ref 获取最新值
    }, 1000);
    
    return () => clearInterval(timer);
  }, []);
  
  return <div>{count}</div>;
}
```

**原理：**
- `useRef` 返回的对象在组件的整个生命周期中保持不变
- `ref.current` 可以手动更新，不会触发重新渲染
- 通过 ref 可以访问到最新的值

#### 方法 3：将 count 加入依赖数组

```javascript
useEffect(() => {
  const timer = setInterval(() => {
    setCount(count + 1);
  }, 1000);
  
  return () => clearInterval(timer);
}, [count]);  // ✅ 将 count 加入依赖数组
```

**注意：** 这种方法会导致每次 count 变化时都重新创建定时器，可能不是最佳方案。

### 复习要点
- ✅ 闭包陷阱的原因：useEffect 闭包捕获了初始状态值
- ✅ 函数式更新可以获取最新状态值，不依赖闭包
- ✅ useRef 可以在不触发重新渲染的情况下保存最新值
- ✅ useState 的 setter 可以接收函数，函数接收最新状态值作为参数

---

## 2. React 批处理机制（React 17 vs React 18）

### 问题
React 17 和 React 18 在批处理方面有什么区别？如何确保状态更新被批处理？

### 错误理解纠正

**错误：** React 17 没有批处理，React 18 有批处理

**正确：** React 17 **也有批处理**，但只在 React 事件处理函数中批处理。React 18 扩展了批处理范围，在更多场景下自动批处理。

### React 17 的批处理

```javascript
function App() {
  const [count, setCount] = useState(0);
  const [name, setName] = useState('');
  
  const handleClick = () => {
    // ✅ React 17: 在事件处理函数中，这些更新会被批处理
    setCount(count + 1);
    setCount(count + 1);
    setCount(count + 1);
    setName('React');
    // 只会触发一次重新渲染，count = 1, name = 'React'
  };
}
```

**React 17 批处理的范围：**
- ✅ React 事件处理函数中
- ❌ Promise、setTimeout、原生事件处理函数中

#### React 17 批处理的实现原理

**核心机制：事件系统 + 更新队列**

1. **事件系统包装**
   ```javascript
   // React 17 内部实现（简化版）
   function dispatchEvent(event) {
     // 1. 设置批处理标志
     isBatchingUpdates = true;
     
     try {
       // 2. 执行用户的事件处理函数
       eventHandler(event);
       
       // 3. 批处理所有更新
       flushBatchedUpdates();
     } finally {
       // 4. 重置批处理标志
       isBatchingUpdates = false;
     }
   }
   ```

2. **更新队列机制**
   ```javascript
   // 更新队列（简化版）
   let updateQueue = [];
   let isBatchingUpdates = false;
   
   function setState(newState) {
     // 将更新加入队列
     updateQueue.push({
       state: newState,
       component: currentComponent
     });
     
     // 如果不在批处理中，立即处理
     if (!isBatchingUpdates) {
       flushUpdates();
     }
     // 如果在批处理中，等待批处理结束时统一处理
   }
   
   function flushBatchedUpdates() {
     // 合并所有更新
     const updates = updateQueue;
     updateQueue = [];
     
     // 批量处理更新
     updates.forEach(update => {
       applyUpdate(update);
     });
     
     // 触发一次重新渲染
     scheduleUpdate();
   }
   ```

3. **为什么三次 setCount(count + 1) 都是 1？**

   **关键理解：状态更新是覆盖，不是累加**
   
   ```javascript
   const handleClick = () => {
     // 执行时，count 的值是 0（闭包捕获）
     setCount(count + 1);  // 计算：0 + 1 = 1，准备更新为 1
     setCount(count + 1);  // 计算：0 + 1 = 1，准备更新为 1（覆盖上一个）
     setCount(count + 1);  // 计算：0 + 1 = 1，准备更新为 1（覆盖上一个）
   };
   ```
   
   **执行流程：**
   1. 三次 `setCount(count + 1)` 都读取的是**同一个闭包中的 count 值**（0）
   2. 三次计算都是 `0 + 1 = 1`
   3. React 将三个更新加入队列：`[1, 1, 1]`
   4. 批处理时，React 会**合并相同状态的更新**，只保留最后一个值
   5. 最终 `count` 更新为 `1`
   
   **状态合并机制（简化版）：**
   ```javascript
   function applyUpdate(update) {
     // 对于同一个状态，后面的更新会覆盖前面的
     if (update.component === currentComponent && 
         update.stateKey === 'count') {
       // 直接使用最新的值，不累加
       currentComponent.state.count = update.newState;
     }
   }
   ```
   
   **重要：** React 不会自动累加状态更新，每次 `setState` 都是**替换**状态值。

```javascript
const handleClick = () => {
  setTimeout(() => {
    // ❌ React 17: 不会批处理，会触发多次渲染
    setCount(count + 1);
    setCount(count + 1);
  }, 1000);
};
```

### React 18 的自动批处理

```javascript
function App() {
  const [count, setCount] = useState(0);
  
  const handleClick = () => {
    setTimeout(() => {
      // ✅ React 18: 自动批处理，只触发一次渲染
      setCount(count + 1);
      setCount(count + 1);
    }, 1000);
  };
}
```

**React 18 批处理的范围：**
- ✅ React 事件处理函数中
- ✅ Promise、setTimeout、原生事件处理函数中
- ✅ 异步操作中

#### React 18 为什么在 setTimeout 中也能批处理？

**核心改进：自动批处理（Automatic Batching）**

React 18 引入了**自动批处理**机制，不再依赖事件系统，而是通过**更新优先级和调度机制**实现。

1. **更新优先级系统**
   ```javascript
   // React 18 内部实现（简化版）
   let updateQueue = [];
   let isInsideEventHandler = false;
   
   function setState(newState) {
     // 创建更新对象
     const update = {
       state: newState,
       priority: getCurrentPriority(),  // 获取当前优先级
       timestamp: performance.now()
     };
     
     // 加入更新队列
     updateQueue.push(update);
     
     // 调度更新（统一调度，不立即执行）
     scheduleUpdate();
   }
   
   function scheduleUpdate() {
     // 使用 Scheduler 调度更新
     scheduleCallback(
       NormalPriority,  // 正常优先级
       () => {
         // 批处理所有更新
         flushUpdates();
       }
     );
   }
   
   function flushUpdates() {
     // 收集所有待处理的更新
     const updates = collectUpdates();
     
     // 合并相同状态的更新
     const mergedUpdates = mergeUpdates(updates);
     
     // 批量应用更新
     mergedUpdates.forEach(update => {
       applyUpdate(update);
     });
     
     // 触发一次重新渲染
     scheduleRender();
   }
   ```

2. **为什么 setTimeout 中也是 count + 1？**

   **关键：闭包捕获 + 状态覆盖机制**
   
   ```javascript
   function App() {
     const [count, setCount] = useState(0);
     
     const handleClick = () => {
       setTimeout(() => {
         // ⚠️ 注意：这里的 count 仍然是闭包捕获的初始值 0
         setCount(count + 1);  // 0 + 1 = 1
         setCount(count + 1);  // 0 + 1 = 1（覆盖上一个）
       }, 1000);
     };
   };
   ```
   
   **执行流程：**
   1. `setTimeout` 回调函数**闭包捕获**了 `count = 0`
   2. 两次 `setCount(count + 1)` 都基于 `count = 0` 计算，都是 `1`
   3. React 18 将两个更新加入队列：`[1, 1]`
   4. 批处理时，合并相同状态的更新，只保留最后一个值
   5. 最终 `count` 更新为 `1`（不是 2！）
   
   **重要区别：**
   - React 17：在 `setTimeout` 中**不会批处理**，会触发两次渲染，但每次渲染时 `count` 仍然是 `0`（闭包问题），所以最终也是 `1`
   - React 18：在 `setTimeout` 中**会批处理**，只触发一次渲染，最终 `count` 是 `1`
   
   **如果要让 count 变为 2，需要使用函数式更新：**
   ```javascript
   setTimeout(() => {
     setCount(count => count + 1);  // 0 → 1
     setCount(count => count + 1);  // 1 → 2
   }, 1000);
   ```

3. **React 18 批处理的实现细节**

   **核心：统一调度机制**
   - React 18 不再依赖事件系统来判断是否批处理
   - 所有状态更新都通过**统一的调度器**处理
   - 调度器会在**合适的时机**批量处理更新
   - 这个"合适的时机"包括：事件处理函数、Promise、setTimeout 等
   
   ```javascript
   // React 18 的批处理逻辑（简化版）
   function ensureRootIsScheduled(root) {
     // 检查是否有待处理的更新
     if (root.pendingUpdateLanes !== NoLanes) {
       // 调度更新任务
       scheduleCallback(
         NormalPriority,
         performConcurrentWorkOnRoot.bind(null, root)
       );
     }
   }
   
   function performConcurrentWorkOnRoot(root) {
     // 收集所有更新
     const updates = collectPendingUpdates(root);
     
     // 批处理更新
     processUpdates(updates);
     
     // 触发渲染
     commitRoot(root);
   }
   ```

### 题目答案纠正

```javascript
function App() {
  const [count, setCount] = useState(0);
  const [name, setName] = useState('');
  
  const handleClick = () => {
    setCount(count + 1);  // count = 0, 更新为 1
    setCount(count + 1);  // count = 0, 更新为 1（覆盖上一个）
    setCount(count + 1);  // count = 0, 更新为 1（覆盖上一个）
    setName('React');    // name = 'React'
  };
  
  // ✅ 结果：count = 1, name = 'React'（不是 3！）
  // 因为 setState 是异步的，三次 setCount(count + 1) 都基于初始值 0
}
```

**为什么 count 是 1 而不是 3？**
- 在同一个事件处理函数中，多次 `setCount(count + 1)` 都读取的是**同一个初始值** `count = 0`
- React 会批处理这些更新，但每次更新都是基于初始值
- 最终 `count` 只会更新一次，从 0 变为 1

**如果要让 count 变为 3，需要使用函数式更新：**
```javascript
setCount(count => count + 1);  // 0 → 1
setCount(count => count + 1);  // 1 → 2
setCount(count => count + 1);  // 2 → 3
```

### 如何确保状态更新被批处理

#### 1. 使用 React 18（自动批处理）

React 18 默认在所有场景下自动批处理，无需特殊处理。

#### 2. 使用 flushSync 强制同步更新（不批处理）

```javascript
import { flushSync } from 'react-dom';

function App() {
  const [count, setCount] = useState(0);
  
  const handleClick = () => {
    flushSync(() => {
      setCount(count + 1);  // 立即更新，不批处理
    });
    flushSync(() => {
      setCount(count + 1);  // 立即更新，不批处理
    });
    // 会触发两次渲染
  };
}
```

#### 3. 使用 startTransition 标记低优先级更新

```javascript
import { startTransition } from 'react';

function App() {
  const [count, setCount] = useState(0);
  const [isPending, startTransition] = useTransition();
  
  const handleClick = () => {
    setCount(count + 1);  // 高优先级更新
    
    startTransition(() => {
      setCount(count + 1);  // 低优先级更新，可能被批处理
    });
  };
}
```

### 深入理解：为什么多次 setState 只更新一次？

#### 核心原理：状态覆盖，不是累加

```javascript
// 错误理解：React 会自动累加
setCount(count + 1);  // 0 → 1
setCount(count + 1);  // 1 → 2  ❌ 错误！
setCount(count + 1);  // 2 → 3  ❌ 错误！

// 正确理解：每次都是基于初始值计算，然后覆盖
setCount(count + 1);  // 计算：0 + 1 = 1，准备更新为 1
setCount(count + 1);  // 计算：0 + 1 = 1，准备更新为 1（覆盖）
setCount(count + 1);  // 计算：0 + 1 = 1，准备更新为 1（覆盖）
// 最终：count = 1
```

#### 状态更新的执行时机

1. **同步阶段（事件处理函数执行时）**
   - 所有 `setState` 调用都是**同步执行**的
   - 但状态更新是**异步应用**的
   - 在事件处理函数执行期间，`count` 的值**不会改变**

2. **异步阶段（事件处理函数执行完后）**
   - React 收集所有更新
   - 合并相同状态的更新
   - 应用更新，触发重新渲染

#### 函数式更新 vs 直接更新

```javascript
// 直接更新：基于闭包中的值
setCount(count + 1);  // count = 0, 更新为 1
setCount(count + 1);  // count = 0, 更新为 1（覆盖）

// 函数式更新：基于最新状态值
setCount(count => count + 1);  // count = 0 → 1
setCount(count => count + 1);  // count = 1 → 2（累加）
```

**函数式更新的优势：**
- 函数接收的是**最新的状态值**，不是闭包中的值
- 可以基于最新值进行计算，实现累加效果
- 不依赖闭包，避免闭包陷阱

### 复习要点
- ✅ React 17 也有批处理，但只在事件处理函数中（通过事件系统实现）
- ✅ React 18 扩展了批处理范围，在更多场景下自动批处理（通过统一调度机制）
- ✅ **状态更新是覆盖，不是累加**：多次 `setState` 如果基于同一个初始值，最终只会更新一次
- ✅ 使用函数式更新可以让状态连续递增（基于最新值计算）
- ✅ React 18 默认自动批处理，无需特殊处理
- ✅ 在 `setTimeout` 中，React 18 会批处理，但仍然是基于闭包值计算，需要使用函数式更新才能累加

---

## 3. Diff 算法和 key 的作用

### 问题纠正

**场景1和场景2（有 key）：**
- ✅ 会复用组件，**不会**重新挂载
- React 通过 key 匹配，识别出是同一个组件，只是位置变化
- 会移动组件到新位置，但不会销毁和重新创建

**场景3和场景4（没有 key）：**
- ✅ 会重新渲染，因为 React 按位置比较
- 位置 0 的组件从 A 变为 B，类型不同，需要重新挂载
- 位置 1 的组件从 B 变为 A，类型不同，需要重新挂载

### Diff 算法的三个阶段

#### 1. 单节点 Diff
```javascript
// 只有一个子节点
<div>
  <ComponentA />
</div>
```

#### 2. 多节点 Diff（无 key）
```javascript
// 按位置比较
<div>
  <ComponentA />  // 位置 0
  <ComponentB />  // 位置 1
</div>
```

#### 3. 多节点 Diff（有 key）
```javascript
// 按 key 匹配
<div>
  <ComponentA key="a" />  // key="a"
  <ComponentB key="b" />  // key="b"
</div>
```

### key 的匹配机制

```javascript
// 场景1：有 key，交换顺序
<div>
  <ComponentA key="a" />
  <ComponentB key="b" />
</div>

// 场景2：交换后
<div>
  <ComponentB key="b" />  // key="b" 匹配，复用组件，移动到位置 0
  <ComponentA key="a" />  // key="a" 匹配，复用组件，移动到位置 1
</div>
```

**React 的处理过程：**
1. 创建 key 到 Fiber 节点的映射表
2. 遍历新节点，通过 key 查找是否存在旧节点
3. 如果找到，复用该节点，移动到新位置
4. 如果没找到，创建新节点
5. 标记需要删除的旧节点

### 复习要点
- ✅ 有 key 时，React 通过 key 匹配，可以复用组件，只移动位置
- ✅ 没有 key 时，React 按位置比较，类型不同会重新挂载
- ✅ key 的作用是帮助 React 识别哪些元素改变了、添加了或删除了
- ✅ key 应该是稳定、唯一、可预测的

---

## 4. useMemo 和 useCallback 的使用场景

### 判断标准

#### 1. 第一个 useMemo（expensiveValue）
```javascript
const expensiveValue = useMemo(() => {
  return count * 2;
}, [count]);
```

**是否有用？**
- ✅ **有用**：如果 `ExpensiveComponent` 用 `React.memo` 包装，且只依赖 `expensiveValue`
- ❌ **没用**：如果 `ExpensiveComponent` 没有用 `React.memo` 包装，或者依赖其他 props

**原因：**
- `useMemo` 的作用是**避免重复计算**
- 但如果子组件没有用 `memo` 优化，父组件重新渲染时子组件也会重新渲染
- 此时 `useMemo` 只能避免重复计算，不能避免子组件重新渲染

#### 2. 第二个 useMemo（simpleValue）
```javascript
const simpleValue = useMemo(() => {
  return name.toUpperCase();
}, [name]);
```

**是否有用？**
- ❌ **基本没用**：`toUpperCase()` 操作非常简单，计算开销可以忽略
- `useMemo` 本身也有开销（比较依赖数组），对于简单操作可能得不偿失

#### 3. 第一个 useCallback（handleClick）
```javascript
const handleClick = useCallback(() => {
  setCount(count + 1);
}, [count]);
```

**是否有用？**
- ❌ **基本没用**：依赖 `count`，每次 `count` 变化都会重新创建函数
- 如果 `Button` 组件没有用 `React.memo` 包装，`useCallback` 没有意义
- 即使 `Button` 用 `memo` 包装，由于依赖 `count`，函数引用还是会变化

**改进：**
```javascript
// 使用函数式更新，移除 count 依赖
const handleClick = useCallback(() => {
  setCount(prev => prev + 1);
}, []);  // ✅ 依赖数组为空，函数引用稳定
```

#### 4. 第二个 useCallback（handleChange）
```javascript
const handleChange = useCallback((e) => {
  setName(e.target.value);
}, []);
```

**是否有用？**
- ⚠️ **可能有用**：如果 `Input` 组件用 `React.memo` 包装，且只依赖 `onChange` prop
- ❌ **没用**：如果 `Input` 组件没有用 `memo` 包装

### 使用原则

1. **useMemo 用于昂贵的计算**
   - 计算开销 > useMemo 开销
   - 子组件用 `memo` 包装，且依赖该值

2. **useCallback 用于稳定的函数引用**
   - 子组件用 `memo` 包装
   - 函数依赖稳定（依赖数组为空或很少变化）

3. **不要过度使用**
   - 简单计算不需要 `useMemo`
   - 没有 `memo` 的子组件不需要 `useCallback`

### 复习要点
- ✅ useMemo 用于避免重复计算，但需要配合 `memo` 使用
- ✅ useCallback 用于稳定函数引用，但需要配合 `memo` 使用
- ✅ 简单操作不需要优化，可能得不偿失
- ✅ 函数式更新可以让 useCallback 的依赖数组为空

---

## 5. 并发渲染（Concurrent Rendering）

### 问题
并发渲染到底是什么意思？哪里并发？

### 并发渲染的含义

**重要理解：**
- ❌ **不是多线程并发**：JavaScript 是单线程的
- ✅ **是可中断的渲染**：渲染过程可以被中断，让浏览器处理高优先级任务
- ✅ **是时间切片**：将渲染工作分成多个小任务，在浏览器空闲时执行

### 并发渲染的工作原理

```
传统渲染（React 15）：
渲染开始 → 渲染完成 → 浏览器绘制 → 用户交互
         ↑________________________|
         如果渲染时间长，用户交互会被阻塞

并发渲染（React 18）：
渲染开始 → 中断（处理用户交互）→ 继续渲染 → 浏览器绘制
         ↑________________________|
         可以中断渲染，优先处理用户交互
```

### React 16 vs React 18 Suspense

#### React 16 Suspense
- 只支持 `React.lazy` 和代码分割
- 不支持数据获取的 Suspense

```javascript
// React 16: 只支持代码分割
const LazyComponent = React.lazy(() => import('./Component'));

<Suspense fallback={<Loading />}>
  <LazyComponent />
</Suspense>
```

#### React 18 Suspense
- 支持代码分割
- **支持数据获取的 Suspense**（实验性）
- 支持服务端渲染的 Suspense

```javascript
// React 18: 支持数据获取
function DataComponent() {
  const data = use(fetchData());  // 实验性 API
  return <div>{data}</div>;
}

<Suspense fallback={<Loading />}>
  <DataComponent />
</Suspense>
```

### useTransition vs useDeferredValue

#### useTransition
**用途：** 标记状态更新为低优先级，不阻塞 UI

```javascript
const [isPending, startTransition] = useTransition();

const handleClick = () => {
  // 高优先级更新
  setInputValue(newValue);
  
  // 低优先级更新
  startTransition(() => {
    setSearchResults(newResults);  // 不会阻塞 UI
  });
};

return (
  <div>
    {isPending && <Spinner />}
    <SearchResults results={results} />
  </div>
);
```

**使用场景：**
- 搜索输入框：输入是高优先级，搜索结果可以延迟
- 标签页切换：切换是高优先级，内容加载可以延迟

#### useDeferredValue
**用途：** 延迟更新某个值，保持旧值直到新值准备好

```javascript
const [query, setQuery] = useState('');
const deferredQuery = useDeferredValue(query);

// query 立即更新（高优先级）
// deferredQuery 延迟更新（低优先级）
return (
  <div>
    <Input value={query} onChange={e => setQuery(e.target.value)} />
    <SearchResults query={deferredQuery} />
  </div>
);
```

**使用场景：**
- 搜索输入框：输入框立即更新，搜索结果延迟更新
- 数据可视化：用户输入立即响应，图表更新可以延迟

### 区别总结

| 特性 | useTransition | useDeferredValue |
|------|--------------|------------------|
| 用途 | 标记状态更新为低优先级 | 延迟某个值的更新 |
| 使用方式 | 包装状态更新 | 包装值 |
| 返回值 | `[isPending, startTransition]` | 延迟后的值 |
| 适用场景 | 控制状态更新的优先级 | 控制值的更新时机 |

### 复习要点
- ✅ 并发渲染不是多线程，而是可中断的渲染
- ✅ 通过时间切片，将渲染工作分成小任务
- ✅ 可以中断低优先级渲染，优先处理高优先级任务（如用户交互）
- ✅ React 18 Suspense 支持数据获取（实验性）
- ✅ useTransition 用于标记状态更新为低优先级
- ✅ useDeferredValue 用于延迟某个值的更新

---

*只记录知识盲区，针对性复习* 🎯
