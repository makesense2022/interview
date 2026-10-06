"""
爬虫配置文件
"""
import os
from pathlib import Path
from typing import Dict, Any

# 基础配置
BASE_DIR = Path(__file__).parent.parent
DOWNLOADS_DIR = BASE_DIR / "downloads"
LOGS_DIR = BASE_DIR / "logs"

# 爬虫默认配置
DEFAULT_CRAWLER_CONFIG = {
    # 爬取设置
    "max_depth": 2,                    # 最大爬取深度
    "max_concurrent": 5,                # 最大并发数
    "timeout": 30000,                   # 超时时间（毫秒）
    "wait_after_load": 2000,            # 页面加载后等待时间（毫秒）
    
    # 图片设置
    "min_image_width": 100,             # 最小图片宽度
    "min_image_height": 100,            # 最小图片高度
    "allowed_extensions": ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp'],
    
    # 浏览器设置
    "headless": True,                   # 是否无头模式
    "viewport_width": 1920,
    "viewport_height": 1080,
    
    # 限制设置
    "max_pages_per_depth": 10,          # 每层最多爬取页面数
    "max_images_per_page": 100,         # 每页最多下载图片数
}

# 预设网站配置
SITE_CONFIGS = {
    "default": DEFAULT_CRAWLER_CONFIG,
    
    # Instagram配置示例
    "instagram": {
        **DEFAULT_CRAWLER_CONFIG,
        "wait_after_load": 5000,
        "need_login": True,
    },
    
    # Pinterest配置示例
    "pinterest": {
        **DEFAULT_CRAWLER_CONFIG,
        "wait_after_load": 3000,
        "max_depth": 3,
    },
    
    # Unsplash配置示例
    "unsplash": {
        **DEFAULT_CRAWLER_CONFIG,
        "min_image_width": 500,
        "min_image_height": 500,
    },
}

# 请求头设置
DEFAULT_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
}

def get_site_config(site_name: str = "default") -> Dict[str, Any]:
    """获取特定网站的配置"""
    return SITE_CONFIGS.get(site_name, DEFAULT_CRAWLER_CONFIG).copy()

def merge_config(base_config: Dict[str, Any], custom_config: Dict[str, Any]) -> Dict[str, Any]:
    """合并配置"""
    result = base_config.copy()
    result.update(custom_config)
    return result
