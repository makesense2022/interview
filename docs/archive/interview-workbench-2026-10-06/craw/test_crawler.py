#!/usr/bin/env python3
"""
爬虫测试脚本 - 使用免费图片网站测试
"""
import asyncio
import sys
from pathlib import Path

# 添加src到Python路径
sys.path.insert(0, str(Path(__file__).parent))

from src.image_crawler import ImageCrawler


async def test_crawler():
    """测试爬虫功能"""
    # 使用Unsplash的公开页面进行测试
    test_url = "https://unsplash.com/s/photos/test"
    
    print("=" * 60)
    print("图片爬虫测试")
    print("=" * 60)
    print(f"测试URL: {test_url}")
    print("注意: 首次运行需要下载Chromium浏览器")
    print("-" * 60)
    
    # 创建爬虫实例（使用较小的配置进行测试）
    crawler = ImageCrawler(
        base_url=test_url,
        download_dir="./downloads/test",
        max_depth=0,  # 只爬取当前页面
        max_concurrent=2,
        min_image_size=(200, 200),
        timeout=30000
    )
    
    try:
        # 开始爬取
        await crawler.crawl()
        
        # 检查结果
        if crawler.stats['images_downloaded'] > 0:
            print("\n✅ 测试成功！")
            print(f"成功下载 {crawler.stats['images_downloaded']} 张图片")
            print(f"图片保存在: {Path(crawler.download_dir).absolute()}")
        else:
            print("\n⚠️ 未能下载图片，请检查网络连接或目标网站")
            
    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")
        print("\n可能的解决方案:")
        print("1. 运行: pip install -r requirements.txt")
        print("2. 运行: playwright install chromium")
        print("3. 检查网络连接")
        raise


if __name__ == "__main__":
    print("""
请确保已完成以下步骤：
1. pip install -r requirements.txt
2. playwright install chromium

按Enter继续，或Ctrl+C退出...
    """)
    
    input()
    
    # 运行测试
    asyncio.run(test_crawler())
