# 面试与源码学习入口

按实际学习需求维护，保留所有笔记与练习。这里没有统一网站构建或公众统计。

已有主题：[JavaScript](javascript/README.md)、[React](react/README.md)、[浏览器](browser/README.md)、[前端工程](engineering/README.md)、[性能](performance/README.md)、[网络](network/README.md)、[架构](architecture/fe-architecture-answers.md)、[设计模式](design-patterns/README.md)、[系统设计](system-design/README.md)、[算法](algorithms/README.md)。Electron 样例在 `electron/`，本輪未启动桌面应用。

原首页中 TypeScript/Vue/security/nodejs/cross-platform 等指向不存在目录的链接已从主入口移出；它们是待补主题，不伪造空目录。原计划完整保留于 [历史首页](docs/history/README-before-20261001.md)。

一条可执行路径（Node v22.23.2，2026-10-01 复现）：

1. 读 [函数式笔记](javascript/functional.md) 的 curry/partial 与 pipe/compose。
2. 先预测同步/异步执行顺序，再运行 `node javascript/snippets/functional.js`。
3. 核对输出：curry 三次均为 6，占位 curry 为 1-2-3，partial 为 6；pipe/compose 最终均为 49。演示只输出结果，不是完整边界测试套件。
4. 复盘参数透传、this、Promise 化、占位符尚未填满的边界。把自己的答案另存带日期笔记，不覆盖题目。

`javascript/snippets/handwrites.js` 中 promiseAll/LRUCache/EventEmitter/scheduler 当前是待完成骨架，不因文件存在就判定练习已完成。本轮没有代写答案或计入个人掌握程度。

第三方源码边界：`source/zustand`、`source/nanoid`、`source/vueuse` 的源码及 LICENSE 保留，三份许可证文件均标注 MIT。引用/再分发时继续保留对应作者与许可；未开展法律审查。它们的代码规模、上游测试数和功能不计入个人项目成果。本轮没有升级或改写 source/ 下任何内容。

个人进步记录应分开写：阅读了什么、独立实现了什么、经什么输入验证、哪些依赖 AI 提示。现有材料未提供足够连续记录，不能由目录数推算能力增长。

## 旧工作台参考资料

2026-10-06：独立的 interview-workbench 已清理，少量面试模板、图片抓取实验源码和 Git 历史归到 [参考归档](docs/archive/interview-workbench-2026-10-06/README.md)。下载图片和旧日志不作为当前学习资料。
