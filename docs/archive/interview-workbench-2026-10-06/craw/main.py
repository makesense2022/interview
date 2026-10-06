#!/usr/bin/env python3
"""
图片爬虫主程序
"""
import asyncio
import argparse
import sys
from pathlib import Path
from datetime import datetime

# 添加src到Python路径
sys.path.insert(0, str(Path(__file__).parent))



def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='智能图片爬虫')
    parser.add_argument('url', help='要爬取的网站URL')
    parser.add_argument('-d', '--depth', type=int, default=2,
                        help='爬取深度 (默认: 2)')
    parser.add_argument('-c', '--concurrent', type=int, default=5,
                        help='最大并发数 (默认: 5)')
    parser.add_argument('-o', '--output', type=str, default=None,
                        help='输出目录 (默认: ./downloads/域名_时间戳)')
    parser.add_argument('--min-width', type=int, default=100,
                        help='最小图片宽度 (默认: 100)')
    parser.add_argument('--min-height', type=int, default=100,
                        help='最小图片高度 (默认: 100)')
    parser.add_argument('--site', type=str, default='default',
                        help='兼容保留参数；当前仅支持 default，站点预设尚未接入')
    parser.add_argument('--timeout', type=int, default=30000,
                        help='页面超时时间，毫秒 (默认: 30000)')
    
    args = parser.parse_args()
    if args.site != 'default':
        parser.error('--site presets are not wired into this entry point; use default and explicit options')
    if args.depth < 0 or args.concurrent < 1 or args.timeout < 1 or args.min_width < 1 or args.min_height < 1:
        parser.error('depth must be >= 0; concurrency, timeout and image dimensions must be positive')
    return args


async def main():
    """主函数"""
    args = parse_arguments()
    try:
        from src.image_crawler import ImageCrawler
    except ModuleNotFoundError as exc:
        print(f"Missing dependency: {exc.name}. Install craw/requirements.txt in a dedicated Python environment.", file=sys.stderr)
        raise SystemExit(2) from None
    
    # 生成输出目录
    if args.output:
        output_dir = args.output
    else:
        from urllib.parse import urlparse
        domain = urlparse(args.url).netloc.replace('.', '_')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_dir = f"./downloads/{domain}_{timestamp}"
    
    print(f"""
╔════════════════════════════════════════╗
║         智能图片爬虫 v1.0.0            ║
╚════════════════════════════════════════╝

配置信息：
- 目标网站: {args.url}
- 爬取深度: {args.depth}
- 并发数: {args.concurrent}
- 输出目录: {output_dir}
- 最小尺寸: {args.min_width}x{args.min_height}
- 网站配置: {args.site}
""")
    
    # 创建爬虫实例
    crawler = ImageCrawler(
        base_url=args.url,
        download_dir=output_dir,
        max_depth=args.depth,
        max_concurrent=args.concurrent,
        min_image_size=(args.min_width, args.min_height),
        timeout=args.timeout
    )
    
    # 开始爬取
    try:
        await crawler.crawl()
        print("\n✅ 爬取完成！")
    except KeyboardInterrupt:
        print("\n⚠️ 用户中断爬取")
    except Exception as e:
        print(f"\n❌ 爬取失败: {str(e)}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
