# JavaScript 位运算与类型转换

> 理解位运算的类型转换机制和实际应用

## 问题描述

在阅读 nanoid 源码时，看到这样的代码：

```javascript
export const nanoid = (size = 21) => {
  size |= 0  // 这是什么意思？
  // ...
}
```

**问题：**
1. `size |= 0` 是什么意思？
2. 为什么能实现取整？
3. 位运算取整的原理是什么？

---

## 实际场景

### 场景 1：参数标准化

```javascript
// 确保函数参数是整数
function createArray(size) {
  size |= 0  // 防止传入小数或字符串
  return new Array(size)
}

createArray(10.5)  // 创建长度为 10 的数组
createArray('8')   // 创建长度为 8 的数组
```

### 场景 2：性能优化

```javascript
// 高性能库中常见的优化技巧
// 例如：游戏引擎、图形处理、数据处理

// 快速取整（比 Math.floor 快 40%）
const x = (mouseX * scale) | 0
const y = (mouseY * scale) | 0
```

### 场景 3：颜色值处理

```javascript
// RGB 颜色值必须是 0-255 的整数
function rgbToHex(r, g, b) {
  r |= 0  // 确保是整数
  g |= 0
  b |= 0
  return '#' + ((1 << 24) + (r << 16) + (g << 8) + b).toString(16).slice(1)
}

rgbToHex(255.7, 128.3, 64.9)  // '#ff8040'
```

---

## 问题本质

### 核心原理：ToInt32 抽象操作

**位运算只能操作 32 位整数，JavaScript 会自动进行类型转换。**

#### ECMAScript 规范中的 ToInt32 操作步骤：

```javascript
// ToInt32(value) 的执行步骤：

// 1. 调用 ToNumber(value) 转换为数字
// 2. 如果是 NaN, +0, -0, +∞, -∞，返回 +0
// 3. 取整数部分（向零方向取整，丢弃小数）
// 4. 对 2^32 取模
// 5. 如果结果 >= 2^31，减去 2^32（处理符号）
```

#### 示例演示：

```javascript
// 步骤 1: ToNumber
'123' | 0  // '123' → 123 (字符串转数字)

// 步骤 2: 特殊值处理
NaN | 0        // 0
Infinity | 0   // 0
null | 0       // 0
undefined | 0  // 0

// 步骤 3: 取整数部分（向零取整）
3.14 | 0   // 3 (丢弃 .14)
-3.14 | 0  // -3 (丢弃 .14)

// 步骤 4-5: 32 位整数范围处理
2147483647 | 0   // 2147483647 (最大 32 位有符号整数)
2147483648 | 0   // -2147483648 (溢出，变成负数)
```

---

## 解决方案

### 1. `| 0` 的工作原理

```javascript
// 语法
value | 0

// 等价于
value = ToInt32(value) | 0

// 由于 0 的所有位都是 0，任何数 | 0 = 原数
// 所以实际效果就是 ToInt32 转换
```

### 1.1 按位与（`&`）到底是怎么操作的？

**按位与**会逐位比较两个二进制数，只有当某一位的两个操作数都为 `1` 时，该位的结果才为 `1`，否则为 `0`。

```javascript
// 真值表（Truth Table）
// A & B → 结果
0 & 0 // 0
0 & 1 // 0
1 & 0 // 0
1 & 1 // 1
```

#### 示例：`5 & 3`

```javascript
// 5 → 二进制 0101
// 3 → 二进制 0011
// ----------------
// 结果   0001 → 十进制 1

5 & 3 // 1
```

#### 示例：`200 & 63`

```javascript
// 200 → 二进制 11001000
//  63 → 二进制 00111111
// ---------------------
// 结果 → 二进制 00001000 → 十进制 8

200 & 63 // 8
```

#### 常见用途

```javascript
// 1. 与掩码（mask）配合使用，提取指定位
const mask = 0b00111111 // 63
const result = pool[i] & mask // 只保留最后 6 位

// 2. 判断某一位是否为 1
const FLAG_READ = 1 << 0 // 0001
const FLAG_WRITE = 1 << 1 // 0010

const permissions = FLAG_READ | FLAG_WRITE // 0011
const canWrite = (permissions & FLAG_WRITE) !== 0 // true

// 3. 快速取模（2 的幂次）
num & 7   // 等价于 num % 8
num & 15  // 等价于 num % 16
```

> 小结：`pool[i] & 63` 就是把随机字节的最后 6 位取出来，从而将 0-255 的范围压缩到 0-63，以便索引 64 个字符的字母表。

### 2. 向零取整 vs 向下取整

**重要区别：**

