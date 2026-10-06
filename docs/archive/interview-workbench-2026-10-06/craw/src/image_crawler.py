"""
高级图片爬虫模块
支持：
- 自动识别并下载原图
- 深度爬取
- 反爬虫处理
- 并发下载
"""
import os
import asyncio
import hashlib
import logging
from pathlib import Path
from typing import Set, List, Optional, Dict, Tuple
from urllib.parse import urljoin, urlparse, parse_qs
from datetime import datetime
import json
import re

from playwright.async_api import async_playwright, Page, Browser
import aiohttp
import aiofiles
from PIL import Image
from io import BytesIO


class ImageCrawler:
    """智能图片爬虫类"""
    
    def __init__(self, 
                 base_url: str,
                 download_dir: str = "./downloads",
                 max_depth: int = 2,
                 max_concurrent: int = 5,
                 min_image_size: Tuple[int, int] = (100, 100),
                 timeout: int = 30000):
        """
        初始化爬虫
        
        Args:
            base_url: 起始URL
            download_dir: 下载目录
            max_depth: 最大爬取深度
            max_concurrent: 最大并发数
            min_image_size: 最小图片尺寸 (width, height)
            timeout: 超时时间（毫秒）
        """
        self.base_url = base_url
        self.domain = urlparse(base_url).netloc
        self.download_dir = Path(download_dir)
        self.max_depth = max_depth
        self.max_concurrent = max_concurrent
        self.min_image_size = min_image_size
        self.timeout = timeout
        
        # 创建下载目录
        self.download_dir.mkdir(parents=True, exist_ok=True)
        
        # 记录已访问的URL和已下载的图片
        self.visited_urls: Set[str] = set()
        self.downloaded_images: Set[str] = set()
        self.failed_urls: Set[str] = set()
        
        # 设置日志
        self._setup_logging()
        
        # 统计信息
        self.stats = {
            "pages_crawled": 0,
            "images_found": 0,
            "images_downloaded": 0,
            "images_failed": 0,
            "start_time": None,
            "end_time": None
        }
        
    def _setup_logging(self):
        """设置日志"""
        log_dir = Path("./logs")
        log_dir.mkdir(exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(f'./logs/crawler_{datetime.now():%Y%m%d_%H%M%S}.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(self.__class__.__name__)
        
    async def crawl(self):
        """开始爬取"""
        self.stats["start_time"] = datetime.now()
        self.logger.info(f"开始爬取: {self.base_url}")
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            
            try:
                # 使用信号量控制并发
                semaphore = asyncio.Semaphore(self.max_concurrent)
                
                # 开始递归爬取
                await self._crawl_page(browser, self.base_url, 0, semaphore)
                
            finally:
                await browser.close()
                
        self.stats["end_time"] = datetime.now()
        self._print_stats()
        
    async def _crawl_page(self, browser: Browser, url: str, depth: int, semaphore: asyncio.Semaphore):
        """
        爬取单个页面
        
        Args:
            browser: Playwright浏览器实例
            url: 页面URL
            depth: 当前深度
            semaphore: 并发控制信号量
        """
        if depth > self.max_depth:
            return
            
        if url in self.visited_urls or url in self.failed_urls:
            return
            
        self.visited_urls.add(url)
        self.stats["pages_crawled"] += 1
        
        self.logger.info(f"爬取页面 [深度:{depth}]: {url}")
        
        try:
            page = await browser.new_page()
            await page.set_viewport_size({"width": 1920, "height": 1080})
            
            # 设置请求拦截，提高性能
            await page.route("**/*.{css,js,font,woff,woff2}", lambda route: route.abort())
            
            await page.goto(url, wait_until="networkidle", timeout=self.timeout)
            
            # 等待图片加载
            await page.wait_for_timeout(2000)
            
            # 查找所有图片
            images = await self._find_images(page, url)
            self.stats["images_found"] += len(images)
            
            # 并发下载图片
            download_tasks = []
            async with semaphore:
                for img_url, is_clickable in images:
                    if img_url not in self.downloaded_images:
                        task = asyncio.create_task(self._download_image(page, img_url, is_clickable))
                        download_tasks.append(task)
                        
            await asyncio.gather(*download_tasks, return_exceptions=True)
            
            # 如果还没达到最大深度，继续爬取子页面
            if depth < self.max_depth:
                links = await self._find_links(page)
                crawl_tasks = []
                for link in links[:10]:  # 限制每页最多爬取10个链接
                    task = asyncio.create_task(self._crawl_page(browser, link, depth + 1, semaphore))
                    crawl_tasks.append(task)
                await asyncio.gather(*crawl_tasks, return_exceptions=True)
                
            await page.close()
            
        except Exception as e:
            self.logger.error(f"爬取页面失败 {url}: {str(e)}")
            self.failed_urls.add(url)
            
    async def _find_images(self, page: Page, base_url: str) -> List[Tuple[str, bool]]:
        """
        查找页面中的所有图片
        
        Returns:
            List of (image_url, is_clickable)
        """
        images = []
        
        # 执行JavaScript查找所有图片及其点击状态
        img_data = await page.evaluate("""
            () => {
                const images = [];
                
                // 查找所有img标签
                document.querySelectorAll('img').forEach(img => {
                    const src = img.src || img.dataset.src || img.dataset.original;
                    if (src) {
                        // 检查图片是否可点击（是否在链接内或有点击事件）
                        const parent = img.closest('a');
                        const hasClickHandler = img.onclick || img.style.cursor === 'pointer';
                        const isClickable = parent || hasClickHandler;
                        
                        images.push({
                            src: src,
                            isClickable: isClickable,
                            parentHref: parent ? parent.href : null,
                            dataSrc: img.dataset.src,
                            dataOriginal: img.dataset.original
                        });
                    }
                });
                
                // 查找CSS背景图片
                document.querySelectorAll('*').forEach(el => {
                    const style = window.getComputedStyle(el);
                    const bg = style.backgroundImage;
                    if (bg && bg !== 'none') {
                        const match = bg.match(/url\\(['"]?(.+?)['"]?\\)/);
                        if (match) {
                            images.push({
                                src: match[1],
                                isClickable: false,
                                parentHref: null
                            });
                        }
                    }
                });
                
                return images;
            }
        """)
        
        for img in img_data:
            img_url = urljoin(base_url, img['src'])
            
            # 尝试获取原图URL
            if img.get('dataOriginal'):
                img_url = urljoin(base_url, img['dataOriginal'])
            elif img.get('parentHref'):
                # 如果图片在链接内，链接可能指向原图
                parent_url = urljoin(base_url, img['parentHref'])
                if self._is_image_url(parent_url):
                    img_url = parent_url
                    
            images.append((img_url, img['isClickable']))
            
        # 去重
        seen = set()
        unique_images = []
        for img_url, clickable in images:
            if img_url not in seen:
                seen.add(img_url)
                unique_images.append((img_url, clickable))
                
        self.logger.info(f"找到 {len(unique_images)} 张图片")
        return unique_images
        
    async def _find_links(self, page: Page) -> List[str]:
        """查找页面中的链接用于深度爬取"""
        links = await page.evaluate("""
            () => {
                const links = [];
                document.querySelectorAll('a[href]').forEach(a => {
                    links.push(a.href);
                });
                return links;
            }
        """)
        
        # 过滤和处理链接
        valid_links = []
        for link in links:
            parsed = urlparse(link)
            # 只爬取同域名的链接
            if parsed.netloc == self.domain or not parsed.netloc:
                full_url = urljoin(self.base_url, link)
                if full_url not in self.visited_urls and full_url not in self.failed_urls:
                    valid_links.append(full_url)
                    
        return valid_links
        
    async def _download_image(self, page: Page, img_url: str, is_clickable: bool):
        """
        下载图片，如果可点击则尝试获取原图
        """
        try:
            # 如果图片可点击，尝试获取原图
            if is_clickable:
                original_url = await self._try_get_original_image(page, img_url)
                if original_url:
                    img_url = original_url
                    self.logger.info(f"找到原图: {img_url}")
                    
            # 下载图片
            async with aiohttp.ClientSession() as session:
                async with session.get(img_url, timeout=aiohttp.ClientTimeout(total=30)) as response:
                    if response.status == 200:
                        content = await response.read()
                        
                        # 检查图片尺寸
                        if not self._check_image_size(content):
                            self.logger.debug(f"图片太小，跳过: {img_url}")
                            return
                            
                        # 生成文件名
                        filename = self._generate_filename(img_url, content)
                        filepath = self.download_dir / filename
                        
                        # 保存图片
                        async with aiofiles.open(filepath, 'wb') as f:
                            await f.write(content)
                            
                        self.downloaded_images.add(img_url)
                        self.stats["images_downloaded"] += 1
                        self.logger.info(f"下载成功: {filename}")
                    else:
                        raise Exception(f"HTTP {response.status}")
                        
        except Exception as e:
            self.logger.error(f"下载失败 {img_url}: {str(e)}")
            self.stats["images_failed"] += 1
            
    async def _try_get_original_image(self, page: Page, img_url: str) -> Optional[str]:
        """尝试获取原图URL"""
        try:
            # 在页面中查找包含该图片的链接
            original_url = await page.evaluate("""
                (imgUrl) => {
                    const img = document.querySelector(`img[src="${imgUrl}"]`);
                    if (img) {
                        const parent = img.closest('a');
                        if (parent && parent.href) {
                            // 检查链接是否指向图片
                            const href = parent.href;
                            if (/\.(jpg|jpeg|png|gif|webp|bmp)/i.test(href)) {
                                return href;
                            }
                        }
                        
                        // 检查data属性
                        if (img.dataset.original) return img.dataset.original;
                        if (img.dataset.src) return img.dataset.src;
                        if (img.dataset.largeSrc) return img.dataset.largeSrc;
                    }
                    return null;
                }
            """, img_url)
            
            if original_url:
                return urljoin(page.url, original_url)
                
        except:
            pass
            
        return None
        
    def _is_image_url(self, url: str) -> bool:
        """检查URL是否是图片"""
        image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.svg', '.ico'}
        parsed = urlparse(url.lower())
        return any(parsed.path.endswith(ext) for ext in image_extensions)
        
    def _check_image_size(self, content: bytes) -> bool:
        """检查图片尺寸是否满足最小要求"""
        try:
            img = Image.open(BytesIO(content))
            width, height = img.size
            return width >= self.min_image_size[0] and height >= self.min_image_size[1]
        except:
            return True  # 如果无法检查，默认接受
            
    def _generate_filename(self, url: str, content: bytes) -> str:
        """生成唯一的文件名"""
        # 获取原始文件扩展名
        parsed = urlparse(url)
        path = parsed.path
        ext = os.path.splitext(path)[1].lower()
        
        if not ext or ext not in {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp'}:
            # 根据内容类型推断扩展名
            try:
                img = Image.open(BytesIO(content))
                ext = f'.{img.format.lower()}' if img.format else '.jpg'
            except:
                ext = '.jpg'
                
        # 使用内容哈希生成唯一文件名
        hash_digest = hashlib.md5(content).hexdigest()[:16]
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{self.domain}_{timestamp}_{hash_digest}{ext}"
        
        return filename
        
    def _print_stats(self):
        """打印统计信息"""
        duration = (self.stats["end_time"] - self.stats["start_time"]).total_seconds()
        
        print("\n" + "="*50)
        print("爬取完成！统计信息：")
        print("="*50)
        print(f"爬取页面数: {self.stats['pages_crawled']}")
        print(f"发现图片数: {self.stats['images_found']}")
        print(f"下载成功数: {self.stats['images_downloaded']}")
        print(f"下载失败数: {self.stats['images_failed']}")
        print(f"总用时: {duration:.2f} 秒")
        print(f"下载目录: {self.download_dir.absolute()}")
        print("="*50)
        
        # 保存统计信息到文件
        stats_file = self.download_dir / "stats.json"
        with open(stats_file, 'w', encoding='utf-8') as f:
            stats_copy = self.stats.copy()
            stats_copy["start_time"] = stats_copy["start_time"].isoformat() if stats_copy["start_time"] else None
            stats_copy["end_time"] = stats_copy["end_time"].isoformat() if stats_copy["end_time"] else None
            json.dump(stats_copy, f, indent=2, ensure_ascii=False)
