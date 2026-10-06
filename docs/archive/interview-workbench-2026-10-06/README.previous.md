# 面试材料与图片抓取实验存档

2026-09-30 本地清点：`project1.md` 为小程序架构面试陈述框架；`craw/` 是独立 Python 图片抓取实验，二者不是一款已部署产品。保存全部源码、原始说明与 Git，不继续建设展示平台，不接公众网站埋点。

## 材料与入口

- [面试陈述框架](project1.md)：包含 STAR、白板图、取舍与追问。其中百分比和收益是讲述模板，未经个人项目证据核实不能当实际履历。
- [抓取工具原说明](craw/README.md)：保留原始功能说明供追溯；描述不等同本次网络验证。
- `craw/main.py`：URL、depth、concurrent、output、min-width/min-height、timeout；`--help` 可离线读取。
- `craw/crawl_single_page.py`：单页入口；`crawl_batch.py`：URL 文件批量入口；`crawl_with_clicks.py` 与 `crawl_deep.py` 是较重的实验。此次均未启动抓取。
- `craw/config/config.py` 有站点预设，但现有 main 并未应用这些配置。`--site` 非 default 现在明确拒绝，避免“看似启用而没有效果”。

当前只核对代码与参数帮助；没有取得图片再使用许可，也没有验证目标站点、登录、反爬或限流处理。原 README 写 MIT，但仓库没有独立 LICENSE 文件；不把第三方网站或图片许可解释成 MIT。

## 按需恢复

在明确目标页面与用途后进入 `craw`，为该次实验使用独立虚拟环境，依赖列表是 `requirements.txt`（不是 pnpm）。先运行 `python main.py --help`，再检查 Python 包与 Playwright Chromium 是否可用。安装或运行抓取不属于本次保存任务，未执行。

如需要抓取，先使用已有授权页面、小范围参数和独立输出目录，不覆盖旧下载。失败时区分依赖缺失、浏览器缺失、页面超时、HTTP 限流和权限拒绝；不要把下载失败写成没有图片，也不要据此扩大并发或绕过访问限制。后续只有实际需要复用抓取结果时维护这一工具。

保留：`project1.md`、全部 `craw/*.py`、核心实现与配置、依赖版本、原始说明，以及既有下载/日志（如果存在）。本轮未删除、重命名或公开任何材料。