```javascript
// 正数：向零取整 = 向下取整
3.7 | 0          // 3
Math.floor(3.7)  // 3

// 负数：向零取整 ≠ 向下取整
-3.7 | 0          // -3 (向零取整，朝 0 方向)
Math.floor(-3.7)  // -4 (向下取整，朝负无穷方向)

// 图解：
//        -4         -3         -2         -1          0          1          2          3          4
//         |          |          |          |          |          |          |          |          |
//         ↓          ↑                                                                 ↑
//    floor(-3.7)  -3.7|0                                                            3.7|0
//                                                                              floor(3.7)
```

### 3. 常见位运算取整技巧

```javascript
// 方法 1: | 0 (最常用)
3.14 | 0  // 3

// 方法 2: ~~ (双波浪号)
~~3.14  // 3
// 原理：~3.14 先按位非，再 ~ 一次恢复，过程中完成 ToInt32

// 方法 3: >> 0 (右移 0 位)
3.14 >> 0  // 3

// 方法 4: << 0 (左移 0 位)
3.14 << 0  // 3

// 方法 5: ^ 0 (异或 0)
3.14 ^ 0  // 3
```

### 4. 各种取整方法对比

```javascript
const num = 3.7

// 向零取整（丢弃小数）
num | 0           // 3
~~num             // 3
num >> 0          // 3
parseInt(num)     // 3

// 向下取整（朝负无穷）
Math.floor(num)   // 3
Math.floor(-3.7)  // -4

// 向上取整（朝正无穷）
Math.ceil(num)    // 4
Math.ceil(-3.7)   // -3

// 四舍五入
Math.round(num)   // 4
Math.round(3.4)   // 3

// 向零取整（另一种方式）
Math.trunc(num)   // 3 (ES6)
Math.trunc(-3.7)  // -3
```

---

## 知识拓展

### 1. 性能对比

```javascript
// 性能测试（100 万次操作）
const num = 3.14159

console.time('| 0')
for (let i = 0; i < 1000000; i++) {
  let x = num | 0
}
console.timeEnd('| 0')  // ~3ms

console.time('~~')
for (let i = 0; i < 1000000; i++) {
  let x = ~~num
}
console.timeEnd('~~')  // ~3ms

console.time('Math.floor')
for (let i = 0; i < 1000000; i++) {
  let x = Math.floor(num)
}
console.timeEnd('Math.floor')  // ~5ms

console.time('Math.trunc')
for (let i = 0; i < 1000000; i++) {
  let x = Math.trunc(num)
}
console.timeEnd('Math.trunc')  // ~4ms

console.time('parseInt')
for (let i = 0; i < 1000000; i++) {
  let x = parseInt(num)
}
console.timeEnd('parseInt')  // ~15ms

// 结论：| 0 和 ~~ 最快，但可读性较差
```

### 2. 32 位整数范围限制

```javascript
// 安全范围：-2^31 到 2^31 - 1
const MAX_INT32 = 2147483647   // 2^31 - 1
const MIN_INT32 = -2147483648  // -2^31

// 在范围内
2147483647 | 0   // 2147483647 ✓
-2147483648 | 0  // -2147483648 ✓

// 超出范围会溢出
2147483648 | 0   // -2147483648 ✗ (溢出)
9999999999 | 0   // 1410065407 ✗ (错误结果)

// 大数应该使用 Math.floor
Math.floor(9999999999)  // 9999999999 ✓
```

### 3. 类型转换表

```javascript
// 各种类型通过 | 0 转换的结果

// 数字
3.14 | 0        // 3
-3.14 | 0       // -3
0 | 0           // 0

// 字符串
'123' | 0       // 123
'3.14' | 0      // 3
'abc' | 0       // 0 (NaN → 0)
'' | 0          // 0

// 布尔值
true | 0        // 1
false | 0       // 0

// 特殊值
null | 0        // 0
undefined | 0   // 0
NaN | 0         // 0
Infinity | 0    // 0
-Infinity | 0   // 0

// 对象
[] | 0          // 0
[5] | 0         // 5
[1,2] | 0       // 0
{} | 0          // 0
```

### 4. 实际应用案例

#### 案例 1：nanoid 源码

```javascript
// nanoid/index.js
export const nanoid = (size = 21) => {
  size |= 0  // 确保 size 是整数
  let id = ''
  let bytes = crypto.getRandomValues(new Uint8Array(size))
  while (size--) {
    id += urlAlphabet[bytes[size] & 63]
  }
  return id
}

// 好处：
// 1. 防止传入小数：nanoid(10.5) → size = 10
// 2. 防止传入字符串：nanoid('8') → size = 8
// 3. 性能优化：比 Math.floor 快
```

