import requests
from bs4 import BeautifulSoup
import html2text
import logging
import time
import asyncio
import aiohttp
from requests.exceptions import RequestException
from urllib3.exceptions import InsecureRequestWarning
import urllib3
import certifi
import ssl
import unicodedata
from typing import Dict, Optional, Tuple, Union
from functools import lru_cache

from llama_index.core.tools import FunctionTool

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Create a session for connection pooling
session = requests.Session()

# Simple in-memory cache
PAGE_CACHE = {}
CACHE_TTL = 3600  # 1 hour cache lifetime

async def async_crawl_page(url: str, verify_ssl: bool = True, headers: Optional[Dict[str, str]] = None, 
                     timeout: int = 30, max_content_length: int = 5 * 1024 * 1024) -> Tuple[str, bool]:
    """
    Asynchronously crawls a webpage and converts its content to markdown format suitable for LLMs.
    
    Args:
        url: The URL to crawl
        verify_ssl: Whether to verify SSL certificates
        headers: Optional HTTP headers for the request
        timeout: Request timeout in seconds
        max_content_length: Maximum content length in bytes to process
        
    Returns:
        Tuple containing (markdown_content, success_flag)
    """
    # Check cache first
    cache_key = f"{url}_{verify_ssl}"
    if cache_key in PAGE_CACHE:
        cache_entry, timestamp = PAGE_CACHE[cache_key]
        if time.time() - timestamp < CACHE_TTL:
            logger.info(f"Using cached content for {url}")
            return cache_entry
    
    start_time = time.time()
    logger.info(f"Starting async crawl of {url}")
    
    # Default headers if none provided
    if headers is None:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
    
    try:
        timeout_obj = aiohttp.ClientTimeout(total=timeout, connect=10, sock_connect=10, sock_read=timeout)
        ssl_context = None if verify_ssl else False
        
        async with aiohttp.ClientSession(headers=headers, timeout=timeout_obj) as session:
            logger.debug(f"Sending async request to {url}")
            async with session.get(url, ssl=ssl_context) as response:
                if response.status >= 400:
                    error_message = f"HTTP error {response.status} for {url}"
                    logger.error(error_message)
                    return f"# Error Crawling Page\n\n{error_message}", False
                
                # Check content length if provided in headers
                content_length = response.headers.get('Content-Length')
                if content_length and int(content_length) > max_content_length:
                    error_message = f"Content too large ({content_length} bytes) for {url}"
                    logger.warning(error_message)
                    return f"# Error Crawling Page\n\n{error_message}", False
                
                content = await response.text()
                
                # Check actual content length
                if len(content) > max_content_length:
                    error_message = f"Content too large (actual: {len(content)} bytes) for {url}"
                    logger.warning(error_message)
                    return f"# Error Crawling Page\n\n{error_message}", False
                
                # Parse the HTML content
                soup = BeautifulSoup(content, 'html.parser')
                
                # Remove scripts, styles, and other non-content elements
                for script in soup(["script", "style", "meta", "noscript", "iframe"]):
                    script.extract()
                
                # Convert HTML to markdown
                h2t = html2text.HTML2Text()
                h2t.ignore_links = False
                h2t.ignore_images = False
                h2t.ignore_tables = False
                h2t.body_width = 0  # No wrapping
                
                markdown_content = h2t.handle(str(soup))
                
                # Clean up the markdown content
                markdown_content = clean_markdown(markdown_content)
                
                elapsed_time = time.time() - start_time
                logger.info(f"Successfully crawled {url} in {elapsed_time:.2f}s")
                
                result = (markdown_content, True)
                # Cache the result
                PAGE_CACHE[cache_key] = (result, time.time())
                return result
                
    except asyncio.TimeoutError:
        elapsed_time = time.time() - start_time
        error_message = f"Timeout error crawling {url} after {elapsed_time:.2f}s"
        logger.error(error_message)
        return f"# Error Crawling Page\n\n{error_message}", False
    
    except Exception as e:
        elapsed_time = time.time() - start_time
        error_message = f"Error crawling {url} after {elapsed_time:.2f}s: {str(e)}"
        logger.error(error_message)
        return f"# Error Crawling Page\n\n{error_message}", False

