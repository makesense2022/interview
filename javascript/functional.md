# 函数式与技巧（≤6 分复习）

- 【15】柯里化 vs 偏函数
  - 柯里化：f(a,b,c) → f(a)(b)(c)
  - 偏函数：预置部分参数，仍一次调用，如 bind 的参数预置
  - 注意实现中的 this/参数透传与边界

- 【23】compose/pipe
  - compose 从右到左，pipe 从左到右
  - 需返回 reduce 结果；异步场景需把累积值 Promise 化
