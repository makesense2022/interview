#!/usr/bin/env python3
"""
图片爬虫使用示例
"""
import asyncio
import sys
from pathlib import Path

# 添加src到Python路径
sys.path.insert(0, str(Path(__file__).parent))

from src.image_crawler import ImageCrawler


async def example_basic():
    """基础使用示例"""
    print("=" * 50)
    print("示例1: 基础爬取")
    print("=" * 50)
    
    crawler = ImageCrawler(
        base_url="https://unsplash.com/s/photos/nature",
        download_dir="./downloads/unsplash_basic",
        max_depth=1,
        max_concurrent=3
    )
    
    await crawler.crawl()


async def example_high_quality():
    """爬取高质量图片示例"""
    print("=" * 50)
    print("示例2: 高质量图片爬取")
    print("=" * 50)
    
    crawler = ImageCrawler(
        base_url="https://www.pexels.com/search/landscape/",
        download_dir="./downloads/pexels_hq",
        max_depth=2,
        max_concurrent=5,
        min_image_size=(1920, 1080),  # 只下载高清图片
        timeout=60000  # 延长超时时间
    )
    
    await crawler.crawl()


async def example_deep_crawl():
    """深度爬取示例"""
    print("=" * 50)
    print("示例3: 深度爬取")
    print("=" * 50)
    
    crawler = ImageCrawler(
        base_url="https://www.example-photography.com",
        download_dir="./downloads/deep_crawl",
        max_depth=3,  # 爬取3层深度
        max_concurrent=3,
        min_image_size=(500, 500)
    )
    
    await crawler.crawl()


async def example_custom_filter():
    """自定义过滤条件示例"""
    print("=" * 50)
    print("示例4: 自定义爬取")
    print("=" * 50)
    
    # 创建自定义爬虫类
    class CustomImageCrawler(ImageCrawler):
        def _is_image_url(self, url: str) -> bool:
            """重写方法，只接受特定格式的图片"""
            # 只接受 jpg 和 png
            return url.lower().endswith(('.jpg', '.jpeg', '.png'))
    
    crawler = CustomImageCrawler(
        base_url="https://example.com",
        download_dir="./downloads/custom",
        max_depth=1,
        max_concurrent=5
    )
    
    await crawler.crawl()


async def example_batch_sites():
    """批量爬取多个网站示例"""
    print("=" * 50)
    print("示例5: 批量爬取多个网站")
    print("=" * 50)
    
    sites = [
        "https://unsplash.com/s/photos/city",
        "https://unsplash.com/s/photos/mountain",
        "https://unsplash.com/s/photos/ocean",
    ]
    
    tasks = []
    for i, site in enumerate(sites, 1):
        crawler = ImageCrawler(
            base_url=site,
            download_dir=f"./downloads/batch_{i}",
            max_depth=1,
            max_concurrent=2
        )
        tasks.append(crawler.crawl())
    
    # 并发爬取所有网站
    await asyncio.gather(*tasks)


async def example_with_stats():
    """带统计信息的爬取示例"""
    print("=" * 50)
    print("示例6: 详细统计信息")
    print("=" * 50)
    
    crawler = ImageCrawler(
        base_url="https://example.com/gallery",
        download_dir="./downloads/with_stats",
        max_depth=2,
        max_concurrent=5
    )
    
    # 爬取
    await crawler.crawl()
    
    # 打印详细统计
    stats = crawler.stats
    print("\n详细统计信息:")
    print(f"  - 爬取页面数: {stats['pages_crawled']}")
    print(f"  - 发现图片数: {stats['images_found']}")
    print(f"  - 成功下载数: {stats['images_downloaded']}")
    print(f"  - 失败数量: {stats['images_failed']}")
    
    if stats['start_time'] and stats['end_time']:
        duration = (stats['end_time'] - stats['start_time']).total_seconds()
        print(f"  - 总用时: {duration:.2f} 秒")
        if stats['images_downloaded'] > 0:
            speed = stats['images_downloaded'] / duration
            print(f"  - 下载速度: {speed:.2f} 张/秒")


def main():
    """主函数"""
    print("""
╔════════════════════════════════════════╗
║      图片爬虫使用示例集合              ║
╚════════════════════════════════════════╝
    
选择要运行的示例:
1. 基础爬取
2. 高质量图片爬取
3. 深度爬取
4. 自定义过滤条件
5. 批量爬取多个网站
6. 带详细统计信息
0. 退出
    """)
    
    while True:
        try:
            choice = input("\n请输入选项 (0-6): ").strip()
            
            if choice == '0':
                print("退出程序")
                break
            elif choice == '1':
                asyncio.run(example_basic())
            elif choice == '2':
                asyncio.run(example_high_quality())
            elif choice == '3':
                asyncio.run(example_deep_crawl())
            elif choice == '4':
                asyncio.run(example_custom_filter())
            elif choice == '5':
                asyncio.run(example_batch_sites())
            elif choice == '6':
                asyncio.run(example_with_stats())
            else:
                print("无效选项，请重新输入")
                
        except KeyboardInterrupt:
            print("\n用户中断")
            break
        except Exception as e:
            print(f"发生错误: {str(e)}")
            
    print("\n示例程序结束")


if __name__ == "__main__":
    main()
