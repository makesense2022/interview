# 事件循环与异步（≤6 分复习）

- 【10】宏任务/微任务顺序
  - 执行一个宏任务 → 清空微任务队列 → 下一宏任务
  - 初始 script 也是一个宏任务；每个宏任务结束都会先清微任务
  - Node：process.nextTick > Promise 微任务；setImmediate 与 setTimeout 时序差异

- 【11】Promise 组合器
  - all：全成一成；一拒全拒；保持输入顺序
  - allSettled：永不 reject，返回每项状态
  - race：首个 settled（成或拒）
  - any：首个 fulfilled；全拒抛 AggregateError
