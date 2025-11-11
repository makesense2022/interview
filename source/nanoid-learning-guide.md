# nanoid 源码阅读指南

> 从最简单的项目开始，建立信心！

## 项目概览

**nanoid** 是一个轻量级的 ID 生成器，核心代码只有约 100 行。

**特点：**
- 🚀 快速：比 UUID 快 60%
- 🔒 安全：使用加密安全的随机 API
- 📦 轻量：只有 130 字节（gzip 后）
- 🎯 URL 友好：使用 URL 安全字符

## 核心文件

### 1. `index.js` - 主文件（约 50 行）

**位置：** `./nanoid/index.js`

**核心功能：** 同步生成 ID

**关键代码：**
```javascript
// 简化版核心逻辑
export const nanoid = (size = 21) => {
  let id = ''
  let bytes = crypto.getRandomValues(new Uint8Array(size))
  
  while (size--) {
    id += urlAlphabet[bytes[size] & 63]
  }
  
  return id
}
```

**学习要点：**
1. 如何使用 `crypto.getRandomValues()` 生成随机数
2. 为什么使用 `& 63` 进行位运算（取模优化）
3. 为什么默认长度是 21

### 2. `url-alphabet/index.js` - 字符集

**位置：** `./nanoid/url-alphabet/index.js`

**内容：**
```javascript
export const urlAlphabet =
  'useandom-26T198340PX75pxJACKVERYMINDBUSHWOLF_GQZbfghjklqvwyzrict'
```

**学习要点：**
1. 为什么是这 64 个字符？
2. 为什么不用标准的 Base64？
3. URL 安全字符的定义

### 3. `non-secure/index.js` - 非安全版本

**位置：** `./nanoid/non-secure/index.js`

**用途：** 不需要加密安全的场景（如测试）

**区别：** 使用 `Math.random()` 而不是 `crypto.getRandomValues()`

---

## 阅读步骤

### 第 1 步：理解需求（10 分钟）

**问题：**
1. 为什么需要 ID 生成器？
2. nanoid 和 UUID 有什么区别？
3. 什么场景下使用 nanoid？

**答案：**
- UUID 太长（36 字符），不适合 URL
- nanoid 更短（21 字符），URL 友好
- 适合生成短链接、订单号、文件名等

### 第 2 步：阅读核心代码（30 分钟）

**打开文件：** `./nanoid/index.js`

**逐行阅读：**

```javascript
// 1. 导入字符集
import { urlAlphabet } from './url-alphabet/index.js'
import crypto from './crypto.js'

// 2. 定义 nanoid 函数
export const nanoid = (size = 21) => {
  let id = ''
  // 3. 生成随机字节数组
  let bytes = crypto.getRandomValues(new Uint8Array(size))
  
  // 4. 将随机字节转换为字符
  while (size--) {
    // 5. 使用位运算取模（& 63 等价于 % 64）
    id += urlAlphabet[bytes[size] & 63]
  }
  
  return id
}

// 6. 自定义字符集版本
export const customAlphabet = (alphabet, defaultSize = 21) => {
  return (size = defaultSize) => {
    let id = ''
    let bytes = crypto.getRandomValues(new Uint8Array(size))
    while (size--) {
      // 使用自定义字符集
      id += alphabet[bytes[size] & 255]
    }
    return id
  }
}
```

**关键问题：**
1. 为什么使用 `& 63`？
   - 63 的二进制是 `111111`（6 位全 1）
   - `bytes[size] & 63` 相当于取最后 6 位
   - 结果范围是 0-63，正好对应 64 个字符

2. 为什么默认长度是 21？
   - 21 个字符，每个字符 6 位，总共 126 位随机性
   - 碰撞概率极低（1% 概率需要生成 4 百万亿个 ID）

3. 为什么不用 `% 64`？
   - 位运算 `&` 比取模 `%` 快得多
   - 但只适用于 2 的幂次（64 = 2^6）

### 第 3 步：调试代码（20 分钟）

**创建测试文件：** `test-nanoid.js`

