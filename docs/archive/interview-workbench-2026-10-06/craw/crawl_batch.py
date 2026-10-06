#!/usr/bin/env python3
"""
批量爬取脚本 - 从文件读取URL列表逐个爬取
适合需要爬取多个页面但要避免触发反爬的场景
"""
import asyncio
import argparse
import sys
from pathlib import Path
import time

sys.path.insert(0, str(Path(__file__).parent))
from src.image_crawler import ImageCrawler


def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='批量图片爬虫（从文件读取URL列表）')
    parser.add_argument('urls_file', help='包含URL列表的文件，每行一个URL')
    parser.add_argument('-o', '--output', type=str, default='./downloads/batch',
                        help='输出根目录 (默认: ./downloads/batch)')
    parser.add_argument('--min-width', type=int, default=200,
                        help='最小图片宽度 (默认: 200)')
    parser.add_argument('--min-height', type=int, default=200,
                        help='最小图片高度 (默认: 200)')
    parser.add_argument('--delay', type=int, default=5,
                        help='每个页面之间的延迟（秒），避免触发反爬 (默认: 5)')
    
    return parser.parse_args()


async def crawl_single_url(url: str, output_dir: str, min_size: tuple, index: int):
    """爬取单个URL"""
    page_dir = f"{output_dir}/page_{index:03d}"
    
    print(f"\n{'='*60}")
    print(f"[{index}] 开始爬取: {url}")
    print(f"{'='*60}")
    
    crawler = ImageCrawler(
        base_url=url,
        download_dir=page_dir,
        max_depth=0,  # 只爬当前页
        max_concurrent=1,  # 降低并发
        min_image_size=min_size,
        timeout=60000
    )
    
    try:
        await crawler.crawl()
        return crawler.stats
    except Exception as e:
        print(f"❌ 爬取失败: {str(e)}")
        return None


async def main():
    """主函数"""
    args = parse_arguments()
    
    # 读取URL列表
    urls_file = Path(args.urls_file)
    if not urls_file.exists():
        print(f"❌ 文件不存在: {args.urls_file}")
        print("\n使用方法：")
        print("1. 创建一个文本文件（如 urls.txt）")
        print("2. 每行写一个要爬取的URL")
        print("3. 运行: python3 crawl_batch.py urls.txt")
        return
    
    with open(urls_file, 'r', encoding='utf-8') as f:
        urls = [line.strip() for line in f if line.strip() and not line.startswith('#')]
    
    if not urls:
        print("❌ 文件中没有有效的URL")
        return
    
    print(f"""
╔════════════════════════════════════════╗
║          批量图片爬虫                  ║
╚════════════════════════════════════════╝

配置信息：
- URL数量: {len(urls)}
- 输出目录: {args.output}
- 最小尺寸: {args.min_width}x{args.min_height}
- 页面延迟: {args.delay}秒
""")
    
    # 创建输出目录
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 逐个爬取
    all_stats = []
    for i, url in enumerate(urls, 1):
        stats = await crawl_single_url(
            url, 
            args.output, 
            (args.min_width, args.min_height),
            i
        )
        
        if stats:
            all_stats.append(stats)
        
        # 延迟，避免触发反爬
        if i < len(urls):
            print(f"\n⏳ 等待 {args.delay} 秒后继续...")
            time.sleep(args.delay)
    
    # 打印总体统计
    if all_stats:
        total_pages = sum(s['pages_crawled'] for s in all_stats)
        total_found = sum(s['images_found'] for s in all_stats)
        total_downloaded = sum(s['images_downloaded'] for s in all_stats)
        total_failed = sum(s['images_failed'] for s in all_stats)
        
        print(f"""
\n{'='*60}
总体统计：
{'='*60}
成功爬取页面: {len(all_stats)}/{len(urls)}
发现图片总数: {total_found}
下载成功总数: {total_downloaded}
下载失败总数: {total_failed}
保存目录: {output_dir.absolute()}
{'='*60}
""")


if __name__ == "__main__":
    asyncio.run(main())