def crawl_page(url: str, verify_ssl: bool = True, headers: Optional[Dict[str, str]] = None, 
               timeout: int = 30) -> Tuple[str, bool]:
    """
    Crawls a webpage and converts its content to markdown format suitable for LLMs.
    
    Args:
        url: The URL to crawl
        verify_ssl: Whether to verify SSL certificates
        headers: Optional HTTP headers for the request
        timeout: Request timeout in seconds
        
    Returns:
        Tuple containing (markdown_content, success_flag)
    """
    # Check cache first
    cache_key = f"{url}_{verify_ssl}"
    if cache_key in PAGE_CACHE:
        cache_entry, timestamp = PAGE_CACHE[cache_key]
        if time.time() - timestamp < CACHE_TTL:
            logger.info(f"Using cached content for {url}")
            return cache_entry
    
    start_time = time.time()
    logger.info(f"Starting crawl of {url}")
    
    # Default headers if none provided
    if headers is None:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
    # Suppress only the InsecureRequestWarning if verify_ssl is False
    if not verify_ssl:
        urllib3.disable_warnings(InsecureRequestWarning)
    
    try:
        # Make the request with appropriate error handling
        logger.debug(f"Sending request to {url}")
        response = session.get(
            url, 
            headers=headers,
            verify=verify_ssl,
            timeout=(10, timeout)  # (connect_timeout, read_timeout)
        )
        response.raise_for_status()  # Raise exception for 4XX/5XX responses
        
        # Parse the HTML content
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Remove scripts, styles, and other non-content elements
        for script in soup(["script", "style", "meta", "noscript", "iframe"]):
            script.extract()
        
        # Convert HTML to markdown
        h2t = html2text.HTML2Text()
        h2t.ignore_links = False
        h2t.ignore_images = False
        h2t.ignore_tables = False
        h2t.body_width = 0  # No wrapping
        
        markdown_content = h2t.handle(str(soup))
        
        # Clean up the markdown content
        markdown_content = clean_markdown(markdown_content)
        
        elapsed_time = time.time() - start_time
        logger.info(f"Successfully crawled {url} in {elapsed_time:.2f}s")
        
        result = (markdown_content, True)
        # Cache the result
        PAGE_CACHE[cache_key] = (result, time.time())
        return result
        
    except RequestException as e:
        elapsed_time = time.time() - start_time
        error_message = f"Error crawling {url} after {elapsed_time:.2f}s: {str(e)}"
        logger.error(error_message)
        return f"# Error Crawling Page\n\n{error_message}", False
    
    except Exception as e:
        elapsed_time = time.time() - start_time
        error_message = f"Unexpected error crawling {url} after {elapsed_time:.2f}s: {str(e)}"
        logger.error(error_message)
        return f"# Unexpected Error\n\n{error_message}", False

# Cache frequently accessed content
@lru_cache(maxsize=128)
def clean_markdown(content: str) -> str:
    """
    Cleans and normalizes markdown content to be more LLM-friendly.
    
    Args:
        content: Raw markdown content
        
    Returns:
        Cleaned markdown content
    """
    # Remove excessive newlines
    while '\n\n\n' in content:
        content = content.replace('\n\n\n', '\n\n')
    
    # Remove Unicode control characters
    content = ''.join(ch for ch in content if not unicodedata.category(ch).startswith('C') 
                      or ch in ('\n', '\t'))
    
    # Fix common markdown issues
    lines = content.split('\n')
    cleaned_lines = []
    
    for line in lines:
        # Remove excessive spaces at beginning of lines
        line = line.lstrip()
        
        # Ensure proper heading spacing
        if line.startswith('#'):
            parts = line.split(' ', 1)
            if len(parts) > 1 and parts[0].strip('#') == '':
                line = parts[0] + ' ' + parts[1].lstrip()
        
        cleaned_lines.append(line)
    
    return '\n'.join(cleaned_lines)


async def async_get_page_as_markdown(url: str, skip_ssl_verification: bool = False) -> str:
    """
    Asynchronous simplified interface to crawl a page and get markdown content.
    
    Args:
        url: The URL to crawl
        skip_ssl_verification: Whether to skip SSL certificate verification
        
    Returns:
        Markdown content of the page
    """
    markdown, success = await async_crawl_page(url, verify_ssl=not skip_ssl_verification)
    return markdown


def get_page_as_markdown(url: str, skip_ssl_verification: bool = False, use_async: bool = False) -> str:
    """
    Simplified interface to crawl a page and get markdown content.
    
    Args:
        url: The URL to crawl
        skip_ssl_verification: Whether to skip SSL certificate verification
        use_async: Whether to use asynchronous crawling
        
    Returns:
        Markdown content of the page
    """
    if use_async:
        return asyncio.run(async_get_page_as_markdown(url, skip_ssl_verification))
    else:
        markdown, success = crawl_page(url, verify_ssl=not skip_ssl_verification)
        return markdown



if __name__ == "__main__":
    # Example usage
    url = "https://www.firecrawl.dev/extract#pricing"
    markdown_content = get_page_as_markdown(url, skip_ssl_verification=True, use_async=True)
    print(markdown_content)