```javascript
import { nanoid, customAlphabet } from './nanoid/index.js'

// 测试 1：生成默认 ID
console.log('默认 ID:', nanoid())
// 输出：V1StGXR8_Z5jdHi6B-myT

// 测试 2：生成指定长度的 ID
console.log('长度 10:', nanoid(10))
// 输出：IRFa-VaY2b

// 测试 3：自定义字符集
const customId = customAlphabet('0123456789', 6)
console.log('自定义 ID:', customId())
// 输出：123456

// 测试 4：观察随机性
for (let i = 0; i < 5; i++) {
  console.log(`ID ${i + 1}:`, nanoid(10))
}
```

**运行测试：**
```bash
cd nanoid
node test-nanoid.js
```

### 第 4 步：深入理解（30 分钟）

**问题 1：为什么使用 crypto.getRandomValues()？**

```javascript
// 不安全的方式（不要用于生产）
Math.random() // 伪随机，可预测

// 安全的方式
crypto.getRandomValues(new Uint8Array(21)) // 加密安全的随机数
```

**问题 2：如何计算碰撞概率？**

```javascript
// 生日悖论公式
// P(碰撞) ≈ n² / (2 * 可能性总数)
// 
// 对于 nanoid (21 个字符，64 种可能)：
// 可能性总数 = 64^21 ≈ 2^126
// 
// 生成 1 亿个 ID 的碰撞概率：
// P ≈ (10^8)² / (2 * 2^126) ≈ 0.000000000000000001%
```

**问题 3：为什么不用 UUID？**

```javascript
// UUID v4
'110ec58a-a0f2-4ac4-8393-c866d813b8d1' // 36 字符

// nanoid
'V1StGXR8_Z5jdHi6B-myT' // 21 字符

// 优势：
// 1. 更短，节省存储空间
// 2. URL 友好，不需要编码
// 3. 更快，性能更好
```

---

## 实践任务

### 任务 1：实现一个简化版 nanoid

```javascript
// 你的实现
function myNanoid(size = 21) {
  // TODO: 实现 nanoid
}

// 测试
console.log(myNanoid()) // 应该输出 21 个字符的随机 ID
```

### 任务 2：实现一个数字 ID 生成器

```javascript
// 只使用数字 0-9
function numericId(size = 10) {
  // TODO: 实现
}

// 测试
console.log(numericId()) // 应该输出 10 位数字
```

### 任务 3：性能测试

```javascript
// 比较 nanoid 和 UUID 的性能
import { nanoid } from './nanoid/index.js'
import { v4 as uuidv4 } from 'uuid'

console.time('nanoid')
for (let i = 0; i < 100000; i++) {
  nanoid()
}
console.timeEnd('nanoid')

console.time('uuid')
for (let i = 0; i < 100000; i++) {
  uuidv4()
}
console.timeEnd('uuid')
```

---

## 学习收获

### 技术点

1. ✅ 如何使用 `crypto.getRandomValues()` 生成安全的随机数
2. ✅ 位运算的优化技巧（`& 63` 代替 `% 64`）
3. ✅ 如何设计简洁的 API
4. ✅ 如何计算碰撞概率
5. ✅ URL 安全字符的选择

### 设计思想

1. ✅ **简洁优于复杂**：核心代码只有几十行
2. ✅ **性能优化**：使用位运算代替取模
3. ✅ **安全第一**：使用加密安全的随机 API
4. ✅ **灵活性**：提供自定义字符集的能力
5. ✅ **文档完善**：README 详细说明使用方法和原理

---

## 下一步

1. ✅ 完成上面的实践任务
2. ✅ 阅读 `non-secure/index.js`，理解非安全版本
3. ✅ 阅读测试文件 `test/index.test.js`，学习如何写测试
4. ✅ 尝试提交一个 PR（如完善文档、添加示例）
5. ✅ 继续学习 Zustand，理解更复杂的状态管理

---

## 常见问题

### Q1: 为什么不用 UUID？
A: UUID 太长（36 字符），nanoid 更短（21 字符），且 URL 友好。

### Q2: nanoid 安全吗？
A: 是的，使用加密安全的 `crypto.getRandomValues()`，碰撞概率极低。

### Q3: 可以用于生产环境吗？
A: 可以，已被广泛使用（如 Next.js、Prisma 等）。

### Q4: 如何选择 ID 长度？
A: 默认 21 已经足够安全，如果需要更短的 ID，可以适当减少长度，但要注意碰撞概率。

---

*恭喜你完成了第一个源码阅读！* 🎉

**下一步：** 开始阅读 Zustand，理解状态管理的实现。

