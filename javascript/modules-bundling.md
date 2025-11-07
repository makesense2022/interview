# 模块化与打包（≤6 分复习）

- 【13】ESM vs CJS
  - ESM：静态结构、live binding、可 tree-shaking、加载为异步
  - CJS：运行时加载、单例缓存、导出为对象引用（非深拷贝）
  - 互操作与 default 差异需注意（尤其在 Node）

- 【14】import() 动态加载
  - 返回 Promise；按需/懒加载、代码分割
  - 与动态插入 <script> 不同，受模块解析与依赖图管理
