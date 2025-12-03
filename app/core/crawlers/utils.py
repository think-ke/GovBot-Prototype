"""
Utility functions for web crawling functionality.
"""
import logging
import re
from bs4 import BeautifulSoup
from typing import Tuple, Optional
from urllib.parse import urlparse

from app.core.crawlers.web_crawler import WebCrawler

logger = logging.getLogger(__name__)

async def get_page_as_markdown(url: str, skip_ssl_verification: bool = False) -> Tuple[str, Optional[str]]:
    """
    Fetch a webpage and convert it to markdown.
    
    Args:
        url: URL to fetch
        skip_ssl_verification: Whether to skip SSL verification
        
    Returns:
        Tuple of (markdown_content, page_title)
    """
    crawler = WebCrawler()
    
    # Fetch the page
    content = await crawler.get_page_as_markdown(url, skip_ssl=skip_ssl_verification)
    
    # Extract title from markdown content (first heading)
    title = None
    if content:
        # Look for the first markdown heading
        match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
        if match:
            title = match.group(1).strip()
        else:
            # Fallback: use domain name as title
            parsed_url = urlparse(url)
            title = parsed_url.netloc
    
    return content, title
