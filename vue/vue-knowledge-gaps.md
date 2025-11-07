# Vue 知识盲区复习

> 本文档记录在面试测试中发现的知识盲区和需要加强的部分

## 1. Vue 2 中 $set 的实现原理

### 问题
在 Vue 2 中，直接给对象添加新属性无法触发响应式更新，需要使用 `$set`。但为什么 `$set` 就能检测到变化？`$set` 是怎么实现的？

### 答案

`$set` 的核心实现原理：

```javascript
function set(target, key, val) {
  // 1. 如果是数组，使用 splice 方法（Vue 2 重写了数组方法）
  if (Array.isArray(target) && isValidArrayIndex(key)) {
    target.length = Math.max(target.length, key)
    target.splice(key, 1, val)  // splice 会触发响应式更新
    return val
  }
  
  // 2. 如果 key 已存在，直接赋值（会触发已有的 setter）
  if (key in target && !(key in Object.prototype)) {
    target[key] = val
    return val
  }
  
  // 3. 获取 target 的 __ob__ 属性（Observer 实例）
  const ob = target.__ob__
  
  // 4. 如果 target 不是响应式对象，直接赋值
  if (!ob) {
    target[key] = val
    return val
  }
  
  // 5. 关键：为新属性添加 getter/setter（调用 defineReactive）
  defineReactive(ob.value, key, val)
  
  // 6. 通知所有依赖该对象的 Watcher 进行更新
  ob.dep.notify()
  
  return val
}
```

**为什么 $set 能触发响应式更新？**

1. **调用 defineReactive**：为新属性添加 getter/setter，使其变成响应式
2. **依赖通知**：调用 `ob.dep.notify()` 通知所有依赖该对象的 Watcher 进行更新
3. **数组特殊处理**：对于数组，使用 `splice` 方法，Vue 2 重写了数组的变异方法，使其能够触发响应式更新

### 复习要点
- ✅ `$set` 通过 `defineReactive` 为新属性添加响应式
- ✅ `$set` 通过 `ob.dep.notify()` 通知依赖更新
- ✅ 数组使用 `splice` 方法触发响应式更新

---

## 2. Proxy 的实际应用场景和妙处

### 问题
知道 Proxy 可以相当于拦截器的能力，但 Proxy 在实际场景下有哪些妙处，或者用的非常好的点？

### 答案

#### Proxy 的核心优势

1. **完整的对象拦截能力**
   - 可以拦截对象的所有操作（get、set、has、deleteProperty 等 13 种操作）
   - 支持新增/删除属性、数组索引修改、数组长度变化

2. **深层响应式（懒代理）**
   - Vue 3 使用懒代理，只有在访问嵌套对象时才创建 Proxy
   - 性能更好，不需要递归遍历整个对象

3. **支持集合类型**
   ```javascript
   const map = reactive(new Map())
   map.set('key', 'value')  // ✅ 响应式
   
   const set = reactive(new Set())
   set.add(1)  // ✅ 响应式
   ```

#### Proxy 的实际应用场景

1. **数据验证**
   ```javascript
   const validator = {
     set(target, prop, value) {
       if (prop === 'email' && !value.includes('@')) {
         throw new Error('邮箱格式不正确')
       }
       target[prop] = value
       return true
     }
   }
   ```

2. **属性访问控制**
   ```javascript
   const secure = {
     get(target, prop) {
       if (prop.startsWith('_')) {
         throw new Error('私有属性不能访问')
       }
       return target[prop]
     }
   }
   ```

3. **性能监控**
   ```javascript
   const monitored = {
     get(target, prop) {
       performance.mark(`get-${prop}-start`)
       const result = target[prop]
       performance.mark(`get-${prop}-end`)
       return result
     }
   }
   ```

4. **数据缓存**
   ```javascript
   const cache = new Map()
   const cached = {
     get(target, prop) {
       if (cache.has(prop)) {
         return cache.get(prop)
       }
       const value = target[prop]
       cache.set(prop, value)
       return value
     }
   }
   ```

### 复习要点
- ✅ Proxy 可以拦截 13 种操作，比 Object.defineProperty 更强大
- ✅ Proxy 支持新增/删除属性、数组操作、集合类型
- ✅ Proxy 的实际应用：数据验证、访问控制、性能监控、缓存等

---

## 3. 生命周期钩子名称纠正

### 问题
写成了 `beforeCreated`，实际应该是 `beforeCreate`

### 正确答案

**Vue 2 生命周期完整顺序：**
```
1. beforeCreate  ✅ (不是 beforeCreated)
2. created
3. beforeMount
4. mounted
5. beforeUpdate
6. updated
7. beforeDestroy
8. destroyed
```

**Vue 3 生命周期（Composition API）：**
```javascript
import { 
  onBeforeMount,    // beforeMount
  onMounted,        // mounted
  onBeforeUpdate,   // beforeUpdate
  onUpdated,         // updated
  onBeforeUnmount,   // beforeDestroy (改名了)
  onUnmounted        // destroyed (改名了)
} from 'vue'
```

### 复习要点
- ✅ Vue 2: `beforeCreate`（不是 `beforeCreated`）
- ✅ Vue 3: `beforeUnmount` 和 `unmounted`（替代了 `beforeDestroy` 和 `destroyed`）

---

## 4. Object.defineProperty 的局限性总结

### 需要记住的局限性

1. ❌ **无法检测对象属性的添加或删除**
   - 需要使用 `$set` 或 `$delete`

2. ❌ **无法检测数组索引的变化**
   - 直接通过索引修改：`arr[0] = value` ❌
   - 需要使用 `$set` 或数组方法：`arr.splice(0, 1, value)` ✅

3. ❌ **无法检测数组长度的变化**
   - `arr.length = 0` ❌

4. ❌ **无法检测深层对象的新增属性**
   - `data.info.version = '2.x'` ❌
   - 需要使用 `$set(data.info, 'version', '2.x')` ✅

### 复习要点
- ✅ Object.defineProperty 只能劫持已存在的属性
- ✅ 新增属性、数组索引修改、数组长度变化都无法检测
- ✅ 需要使用 `$set` 或数组变异方法

---

## 5. Vue 2 vs Vue 3 响应式对比

### 关键区别

| 特性 | Vue 2 | Vue 3 |
|------|-------|-------|
| 检测属性添加 | ❌ 需要 $set | ✅ 自动检测 |
| 检测属性删除 | ❌ 需要 $delete | ✅ 自动检测 |
| 数组索引修改 | ❌ 需要 $set | ✅ 自动检测 |
| 数组长度变化 | ❌ 无法检测 | ✅ 自动检测 |
| 深层对象 | ⚠️ 需要递归遍历 | ✅ 懒代理 |
| 集合类型 | ❌ 不支持 | ✅ 支持 Map/Set |

### 复习要点
- ✅ Vue 3 的 Proxy 解决了 Vue 2 的所有局限性
- ✅ Vue 3 性能更好（懒代理、按需创建）
- ✅ Vue 3 支持更多数据类型（Map、Set 等）

---

*只记录知识盲区，针对性复习* 🎯
