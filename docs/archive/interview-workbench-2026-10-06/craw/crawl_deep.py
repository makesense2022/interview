#!/usr/bin/env python3
"""
深度嵌套爬虫
支持场景：
1. 相册列表页 → 多个相册
2. 相册详情页 → 有分页的缩略图
3. 点击缩略图 → 获取大图
"""
import asyncio
import argparse
import sys
from pathlib import Path
import random

sys.path.insert(0, str(Path(__file__).parent))

from playwright.async_api import async_playwright
import aiohttp
import aiofiles
from datetime import datetime
import hashlib
from urllib.parse import urljoin, urlparse
import logging
import os
from PIL import Image
from io import BytesIO


class DeepImageCrawler:
    """深度嵌套图片爬虫"""
    
    def __init__(self, base_url: str, download_dir: str, min_size: tuple, 
                 delay: int = 2, max_albums: int = 5, max_pages_per_album: int = 5, 
                 concurrent: int = 5):
        self.base_url = base_url
        self.download_dir = Path(download_dir)
        self.download_dir.mkdir(parents=True, exist_ok=True)
        self.min_size = min_size
        self.delay = delay
        self.max_albums = max_albums  # 最多爬取多少个相册
        self.max_pages_per_album = max_pages_per_album  # 每个相册最多爬取多少页
        self.concurrent = concurrent
        
        self.downloaded_images = set()
        self.visited_urls = set()
        self.stats = {
            "albums_found": 0,
            "albums_crawled": 0,
            "pages_crawled": 0,
            "thumbnails_found": 0,
            "large_images_found": 0,
            "images_downloaded": 0,
            "images_failed": 0
        }
        
        # 用户代理池
        self.user_agents = [
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
        ]
        self.current_ua_index = 0
        
        self._setup_logging()
    
    def _setup_logging(self):
        """设置日志"""
        log_dir = Path("./logs")
        log_dir.mkdir(exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(f'./logs/deep_crawler_{datetime.now():%Y%m%d_%H%M%S}.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def _get_next_user_agent(self):
        """获取下一个用户代理"""
        ua = self.user_agents[self.current_ua_index]
        self.current_ua_index = (self.current_ua_index + 1) % len(self.user_agents)
        return ua
    
    async def crawl(self):
        """开始深度爬取"""
        self.logger.info(f"开始深度爬取: {self.base_url}")
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--disable-dev-shm-usage',
                    '--no-sandbox',
                ]
            )
            
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent=self._get_next_user_agent(),
                extra_http_headers={
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                }
            )
            
            try:
                # 第1层：收集相册列表
                self.logger.info("\n" + "="*60)
                self.logger.info("🔍 第1层：收集相册列表")
                self.logger.info("="*60)
                
                page = await context.new_page()
                album_urls = await self._collect_albums(page, self.base_url)
                
                self.stats["albums_found"] = len(album_urls)
                self.logger.info(f"\n✓ 找到 {len(album_urls)} 个相册")
                
                # 第2层：处理每个相册
                for album_index, album_url in enumerate(album_urls[:self.max_albums], 1):
                    self.logger.info(f"\n{'='*60}")
                    self.logger.info(f"📚 处理相册 {album_index}/{min(len(album_urls), self.max_albums)}")
                    self.logger.info(f"{'='*60}")
                    self.logger.info(f"URL: {album_url}")
                    
                    try:
                        await self._process_album(context, album_url, album_index)
                        self.stats["albums_crawled"] += 1
                    except Exception as e:
                        self.logger.error(f"❌ 处理相册 {album_index} 失败: {str(e)}")
                        self.logger.info(f"⏭️  跳过该相册，继续处理下一个...")
                        # 失败后等待更长时间
                        await asyncio.sleep(random.uniform(10, 20))
                        continue
                    
                    # 相册之间延迟
                    if album_index < len(album_urls):
                        await asyncio.sleep(random.uniform(5, 10))
                
            finally:
                await context.close()
                await browser.close()
        
        self._print_stats()
    
    async def _collect_albums(self, page, list_url):
        """收集相册列表"""
        await asyncio.sleep(random.uniform(1, 2))
        await page.goto(list_url, wait_until="domcontentloaded", timeout=30000)
        await page.wait_for_timeout(random.randint(1500, 2500))
        
        # 查找相册链接
        albums = await page.evaluate("""
            () => {
                const results = [];
                
                // 策略1: 查找包含图片的链接（通常是相册）
                document.querySelectorAll('a').forEach(link => {
                    const img = link.querySelector('img');
                    if (img && link.href && !link.href.includes('#')) {
                        // 排除导航链接等
                        const href = link.href;
                        if (href.includes('aid-') || href.includes('album') || 
                            href.includes('photos-index')) {
                            results.push(href);
                        }
                    }
                });
                
                // 去重
                return [...new Set(results)];
            }
        """)
        
        self.logger.info(f"在列表页找到 {len(albums)} 个相册链接")
        return albums
    
    async def _process_album(self, context, album_url, album_index):
        """处理单个相册（包含分页）"""
        page = await context.new_page()
        
        try:
            # 收集该相册的所有分页
            album_pages = await self._collect_album_pages(page, album_url)
            self.logger.info(f"相册有 {len(album_pages)} 个分页")
            
            # 处理每一页
            for page_index, page_url in enumerate(album_pages[:self.max_pages_per_album], 1):
                self.logger.info(f"\n  📄 处理第 {page_index}/{min(len(album_pages), self.max_pages_per_album)} 页")
                
                try:
                    await self._process_album_page(context, page_url, album_index, page_index)
                    self.stats["pages_crawled"] += 1
                except Exception as e:
                    self.logger.error(f"  ❌ 处理第 {page_index} 页失败: {str(e)}")
                    self.logger.info(f"  ⏭️  跳过该页，继续处理下一页...")
                    # 失败后等待更长时间
                    await asyncio.sleep(random.uniform(5, 10))
                    continue
                
                # 页面之间延迟
                if page_index < len(album_pages):
                    await asyncio.sleep(random.uniform(3, 6))
                    
        finally:
            await page.close()
    
    async def _collect_album_pages(self, page, start_url):
        """收集相册的所有分页"""
        all_pages = [start_url]
        current_url = start_url
        
        while len(all_pages) < self.max_pages_per_album:
            if current_url in self.visited_urls:
                break
            
            self.visited_urls.add(current_url)
            
            await asyncio.sleep(random.uniform(0.5, 1.5))
            await page.goto(current_url, wait_until="domcontentloaded", timeout=30000)
            await page.wait_for_timeout(random.randint(1000, 2000))
            
            # 查找下一页
            next_url = await self._find_next_page(page)
            
            if next_url and next_url not in all_pages:
                all_pages.append(next_url)
                current_url = next_url
            else:
                break
        
        return all_pages
    
    async def _process_album_page(self, context, page_url, album_index, page_index):
        """处理相册的单个页面"""
        page = await context.new_page()
        
        try:
            # 增加延迟，避免请求过快
            await asyncio.sleep(random.uniform(2, 4))
            
            # 添加重试机制
            max_retries = 3
            for retry in range(max_retries):
                try:
                    await page.goto(page_url, wait_until="domcontentloaded", timeout=30000)
                    await page.wait_for_timeout(random.randint(2000, 4000))
                    break  # 成功则跳出重试循环
                except Exception as e:
                    if retry < max_retries - 1:
                        wait_time = (retry + 1) * 5  # 递增等待：5秒、10秒、15秒
                        self.logger.warning(f"    ⚠️ 访问失败，{wait_time}秒后重试 ({retry + 1}/{max_retries})")
                        await asyncio.sleep(wait_time)
                    else:
                        raise  # 最后一次重试失败则抛出异常
            
            # 查找缩略图链接
            image_links = await self._find_clickable_images(page)
            self.stats["thumbnails_found"] += len(image_links)
            self.logger.info(f"    找到 {len(image_links)} 个缩略图")
            
            if len(image_links) == 0:
                return
            
            # 并发获取大图URL
            self.logger.info(f"    📥 获取大图URL（并发: {self.concurrent}）")
            large_image_urls = []
            
            semaphore = asyncio.Semaphore(self.concurrent)
            
            async def get_url_with_semaphore(link_info):
                async with semaphore:
                    try:
                        return await self._get_large_image(context, link_info)
                    except:
                        return None
            
            tasks = [get_url_with_semaphore(link) for link in image_links]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            large_image_urls = [url for url in results if url and isinstance(url, str)]
            self.stats["large_images_found"] += len(large_image_urls)
            self.logger.info(f"    ✓ 获取到 {len(large_image_urls)} 个大图URL")
            
            # 并发下载
            if large_image_urls:
                self.logger.info(f"    📥 下载 {len(large_image_urls)} 张大图...")
                
                semaphore = asyncio.Semaphore(self.concurrent)
                
                async def download_with_semaphore(url):
                    async with semaphore:
                        success = await self._download_image(url)
                        if success:
                            self.stats["images_downloaded"] += 1
                        else:
                            self.stats["images_failed"] += 1
                
                tasks = [download_with_semaphore(url) for url in large_image_urls]
                await asyncio.gather(*tasks, return_exceptions=True)
                
                self.logger.info(f"    ✓ 下载完成")
                
        finally:
            await page.close()
    
    async def _find_clickable_images(self, page):
        """查找可点击的图片链接"""
        links = await page.evaluate("""
            () => {
                const results = [];
                
                // 查找 <a> 标签包裹的 <img>
                document.querySelectorAll('a img').forEach(img => {
                    const link = img.closest('a');
                    if (link && link.href && !link.href.includes('#')) {
                        results.push({
                            type: 'link',
                            href: link.href,
                            thumb: img.src
                        });
                    }
                });
                
                // 去重
                const seen = new Set();
                return results.filter(item => {
                    const key = item.href;
                    if (seen.has(key)) return false;
                    seen.add(key);
                    return true;
                });
            }
        """)
        
        return links
    
    async def _get_large_image(self, context, link_info):
        """获取大图URL"""
        try:
            page = await context.new_page()
            
            if link_info['type'] == 'link':
                target_url = link_info['href']
                
                await page.goto(target_url, wait_until="domcontentloaded", timeout=30000)
                await page.wait_for_timeout(1000)
                
                # 查找大图
                large_image_url = await page.evaluate("""
                    () => {
                        let largestImg = null;
                        let maxSize = 0;
                        
                        document.querySelectorAll('img').forEach(img => {
                            const width = img.naturalWidth || img.width;
                            const height = img.naturalHeight || img.height;
                            const size = width * height;
                            
                            if (size > maxSize) {
                                maxSize = size;
                                largestImg = img;
                            }
                        });
                        
                        if (largestImg) {
                            return largestImg.src || largestImg.dataset.src;
                        }
                        
                        return null;
                    }
                """)
                
                await page.close()
                
                if large_image_url:
                    return urljoin(target_url, large_image_url)
            
            return None
            
        except Exception as e:
            try:
                await page.close()
            except:
                pass
            return None
    
    async def _find_next_page(self, page):
        """查找下一页链接"""
        try:
            next_url = await page.evaluate("""
                () => {
                    const nextTexts = ['下一页', 'next', 'Next', '>', '»'];
                    const nextSelectors = [
                        'a.next', 'a[rel="next"]', '.pagination a.next',
                        '.pagination .next', '.page-next'
                    ];
                    
                    // 通过选择器查找
                    for (const selector of nextSelectors) {
                        const link = document.querySelector(selector);
                        if (link && link.href) return link.href;
                    }
                    
                    // 通过文字查找
                    const allLinks = Array.from(document.querySelectorAll('a'));
                    for (const link of allLinks) {
                        const text = link.textContent.trim();
                        for (const nextText of nextTexts) {
                            if (text === nextText || text.includes(nextText)) {
                                if (link.href) return link.href;
                            }
                        }
                    }
                    
                    return null;
                }
            """)
            
            if next_url and next_url != page.url:
                return urljoin(page.url, next_url)
            
            return None
        except:
            return None
    
    async def _download_image(self, img_url: str) -> bool:
        """下载图片"""
        if img_url in self.downloaded_images:
            return True
        
        # 过滤 webp
        if img_url.lower().endswith('.webp') or '.webp' in img_url.lower():
            return False
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(img_url, timeout=aiohttp.ClientTimeout(total=30)) as response:
                    if response.status == 200:
                        content = await response.read()
                        
                        # 验证完整性
                        if not self._validate_image(content):
                            return False
                        
                        # 检查尺寸
                        if not self._check_image_size(content):
                            return False
                        
                        # 保存
                        filename = self._generate_filename(img_url, content)
                        filepath = self.download_dir / filename
                        
                        async with aiofiles.open(filepath, 'wb') as f:
                            await f.write(content)
                        
                        if not self._verify_saved_file(filepath):
                            try:
                                filepath.unlink()
                            except:
                                pass
                            return False
                        
                        self.downloaded_images.add(img_url)
                        self.logger.info(f"      ✅ {filename}")
                        return True
                        
        except Exception as e:
            return False
        
        return False
    
    def _validate_image(self, content: bytes) -> bool:
        """验证图片"""
        try:
            if not content or len(content) < 100:
                return False
            img = Image.open(BytesIO(content))
            if img.format and img.format.lower() == 'webp':
                return False
            img.verify()
            return True
        except:
            return False
    
    def _verify_saved_file(self, filepath: Path) -> bool:
        """验证保存的文件"""
        try:
            with Image.open(filepath) as img:
                if img.format and img.format.lower() == 'webp':
                    return False
                img.load()
                return True
        except:
            return False
    
    def _check_image_size(self, content: bytes) -> bool:
        """检查图片尺寸"""
        try:
            img = Image.open(BytesIO(content))
            width, height = img.size
            return width >= self.min_size[0] and height >= self.min_size[1]
        except:
            return True
    
    def _generate_filename(self, url: str, content: bytes) -> str:
        """生成文件名"""
        parsed = urlparse(url)
        ext = os.path.splitext(parsed.path)[1].lower()
        
        if not ext or ext not in {'.jpg', '.jpeg', '.png', '.gif', '.bmp'}:
            try:
                img = Image.open(BytesIO(content))
                format_lower = img.format.lower() if img.format else 'jpg'
                if format_lower == 'webp':
                    format_lower = 'jpg'
                ext = f'.{format_lower}'
            except:
                ext = '.jpg'
        
        hash_digest = hashlib.md5(content).hexdigest()[:16]
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')[:19]
        domain = urlparse(self.base_url).netloc.replace('.', '_')
        
        return f"{domain}_{timestamp}_{hash_digest}{ext}"
    
    def _print_stats(self):
        """打印统计信息"""
        print("\n" + "="*60)
        print("深度爬取完成！统计信息：")
        print("="*60)
        print(f"发现相册数: {self.stats['albums_found']}")
        print(f"爬取相册数: {self.stats['albums_crawled']}")
        print(f"爬取页数: {self.stats['pages_crawled']}")
        print(f"发现缩略图数: {self.stats['thumbnails_found']}")
        print(f"找到大图数: {self.stats['large_images_found']}")
        print(f"下载成功数: {self.stats['images_downloaded']}")
        print(f"下载失败数: {self.stats['images_failed']}")
        print(f"下载目录: {self.download_dir.absolute()}")
        print("="*60)


