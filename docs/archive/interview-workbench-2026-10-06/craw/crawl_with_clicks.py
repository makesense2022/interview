#!/usr/bin/env python3
"""
点击图片获取大图爬虫
专门处理：页面上的图片是缩略图，点击后才能看到大图的场景
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


class ClickImageCrawler:
    """点击图片获取大图的爬虫"""
    
    def __init__(self, base_url: str, download_dir: str, min_size: tuple, delay: int = 2, max_pages: int = 10, concurrent: int = 5, use_proxy: bool = False):
        self.base_url = base_url
        self.download_dir = Path(download_dir)
        self.download_dir.mkdir(parents=True, exist_ok=True)
        self.min_size = min_size
        self.delay = delay  # 每次点击之间的延迟（秒）
        self.max_pages = max_pages  # 最大翻页数
        self.concurrent = concurrent  # 并发下载数
        self.use_proxy = use_proxy  # 是否使用代理
        
        self.downloaded_images = set()
        self.visited_pages = set()  # 记录已访问的页面URL
        self.stats = {
            "pages_crawled": 0,
            "thumbnails_found": 0,
            "large_images_found": 0,
            "images_downloaded": 0,
            "images_failed": 0
        }
        
        # 用户代理池（轮换使用）
        self.user_agents = [
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        ]
        self.current_ua_index = 0
        
        # 设置日志
        self._setup_logging()
        
    def _setup_logging(self):
        """设置日志"""
        log_dir = Path("./logs")
        log_dir.mkdir(exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(f'./logs/click_crawler_{datetime.now():%Y%m%d_%H%M%S}.log'),
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
        """开始爬取（先收集所有分页，再并发处理）"""
        self.logger.info(f"开始爬取: {self.base_url}")
        
        async with async_playwright() as p:
            # 添加更多反检测参数
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--disable-dev-shm-usage',
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-web-security',
                ]
            )
            
            # 设置更真实的浏览器环境，使用轮换的UA
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent=self._get_next_user_agent(),
                extra_http_headers={
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'DNT': '1',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1',
                }
            )
            
            try:
                # 第一阶段：收集所有分页URL
                self.logger.info("\n" + "="*60)
                self.logger.info("🔍 第一阶段：收集所有分页URL")
                self.logger.info("="*60)
                
                page = await context.new_page()
                all_page_urls = await self._collect_all_pages(page, self.base_url)
                
                self.logger.info(f"\n✓ 找到 {len(all_page_urls)} 个分页")
                for i, url in enumerate(all_page_urls, 1):
                    self.logger.info(f"  [{i}] {url}")
                
                # 第二阶段：并发处理所有页面
                self.logger.info("\n" + "="*60)
                self.logger.info("📥 第二阶段：并发处理所有页面")
                self.logger.info("="*60)
                
                # 使用信号量控制页面并发数（避免打开太多浏览器标签）
                page_semaphore = asyncio.Semaphore(min(3, self.concurrent))  # 最多3个页面同时处理
                
                async def process_page_with_semaphore(page_index, page_url):
                    async with page_semaphore:
                        await self._process_single_page(context, page_index, page_url)
                
                # 并发处理所有页面
                page_tasks = [
                    process_page_with_semaphore(i+1, url) 
                    for i, url in enumerate(all_page_urls)
                ]
                await asyncio.gather(*page_tasks, return_exceptions=True)
                
            finally:
                await context.close()
                await browser.close()
                
        self._print_stats()
    
    async def _collect_all_pages(self, page, start_url):
        """收集所有分页URL"""
        all_pages = [start_url]
        current_url = start_url
        
        self.logger.info(f"开始收集分页...")
        
        while len(all_pages) < self.max_pages:
            # 检查是否已访问过
            if current_url in self.visited_pages:
                self.logger.info("检测到重复页面，停止收集")
                break
            
            self.visited_pages.add(current_url)
            
            # 访问页面，添加随机延迟
            await asyncio.sleep(random.uniform(1, 3))  # 随机延迟1-3秒
            await page.goto(current_url, wait_until="domcontentloaded", timeout=30000)
            await page.wait_for_timeout(random.randint(1500, 3000))  # 随机等待
            
            # 查找下一页链接
            next_page_url = await self._find_next_page(page)
            
            if next_page_url and next_page_url not in all_pages:
                all_pages.append(next_page_url)
                self.logger.info(f"  发现第 {len(all_pages)} 页: {next_page_url}")
                current_url = next_page_url
                await asyncio.sleep(0.5)  # 短暂延迟
            else:
                self.logger.info("没有更多分页了")
                break
        
        return all_pages
    
    async def _process_single_page(self, context, page_index, page_url):
        """处理单个页面的所有图片"""
        try:
            self.logger.info(f"\n{'='*60}")
            self.logger.info(f"📄 处理第 {page_index} 页")
            self.logger.info(f"{'='*60}")
            self.logger.info(f"URL: {page_url}")
            
            # 创建新页面
            page = await context.new_page()
            
            try:
                # 访问页面，添加随机延迟
                await asyncio.sleep(random.uniform(0.5, 2))
                await page.goto(page_url, wait_until="domcontentloaded", timeout=30000)
                await page.wait_for_timeout(random.randint(1000, 2000))
                
                # 查找所有可点击的图片链接
                image_links = await self._find_clickable_images(page)
                page_images = len(image_links)
                self.stats["thumbnails_found"] += page_images
                self.logger.info(f"找到 {page_images} 个可点击的图片链接")
                
                if page_images == 0:
                    return
                
                # 第一步：并发获取所有大图URL
                self.logger.info(f"\n📥 步骤1：并发获取大图URL（并发数: {self.concurrent}）")
                print(f"    [{page_index}] 进度: 0/{page_images} (0%)", end='\r')
                
                completed = 0
                url_semaphore = asyncio.Semaphore(self.concurrent)
                
                async def get_url_with_semaphore(index, link_info):
                    nonlocal completed
                    async with url_semaphore:
                        try:
                            large_image_url = await self._get_large_image(context, link_info)
                            
                            completed += 1
                            percent = int(completed / page_images * 100)
                            print(f"    [{page_index}] 进度: {completed}/{page_images} ({percent}%)", end='\r')
                            
                            return large_image_url if large_image_url else None
                        except Exception as e:
                            completed += 1
                            percent = int(completed / page_images * 100)
                            print(f"    [{page_index}] 进度: {completed}/{page_images} ({percent}%)", end='\r')
                            return None
                
                # 并发获取所有URL
                url_tasks = [get_url_with_semaphore(i+1, link) for i, link in enumerate(image_links)]
                results = await asyncio.gather(*url_tasks, return_exceptions=True)
                
                # 过滤有效的URL
                large_image_urls = [url for url in results if url and isinstance(url, str)]
                self.stats["large_images_found"] += len(large_image_urls)
                print()  # 换行
                self.logger.info(f"✓ 获取到 {len(large_image_urls)}/{page_images} 个大图URL")
                
                # 第二步：并发下载所有大图
                if large_image_urls:
                    self.logger.info(f"\n📥 步骤2：并发下载 {len(large_image_urls)} 张大图...")
                    
                    semaphore = asyncio.Semaphore(self.concurrent)
                    
                    async def download_with_semaphore(url):
                        async with semaphore:
                            success = await self._download_image(url)
                            if success:
                                self.stats["images_downloaded"] += 1
                            else:
                                self.stats["images_failed"] += 1
                    
                    download_tasks = [download_with_semaphore(url) for url in large_image_urls]
                    await asyncio.gather(*download_tasks, return_exceptions=True)
                    
                    self.logger.info(f"✓ 第 {page_index} 页下载完成")
                else:
                    self.logger.warning(f"第 {page_index} 页没有找到可下载的大图")
                    
            finally:
                await page.close()
                
            self.stats["pages_crawled"] += 1
            
        except Exception as e:
            self.logger.error(f"处理第 {page_index} 页失败: {str(e)}")
        
    async def _find_clickable_images(self, page):
        """查找所有可点击的图片链接"""
        # 查找所有包含图片的链接
        links = await page.evaluate("""
            () => {
                const results = [];
                
                // 方法1: 查找 <a> 标签包裹的 <img>
                document.querySelectorAll('a img').forEach(img => {
                    const link = img.closest('a');
                    if (link && link.href) {
                        results.push({
                            type: 'link',
                            href: link.href,
                            thumb: img.src,
                            alt: img.alt || ''
                        });
                    }
                });
                
                // 方法2: 查找有 onclick 的图片
                document.querySelectorAll('img[onclick]').forEach(img => {
                    results.push({
                        type: 'onclick',
                        thumb: img.src,
                        alt: img.alt || '',
                        onclick: img.getAttribute('onclick')
                    });
                });
                
                // 去重
                const seen = new Set();
                return results.filter(item => {
                    const key = item.href || item.thumb;
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
            # 创建新页面
            page = await context.new_page()
            
            if link_info['type'] == 'link':
                # 访问链接
                target_url = link_info['href']
                
                # 使用 domcontentloaded 而不是 networkidle，更快
                await page.goto(target_url, wait_until="domcontentloaded", timeout=30000)
                await page.wait_for_timeout(1000)  # 减少等待时间
                
                # 在新页面中查找大图
                large_image_url = await page.evaluate("""
                    () => {
                        // 策略1: 查找最大的图片
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
                            return largestImg.src || largestImg.dataset.src || largestImg.dataset.original;
                        }
                        
                        // 策略2: 查找特定类名或ID的图片
                        const selectors = [
                            '#picarea img',  // 常见的图片区域ID
                            '.pic_box img',
                            '.image-container img',
                            '.photo img',
                            '[id*="pic"] img',
                            '[class*="image"] img'
                        ];
                        
                        for (const selector of selectors) {
                            const img = document.querySelector(selector);
                            if (img) {
                                return img.src || img.dataset.src || img.dataset.original;
                            }
                        }
                        
                        return null;
                    }
                """)
                
                await page.close()
                
                if large_image_url:
                    return urljoin(target_url, large_image_url)
                    
            return None
            
        except Exception as e:
            self.logger.error(f"获取大图失败: {str(e)}")
            try:
                await page.close()
            except:
                pass
            return None
    
    async def _find_next_page(self, page):
        """智能查找下一页链接"""
        try:
            # 使用JavaScript在页面中智能查找"下一页"链接
            next_url = await page.evaluate("""
                () => {
                    // 常见的"下一页"文字
                    const nextTexts = [
                        '下一页', '下一頁', 'next', 'Next', 'NEXT', 
                        '次のページ', '다음', '>', '»', '››', 
                        'next page', 'Next Page', '下页'
                    ];
                    
                    // 常见的"下一页"类名或ID
                    const nextSelectors = [
                        'a.next',
                        'a.next-page',
                        'a[rel="next"]',
                        '.pagination a.next',
                        '.pagination .next',
                        '.pager a.next',
                        '.page-next',
                        '#next',
                        '[class*="next"]',
                        '[id*="next"]',
                        '.pagination a:last-child',
                        '.page-numbers.next'
                    ];
                    
                    // 策略1: 通过CSS选择器查找
                    for (const selector of nextSelectors) {
                        const link = document.querySelector(selector);
                        if (link && link.href && link.offsetParent !== null) {
                            // 确保链接可见且有效
                            return link.href;
                        }
                    }
                    
                    // 策略2: 通过文字内容查找
                    const allLinks = Array.from(document.querySelectorAll('a'));
                    for (const link of allLinks) {
                        const text = link.textContent.trim();
                        const title = link.title || '';
                        const ariaLabel = link.getAttribute('aria-label') || '';
                        
                        // 检查链接文字、title或aria-label是否包含"下一页"相关文字
                        for (const nextText of nextTexts) {
                            if (text === nextText || 
                                text.includes(nextText) || 
                                title.includes(nextText) ||
                                ariaLabel.includes(nextText)) {
                                if (link.href && link.offsetParent !== null) {
                                    return link.href;
                                }
                            }
                        }
                    }
                    
                    // 策略3: 查找分页中的数字链接（当前页+1）
                    const pagination = document.querySelector('.pagination, .pager, [class*="page"]');
                    if (pagination) {
                        const currentPage = pagination.querySelector('.active, .current, [class*="active"], [class*="current"]');
                        if (currentPage) {
                            const nextSibling = currentPage.parentElement?.nextElementSibling?.querySelector('a') ||
                                              currentPage.nextElementSibling?.querySelector('a');
                            if (nextSibling && nextSibling.href) {
                                return nextSibling.href;
                            }
                        }
                    }
                    
                    return null;
                }
            """)
            
            if next_url and next_url != page.url:
                # 将相对URL转换为绝对URL
                return urljoin(page.url, next_url)
            
            return None
            
        except Exception as e:
            self.logger.error(f"查找下一页失败: {str(e)}")
            return None
            
    async def _download_image(self, img_url: str) -> bool:
        """下载图片"""
        if img_url in self.downloaded_images:
            return True
        
        # 过滤 webp 格式
        if img_url.lower().endswith('.webp') or '.webp' in img_url.lower():
            self.logger.info(f"跳过 webp 格式: {img_url}")
            return False
            
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(img_url, timeout=aiohttp.ClientTimeout(total=30)) as response:
                    if response.status == 200:
                        content = await response.read()
                        
                        # 验证文件完整性
                        if not self._validate_image(content):
                            self.logger.warning(f"图片文件损坏或无效，跳过")
                            return False
                        
                        # 检查图片尺寸
                        if not self._check_image_size(content):
                            self.logger.info(f"图片尺寸不符合要求，跳过")
                            return False
                            
                        # 生成文件名
                        filename = self._generate_filename(img_url, content)
                        filepath = self.download_dir / filename
                        
                        # 保存图片
                        async with aiofiles.open(filepath, 'wb') as f:
                            await f.write(content)
                        
                        # 再次验证保存后的文件
                        if not self._verify_saved_file(filepath):
                            self.logger.error(f"保存后验证失败，删除文件: {filename}")
                            try:
                                filepath.unlink()
                            except:
                                pass
                            return False
                            
                        self.downloaded_images.add(img_url)
                        self.logger.info(f"✅ 下载成功: {filename}")
                        return True
                    else:
                        self.logger.error(f"HTTP {response.status}")
                        return False
                        
        except Exception as e:
            self.logger.error(f"下载失败: {str(e)}")
            return False
            
    def _validate_image(self, content: bytes) -> bool:
        """验证图片文件完整性"""
        try:
            # 检查内容是否为空
            if not content or len(content) < 100:
                self.logger.warning("图片内容太小或为空")
                return False
            
            # 尝试打开图片验证完整性
            img = Image.open(BytesIO(content))
            
            # 检查是否为 webp 格式
            if img.format and img.format.lower() == 'webp':
                self.logger.info("检测到 webp 格式，跳过")
                return False
            
            # 验证图片可以正常读取
            img.verify()
            
            # 重新打开以确保可以获取尺寸（verify后需要重新打开）
            img = Image.open(BytesIO(content))
            _ = img.size  # 确保可以读取尺寸
            
            return True
        except Exception as e:
            self.logger.warning(f"图片验证失败: {str(e)}")
            return False
    
    def _verify_saved_file(self, filepath: Path) -> bool:
        """验证保存后的文件"""
        try:
            with Image.open(filepath) as img:
                # 检查格式
                if img.format and img.format.lower() == 'webp':
                    return False
                # 尝试加载图片数据
                img.load()
                return True
        except Exception as e:
            self.logger.warning(f"文件验证失败: {str(e)}")
            return False
            
    def _check_image_size(self, content: bytes) -> bool:
        """检查图片尺寸"""
        try:
            img = Image.open(BytesIO(content))
            width, height = img.size
            result = width >= self.min_size[0] and height >= self.min_size[1]
            self.logger.info(f"图片尺寸: {width}x{height} (最小要求: {self.min_size[0]}x{self.min_size[1]}) - {'✓' if result else '✗'}")
            return result
        except:
            return True
            
    def _generate_filename(self, url: str, content: bytes) -> str:
        """生成文件名（排除webp）"""
        parsed = urlparse(url)
        ext = os.path.splitext(parsed.path)[1].lower()
        
        # 排除 webp 格式
        if not ext or ext not in {'.jpg', '.jpeg', '.png', '.gif', '.bmp'}:
            try:
                img = Image.open(BytesIO(content))
                format_lower = img.format.lower() if img.format else 'jpg'
                # 如果是 webp，转换为 jpg
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
        print("爬取完成！统计信息：")
        print("="*60)
        print(f"爬取页数: {self.stats['pages_crawled']}")
        print(f"发现缩略图数: {self.stats['thumbnails_found']}")
        print(f"找到大图数: {self.stats['large_images_found']}")
        print(f"下载成功数: {self.stats['images_downloaded']}")
        print(f"下载失败数: {self.stats['images_failed']}")
        print(f"下载目录: {self.download_dir.absolute()}")
        print("="*60)


def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='点击图片获取大图爬虫（支持自动翻页+并发下载）')
    parser.add_argument('url', help='要爬取的网站URL')
    parser.add_argument('-o', '--output', type=str, default=None,
                        help='输出目录')
    parser.add_argument('--min-width', type=int, default=500,
                        help='最小图片宽度 (默认: 500)')
    parser.add_argument('--min-height', type=int, default=500,
                        help='最小图片高度 (默认: 500)')
    parser.add_argument('--delay', type=int, default=2,
                        help='每次点击之间的延迟（秒） (默认: 2)')
    parser.add_argument('--max-pages', type=int, default=10,
                        help='最大翻页数量 (默认: 10)')
    parser.add_argument('-c', '--concurrent', type=int, default=5,
                        help='并发下载数量 (默认: 5)')
    
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
        output_dir = f"./downloads/{domain}_{timestamp}_large"
    
    print(f"""
╔════════════════════════════════════════╗
║  点击图片爬虫 v3.0 (翻页+并发下载) ║
╚════════════════════════════════════════╝

配置信息：
- 目标网站: {args.url}
- 输出目录: {output_dir}
- 最小尺寸: {args.min_width}x{args.min_height}
- 点击延迟: {args.delay}秒
- 最大页数: {args.max_pages}页
- 并发下载: {args.concurrent}个
- 工作模式: 串行获取URL + 并发下载 + 自动翻页

开始工作...
""")
    
    crawler = ClickImageCrawler(
        base_url=args.url,
        download_dir=output_dir,
        min_size=(args.min_width, args.min_height),
        delay=args.delay,
        max_pages=args.max_pages,
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
