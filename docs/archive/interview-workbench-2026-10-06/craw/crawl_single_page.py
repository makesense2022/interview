#!/usr/bin/env python3
"""
单页爬取脚本 - 针对有反爬虫的网站
只爬取指定页面，不进行深度爬取
"""
import asyncio
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from src.image_crawler import ImageCrawler


def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='单页图片爬虫（适合反爬网站）')
    parser.add_argument('url', help='要爬取的网站URL')
    parser.add_argument('-o', '--output', type=str, default=None,
                        help='输出目录')
    parser.add_argument('--min-width', type=int, default=200,
                        help='最小图片宽度 (默认: 200)')
    parser.add_argument('--min-height', type=int, default=200,
                        help='最小图片高度 (默认: 200)')
    parser.add_argument('--timeout', type=int, default=60000,
                        help='页面超时时间，毫秒 (默认: 60000)')
    parser.add_argument('--wait', type=int, default=5000,
                        help='页面加载后等待时间，毫秒 (默认: 5000)')
    
    return parser.parse_args()


async def main():
    """主函数"""
    args = parse_arguments()
    
    # 生成输出目录
    if args.output:
        output_dir = args.output
    else:
        from urllib.parse import urlparse
        from datetime import datetime
        domain = urlparse(args.url).netloc.replace('.', '_')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_dir = f"./downloads/{domain}_{timestamp}_single"
    
    print(f"""
╔════════════════════════════════════════╗
║      单页图片爬虫（反爬优化）          ║
╚════════════════════════════════════════╝

配置信息：
- 目标网站: {args.url}
- 爬取深度: 0 (仅当前页)
- 并发数: 1 (避免触发反爬)
- 输出目录: {output_dir}
- 最小尺寸: {args.min_width}x{args.min_height}
- 超时时间: {args.timeout}ms
- 等待时间: {args.wait}ms
""")
    
    # 创建爬虫实例 - 使用保守配置
    crawler = ImageCrawler(
        base_url=args.url,
        download_dir=output_dir,
        max_depth=0,  # 只爬当前页
        max_concurrent=1,  # 降低并发避免触发反爬
        min_image_size=(args.min_width, args.min_height),
        timeout=args.timeout
    )
    
    # 开始爬取
    try:
        await crawler.crawl()
        print("\n✅ 爬取完成！")
        
        if crawler.stats['images_downloaded'] == 0:
            print("\n⚠️ 提示：")
            print("- 如果没有下载到图片，可能是最小尺寸设置太高")
            print("- 尝试降低尺寸要求：--min-width 100 --min-height 100")
            print("- 或者该页面确实没有符合条件的图片")
            
    except KeyboardInterrupt:
        print("\n⚠️ 用户中断爬取")
    except Exception as e:
        print(f"\n❌ 爬取失败: {str(e)}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
