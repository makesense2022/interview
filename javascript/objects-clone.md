# 对象操作与拷贝（≤6 分复习）

- 【17】浅拷贝 vs 深拷贝
  - 难点：循环引用（WeakMap 记忆化）、Symbol 键、不可枚举、原型、访问器属性、Map/Set、RegExp/Date、TypedArray/ArrayBuffer
  - 泄漏与循环引用：是否“可达”才关键，非循环本身
  - 自引用/图结构在状态机、解析树、链表中常见

- 【18】defineProperty vs Proxy
  - defineProperty：对已定义属性可用 getter/setter；新增属性/数组索引变更需手动处理
  - Proxy：可拦截 get/set/in/deleteProperty/ownKeys 等，更全面