def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='深度嵌套图片爬虫（列表→相册→分页→大图）')
    parser.add_argument('url', help='相册列表页URL')
    parser.add_argument('-o', '--output', type=str, default=None, help='输出目录')
    parser.add_argument('--min-width', type=int, default=500, help='最小图片宽度 (默认: 500)')
    parser.add_argument('--min-height', type=int, default=500, help='最小图片高度 (默认: 500)')
    parser.add_argument('--delay', type=int, default=2, help='延迟（秒） (默认: 2)')
    parser.add_argument('--max-albums', type=int, default=5, help='最多爬取相册数 (默认: 5)')
    parser.add_argument('--max-pages', type=int, default=5, help='每个相册最多爬取页数 (默认: 5)')
    parser.add_argument('-c', '--concurrent', type=int, default=5, help='并发数 (默认: 5)')
    
    return parser.parse_args()


async def main():
    """主函数"""
    args = parse_arguments()
    
    # 生成输出目录
    if args.output:
        output_dir = args.output
    else:
        domain = urlparse(args.url).netloc.replace('.', '_')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_dir = f"./downloads/{domain}_{timestamp}_deep"
    
    print(f"""
╔════════════════════════════════════════╗
║     深度嵌套爬虫 v1.0              ║
╚════════════════════════════════════════╝

配置信息：
- 目标网站: {args.url}
- 输出目录: {output_dir}
- 最小尺寸: {args.min_width}x{args.min_height}
- 延迟: {args.delay}秒
- 最多相册: {args.max_albums}个
- 每相册页数: {args.max_pages}页
- 并发数: {args.concurrent}个
- 工作模式: 列表页 → 相册 → 分页 → 大图

开始工作...
""")
    
    crawler = DeepImageCrawler(
        base_url=args.url,
        download_dir=output_dir,
        min_size=(args.min_width, args.min_height),
        delay=args.delay,
        max_albums=args.max_albums,
        max_pages_per_album=args.max_pages,
        concurrent=args.concurrent
    )
    
    try:
        await crawler.crawl()
        print("\n✅ 所有图片处理完成！")
    except KeyboardInterrupt:
        print("\n⚠️ 用户中断")
    except Exception as e:
        print(f"\n❌ 爬取失败: {str(e)}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