#### 案例 2：Canvas 像素操作

```javascript
// 图像处理中的坐标计算
function getPixel(imageData, x, y) {
  // 确保坐标是整数
  x |= 0
  y |= 0
  
  const index = (y * imageData.width + x) * 4
  return {
    r: imageData.data[index],
    g: imageData.data[index + 1],
    b: imageData.data[index + 2],
    a: imageData.data[index + 3]
  }
}
```

#### 案例 3：游戏开发

```javascript
// 游戏中的碰撞检测
class Sprite {
  constructor(x, y) {
    this.x = x | 0  // 确保是整数坐标
    this.y = y | 0
  }
  
  move(dx, dy) {
    this.x = (this.x + dx) | 0
    this.y = (this.y + dy) | 0
  }
}
```

---

## 复习要点

### 核心知识点

1. ✅ **位运算会触发 ToInt32 转换**
   - 自动将操作数转换为 32 位有符号整数
   - 过程中会丢弃小数部分

2. ✅ **`| 0` 的作用**
   - 将任何值转换为 32 位整数
   - 丢弃小数部分（向零取整）
   - 性能优于 `Math.floor()`

3. ✅ **向零取整 vs 向下取整**
   - 向零取整：朝 0 方向（`| 0`, `~~`, `Math.trunc()`）
   - 向下取整：朝负无穷（`Math.floor()`）
   - 正数时两者相同，负数时不同

4. ✅ **32 位整数范围限制**
   - 安全范围：-2,147,483,648 到 2,147,483,647
   - 超出范围会溢出，产生错误结果
   - 大数应使用 `Math.floor()` 等方法

5. ✅ **性能 vs 可读性权衡**
   - `| 0` 性能最好，但可读性差
   - `Math.floor()` 性能稍慢，但语义清晰
   - 选择取决于场景：性能敏感用位运算，否则用 Math 方法

### 面试常见问题

**Q1: `~~` 和 `| 0` 有什么区别？**

A: 效果完全相同，都是 ToInt32 转换。`~~` 是两次按位非，`| 0` 是按位或 0。性能相近，`| 0` 更常见。

**Q2: 为什么 `-3.7 | 0` 是 -3 而不是 -4？**

A: 因为位运算是向零取整（丢弃小数），不是向下取整。-3.7 去掉小数是 -3，不是 -4。

**Q3: 什么时候应该使用位运算取整？**

A: 
- ✅ 性能敏感的场景（游戏、图形处理）
- ✅ 数值在 32 位整数范围内
- ✅ 团队熟悉这种写法
- ❌ 需要处理大数
- ❌ 代码可读性优先

**Q4: `| 0` 能处理字符串吗？**

A: 可以，会先调用 ToNumber 转换。`'123' | 0` → `123`，`'abc' | 0` → `0`。

---

## 最佳实践

### ✅ 推荐做法

```javascript
// 1. 明确知道数值范围小，且追求性能
function fastOperation(value) {
  value |= 0  // 快速取整
  // ... 高频操作
}

// 2. 处理用户输入，确保是整数
function setArraySize(size) {
  size |= 0  // 防止小数和字符串
  return new Array(size)
}

// 3. 添加注释说明意图
function process(index) {
  index |= 0  // 确保索引是整数
  return data[index]
}
```

### ❌ 避免的做法

```javascript
// 1. 处理大数（会溢出）
const bigNum = 9999999999
const result = bigNum | 0  // ✗ 错误结果

// 应该用：
const result = Math.floor(bigNum)  // ✓

// 2. 需要向下取整负数
const negative = -3.7
const result = negative | 0  // -3 (可能不是你想要的)

// 如果需要向下取整，应该用：
const result = Math.floor(negative)  // -4 ✓

// 3. 团队不熟悉位运算
const value = someValue | 0  // ✗ 可读性差

// 应该用：
const value = Math.trunc(someValue)  // ✓ 语义清晰
```

---

## 总结

**位运算取整的本质：**
- JavaScript 位运算只能操作 32 位整数
- 引擎自动调用 ToInt32 进行类型转换
- 转换过程中丢弃小数部分（向零取整）

**记忆口诀：**
- `| 0` 快如闪电，整数立现
- 向零取整，小数不见
- 三十二位，范围有限
- 性能优先，可读靠边

**实际应用：**
- 高性能库（如 nanoid）
- 游戏开发和图形处理
- 需要确保整数的场景

*理解位运算的类型转换机制，是深入掌握 JavaScript 的重要一步！* 🚀

