# 错误处理与健壮性（≤6 分复习）

- 【19】错误捕获
  - 运行时：window.onerror 或 addEventListener('error', …)
  - 资源加载错误：捕获型 error 事件（不冒泡）
  - 未处理拒绝：unhandledrejection（拼写注意）
  - 跨域与 source map：需 crossorigin/服务端 CORS 以获取堆栈

- 【20】生产可观测性
  - Source map 对齐版本并上传（Sentry 等）
  - 采样、脱敏（PII）、错误指纹、去抖与归并
  - 框架集成（React/Vue）、长任务与性能关联上报
