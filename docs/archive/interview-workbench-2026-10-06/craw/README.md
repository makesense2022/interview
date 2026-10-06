# 🖼️ 智能图片爬虫 (Smart Image Crawler)

一个功能强大的 Python 图片爬虫，支持深度爬取、原图识别和反爬虫处理。

## ✨ 核心特性

- **🔍 智能原图识别**: 自动检测并下载原图而非缩略图
- **🌊 深度爬取**: 可配置的多层级页面爬取
- **🛡️ 反爬虫处理**: 使用 Playwright 无头浏览器绕过反爬机制
- **⚡ 并发下载**: 支持多线程并发下载，提高效率
- **📊 尺寸过滤**: 自动过滤小尺寸图片
- **📈 详细统计**: 实时显示爬取进度和统计信息
- **🔧 灵活配置**: 支持自定义配置和预设网站配置

## 📋 系统要求

- Python 3.8+
- 操作系统: Windows/macOS/Linux

## 🚀 快速开始

### 1. 安装依赖

使用 pip 安装：
```bash
cd craw
pip install -r requirements.txt
```

推荐使用 pnpm 管理 Python 环境（如果已安装）：
```bash
pnpm install  # 如果配置了 pnpm 的 Python 支持
```

### 2. 安装 Playwright 浏览器

```bash
playwright install chromium
```

### 3. 基本使用

```bash
# 爬取网站图片（基本用法）
python main.py https://example.com

# 指定爬取深度
python main.py https://example.com -d 3

# 指定输出目录
python main.py https://example.com -o ./my_images

# 设置最小图片尺寸
python main.py https://example.com --min-width 500 --min-height 500

# 使用预设配置
python main.py https://unsplash.com --site unsplash
```

## 📝 命令行参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `url` | 要爬取的网站URL | 必需 |
| `-d, --depth` | 爬取深度 | 2 |
| `-c, --concurrent` | 最大并发数 | 5 |
| `-o, --output` | 输出目录 | ./downloads/域名_时间戳 |
| `--min-width` | 最小图片宽度 | 100 |
| `--min-height` | 最小图片高度 | 100 |
| `--site` | 使用预设的网站配置 | default |
| `--timeout` | 页面超时时间(毫秒) | 30000 |

## 🐍 Python API 使用

```python
import asyncio
from src.image_crawler import ImageCrawler

async def crawl_images():
    # 创建爬虫实例
    crawler = ImageCrawler(
        base_url="https://example.com",
        download_dir="./downloads",
        max_depth=2,
        max_concurrent=5,
        min_image_size=(200, 200)
    )
    
    # 开始爬取
    await crawler.crawl()

# 运行爬虫
asyncio.run(crawl_images())
```

## 📂 项目结构

```
craw/
├── src/
│   ├── __init__.py
│   └── image_crawler.py      # 核心爬虫类
├── config/
│   └── config.py             # 配置文件
├── downloads/                # 默认下载目录
├── logs/                     # 日志目录
├── main.py                   # 主程序入口
├── requirements.txt          # 依赖列表
├── examples.py              # 使用示例
└── README.md                # 本文档
```

## 🎯 使用示例

### 示例 1: 爬取 Unsplash 高清图片

```bash
python main.py https://unsplash.com/s/photos/nature \
    --depth 2 \
    --min-width 1920 \
    --min-height 1080 \
    --site unsplash
```

### 示例 2: 爬取特定页面的所有图片

```bash
python main.py https://example.com/gallery \
    --depth 0 \
    --concurrent 10 \
    -o ./gallery_images
```

### 示例 3: 深度爬取整个网站

```bash
python main.py https://photography-site.com \
    --depth 5 \
    --concurrent 3 \
    --min-width 800
```

## ⚙️ 高级配置

### 自定义网站配置

编辑 `config/config.py` 添加新的网站配置：

```python
SITE_CONFIGS = {
    "my_site": {
        "max_depth": 3,
        "wait_after_load": 5000,  # 等待5秒
        "min_image_width": 1000,
        "min_image_height": 1000,
    }
}
```

### 处理需要登录的网站

对于需要登录的网站，可以：

1. 使用浏览器的非无头模式手动登录
2. 保存登录状态供后续使用
3. 通过代码自动化登录流程

## 🔍 工作原理

1. **页面加载**: 使用 Playwright 加载目标页面
2. **图片识别**: 扫描所有 `<img>` 标签和 CSS 背景图
3. **原图检测**: 检查图片是否可点击，尝试获取原图链接
4. **深度爬取**: 根据配置递归爬取子页面
5. **并发下载**: 使用 asyncio 并发下载图片
6. **去重处理**: 基于内容哈希避免重复下载

## 📊 输出说明

爬取完成后，会在下载目录生成：

- **图片文件**: 格式为 `域名_时间戳_哈希值.扩展名`
- **stats.json**: 包含爬取统计信息
- **日志文件**: 在 `logs/` 目录下，记录详细爬取过程

## ⚠️ 注意事项

1. **遵守 robots.txt**: 请遵守网站的爬虫协议
2. **控制爬取频率**: 避免对目标网站造成过大压力
3. **版权问题**: 下载的图片可能受版权保护，请合理使用
4. **资源消耗**: 深度爬取可能消耗大量带宽和存储空间

## 🐛 故障排除

### 问题: Playwright 浏览器未安装
```bash
playwright install chromium
```

### 问题: 爬取速度慢
- 增加并发数: `--concurrent 10`
- 减少等待时间: 修改配置文件中的 `wait_after_load`

### 问题: 内存占用过高
- 减少并发数
- 限制爬取深度
- 分批次爬取

## 📄 许可证

MIT License

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📧 联系方式

如有问题，请提交 Issue 或联系开发者。

---

**免责声明**: 本工具仅供学习和研究使用，使用者需自行承担使用风险。
