"""
Web Crawler Module

This module provides advanced web crawling functionality with configurable 
depth, concurrency, and content processing for GovStack.
"""
import os
import re
import time
import uuid
import hashlib
import logging
import asyncio
import requests
import urllib3
import chardet
from bs4 import BeautifulSoup
from markdownify import markdownify
from requests.exceptions import RequestException
from urllib3.exceptions import InsecureRequestWarning
from typing import Dict, Optional, Tuple, Union, List, Set, Any, Callable
from functools import lru_cache
from urllib.parse import urlparse, urlsplit, urljoin
from threading import Thread, Lock
from queue import Queue, PriorityQueue
from datetime import datetime, timedelta, timezone
import aiohttp
from aiohttp import ClientSession, ClientTimeout, TCPConnector
import unicodedata
import html2text
import ssl
import certifi

from sqlalchemy import select, update, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine

from app.db.models.webpage import Webpage, WebpageLink
from llama_index.core.tools import FunctionTool

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Create a session for connection pooling
session = requests.Session()

# Simple in-memory cache
PAGE_CACHE = {}
CACHE_TTL = 3600  # 1 hour cache lifetime

# Load database URL from environment or use default
# Ensure we're using the asyncpg driver for async database operations
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost/govstackdb")
if not DATABASE_URL.startswith('postgresql+asyncpg://'):
    # Convert standard postgresql:// URL to use asyncpg
    if DATABASE_URL.startswith('postgresql://'):
        DATABASE_URL = DATABASE_URL.replace('postgresql://', 'postgresql+asyncpg://', 1)
    # Convert psycopg2 URL if present
    elif DATABASE_URL.startswith('postgresql+psycopg2://'):
        DATABASE_URL = DATABASE_URL.replace('postgresql+psycopg2://', 'postgresql+asyncpg://', 1)

# Default user agent to mimic a browser
DEFAULT_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36"

# Default crawler settings
DEFAULT_SETTINGS = {
    "max_depth": 3,                  # Maximum link depth to crawl
    "max_concurrent_requests": 10,    # Maximum concurrent requests
    "follow_external_links": False,   # Whether to follow links to other domains
    "respect_robots_txt": False,       # Whether to respect robots.txt
    "delay": 0.1,                    # Delay between requests in seconds
    "timeout": 30,                    # Request timeout in seconds
    "max_retries": 3,                 # Maximum number of retries for failed requests
    "verify_ssl": False,               # Whether to verify SSL certificates
    "max_content_length": 5 * 1024 * 1024,  # Maximum content length in bytes (5MB)
    "file_extensions_to_skip": [      # File extensions to skip
        ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
        ".zip", ".rar", ".7z", ".tar", ".gz", ".jpg", ".jpeg", 
        ".png", ".gif", ".bmp", ".svg", ".mp3", ".mp4", ".avi", 
        ".mov", ".wmv", ".flv", ".exe", ".dll", ".so", ".jar"
    ],
    "follow_redirects": True,         # Whether to follow redirects
    "max_redirects": 5,               # Maximum number of redirects to follow
    "crawl_strategy": "breadth_first",  # breadth_first or depth_first
    "log_level": "INFO",              # Logging level
}

class RobotsTxtParser:
    """Parser for robots.txt files."""
    
    def __init__(self):
        self.robot_cache = {}  # Cache for robots.txt content
    
    async def async_fetch_robots_txt(self, base_url):
        """Asynchronously fetch and parse robots.txt for a given domain."""
        parsed_url = urlparse(base_url)
        robots_url = f"{parsed_url.scheme}://{parsed_url.netloc}/robots.txt"
        
        if robots_url in self.robot_cache:
            return self.robot_cache[robots_url]
        
        try:
            async with ClientSession() as session:
                async with session.get(robots_url, timeout=10) as response:
                    if response.status == 200:
                        text = await response.text()
                        self.robot_cache[robots_url] = self._parse_robots_txt(text)
                        return self.robot_cache[robots_url]
                    else:
                        # If robots.txt doesn't exist or can't be fetched, allow all
                        self.robot_cache[robots_url] = {"allow_all": True, "disallow": []}
                        return self.robot_cache[robots_url]
        except Exception as e:
            logger.warning(f"Error fetching robots.txt from {robots_url}: {e}")
            # Allow all if robots.txt can't be fetched
            self.robot_cache[robots_url] = {"allow_all": True, "disallow": []}
            return self.robot_cache[robots_url]
    
    def fetch_robots_txt(self, base_url):
        """Fetch and parse robots.txt for a given domain."""
        parsed_url = urlparse(base_url)
        robots_url = f"{parsed_url.scheme}://{parsed_url.netloc}/robots.txt"
        
        if robots_url in self.robot_cache:
            return self.robot_cache[robots_url]
        
        try:
            response = session.get(robots_url, timeout=10)
            if response.status_code == 200:
                self.robot_cache[robots_url] = self._parse_robots_txt(response.text)
                return self.robot_cache[robots_url]
            else:
                # If robots.txt doesn't exist or can't be fetched, allow all
                self.robot_cache[robots_url] = {"allow_all": True, "disallow": []}
                return self.robot_cache[robots_url]
        except Exception as e:
            logger.warning(f"Error fetching robots.txt from {robots_url}: {e}")
            # Allow all if robots.txt can't be fetched
            self.robot_cache[robots_url] = {"allow_all": True, "disallow": []}
            return self.robot_cache[robots_url]
    
    def _parse_robots_txt(self, content):
        """Parse robots.txt content to extract rules."""
        rules = {"allow_all": False, "disallow": []}
        
        # Simple parser for robots.txt - looks for Disallow: directives for our user agent
        # This is a simplified implementation - a full implementation would also consider
        # Allow directives, different user agents, etc.
        lines = content.splitlines()
        is_relevant_section = False
        
        for line in lines:
            line = line.strip()
            
            if not line or line.startswith('#'):
                continue
                
            # Check if this section applies to us
            if line.lower().startswith('user-agent:'):
                agent = line.split(':', 1)[1].strip()
                # If '*' or our user agent, this section applies to us
                if agent == '*' or DEFAULT_USER_AGENT.lower() in agent.lower():
                    is_relevant_section = True
                else:
                    is_relevant_section = False
            
            # If we're in a relevant section, check for disallow directives
            if is_relevant_section and line.lower().startswith('disallow:'):
                path = line.split(':', 1)[1].strip()
                if path:  # Skip empty disallow (which means allow all)
                    rules["disallow"].append(path)
        
        return rules
    
    def is_allowed(self, url, robots_rules):
        """Check if a URL is allowed by robots.txt rules."""
        if robots_rules.get("allow_all", False):
            return True
            
        path = urlparse(url).path
        
        for disallow_path in robots_rules.get("disallow", []):
            # If path starts with disallow_path, it's disallowed
            if path.startswith(disallow_path):
                return False
        
        # If no matching disallow rule, allow
        return True


def get_domain(url):
    """
    Extract the domain from a URL.
    """
    return urlparse(url).netloc


def is_valid_url(url):
    """
    Check if a URL is valid.
    """
    parsed = urlparse(url)
    return bool(parsed.netloc and parsed.scheme)


def sanitize_url(url):
    """
    Sanitize a URL by removing fragments, query parameters, etc.
    """
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}{parsed.path}"


def generate_content_hash(content):
    """
    Generate a hash of content to detect changes.
    """
    return hashlib.sha256(content.encode('utf-8')).hexdigest()


def is_file_url(url, extensions_to_skip):
    """
    Check if the URL points to a file with a specific extension.
    """
    parsed = urlparse(url)
    path = parsed.path.lower()
    return any(path.endswith(ext) for ext in extensions_to_skip)


def normalize_url(url, base_url=None):
    """
    Normalize a URL by resolving relative URLs, removing fragments, etc.
    """
    if base_url and not url.startswith(('http://', 'https://')):
        url = urljoin(base_url, url)
    
    parsed = urlparse(url)
    
    # Remove fragments
    url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
    
    # Add query parameters if they exist
    if parsed.query:
        url = f"{url}?{parsed.query}"
    
    return url


def extract_title(soup):
    """
    Extract the title from a BeautifulSoup object.
    """
    title = soup.find('title')
    return title.get_text().strip() if title else None


def extract_links(soup, base_url):
    """
    Extract all links from a BeautifulSoup object.
    """
    links = []
    
    for a_tag in soup.find_all('a', href=True):
        href = a_tag.get('href')
        if href:
            # Normalize the URL
            url = normalize_url(href, base_url)
            # Get the link text
            text = a_tag.get_text().strip()
            # Get the rel attribute
            rel = a_tag.get('rel', '')
            
            if is_valid_url(url):
                links.append({
                    'url': url,
                    'text': text,
                    'rel': ' '.join(rel) if isinstance(rel, list) else rel
                })
    
    return links


def html_to_markdown(html_content):
    """
    Convert HTML content to markdown.
    """
    try:
        # Parse HTML using BeautifulSoup
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Remove unwanted elements
        for unwanted in soup(["script", "style", "iframe", "noscript", "meta", "link"]):
            unwanted.decompose()
        
        # Convert to markdown
        md = markdownify(str(soup), heading_style="ATX")
        
        # Clean up the markdown
        return clean_markdown(md)
    except Exception as e:
        logger.error(f"Error converting HTML to markdown: {e}")
        return ""


class WebCrawler:
    """
    Advanced web crawler with configurable settings.
    """
    def __init__(self, settings=None, engine=None, collection_id=None, user_id=None, api_key_name=None):
        """
        Initialize the web crawler.
        
        Args:
            settings: Crawler settings
            engine: SQLAlchemy engine for database operations
            collection_id: Identifier for grouping crawl jobs
            user_id: User ID for audit trail
            api_key_name: API key name for audit trail
        """
        self.settings = DEFAULT_SETTINGS.copy()
        if settings:
            self.settings.update(settings)
        self.collection_id = collection_id
        self.user_id = user_id
        self.api_key_name = api_key_name
        # Ensure the database URL uses the asyncpg driver
        db_url = DATABASE_URL
        if not db_url.startswith('postgresql+asyncpg://'):
            # Convert standard postgresql:// URL to use asyncpg
            if db_url.startswith('postgresql://'):
                db_url = db_url.replace('postgresql://', 'postgresql+asyncpg://', 1)
            # Convert psycopg2 URL if present
            elif db_url.startswith('postgresql+psycopg2://'):
                db_url = db_url.replace('postgresql+psycopg2://', 'postgresql+asyncpg://', 1)
        
        self.engine = engine or create_async_engine(db_url, echo=False)
        self.session_maker = sessionmaker(self.engine, class_=AsyncSession, expire_on_commit=False)
        
        self.robots_parser = RobotsTxtParser()
        
        # Set up logging
        log_level = getattr(logging, self.settings['log_level'].upper())
        logging.getLogger(__name__).setLevel(log_level)
        
        # Tracking visited URLs to avoid duplicates
        self.visited_urls = set()
        self.visited_domains = set()
        
        # Progress tracking
        self.urls_crawled = 0
        self.urls_queued = 0
        self.start_time = None
        self.end_time = None
        
        # Track errors
        self.errors = []
    
    async def _get_or_create_webpage(self, session, url, depth, is_seed=False):
        """
        Get or create a webpage record in the database.
        """
        query = select(Webpage).where(Webpage.url == url)
        
        try:
            result = await session.execute(query)
            webpage = result.scalars().first()
            
            if not webpage:                
                logger.info(f"No existing webpage found for URL: {url}. Creating new record at depth {depth}")                
                # Remove the is_seed parameter as it's not supported by the Webpage model
                webpage = Webpage(
                    url=url,
                    crawl_depth=depth,
                    first_crawled=datetime.now(timezone.utc),
                    collection_id=self.collection_id,
                    created_by=self.user_id,
                    api_key_name=self.api_key_name
                )
                session.add(webpage)
                logger.debug(f"Added new webpage to session: {url}")
                
                try:
                    await session.commit()
                    logger.debug(f"Committed new webpage to database: {url}")
                    await session.refresh(webpage)
                    logger.info(f"Created new webpage record with ID: {webpage.id} for URL: {url}")
                except Exception as e:
                    logger.error(f"Database error when committing webpage {url}: {str(e)}")
                    raise
            else:
                logger.info(f"Found existing webpage record with ID: {webpage.id} for URL: {url}")
            
            return webpage
        except Exception as e:
            logger.error(f"Error in _get_or_create_webpage for {url}: {str(e)}")
            raise
    
    async def _add_link(self, session, source_id, target_id, text=None, rel=None):
        """
        Add a link between webpages in the database.
        """
        link = WebpageLink(
            source_id=source_id,
            target_id=target_id,
            text=text,
            rel=rel
        )
        session.add(link)
        await session.commit()
    
    async def _store_webpage_content(self, session, webpage_id, content, status_code, content_type=None):
        """
        Store webpage content in the database.
        """
        # Generate hash of content
        content_hash = generate_content_hash(content)
        
        # Extract title using BeautifulSoup
        soup = BeautifulSoup(content, 'html.parser')
        title = extract_title(soup)
        
        # Convert to markdown
        markdown_content = html_to_markdown(content)
        
        # Update webpage record
        query = (
            update(Webpage)
            .where(Webpage.id == webpage_id)
            .values(                title=title,
                content_hash=content_hash,
                content_markdown=markdown_content,
                last_crawled=datetime.now(timezone.utc),
                status_code=status_code,
                content_type=content_type
            )
        )
        await session.execute(query)
        await session.commit()
    
    async def _store_webpage_error(self, session, webpage_id, error_message):
        """
        Store webpage error in the database.
        """
        query = (
            update(Webpage)
            .where(Webpage.id == webpage_id)
            .values(                error=error_message,
                last_crawled=datetime.now(timezone.utc)
            )
        )
        await session.execute(query)
        await session.commit()
    
    async def _process_links(self, session, soup, base_url, webpage_id, depth):
        """
        Process links from a webpage and store them in the database.
        """
        links = extract_links(soup, base_url)
        links_processed = 0
        
        for link in links:
            url = link['url']
            target_domain = get_domain(url)
            
            # Skip external links if configured to do so
            if not self.settings['follow_external_links'] and target_domain != get_domain(base_url):
                continue
            
            # Skip file URLs
            if is_file_url(url, self.settings['file_extensions_to_skip']):
                continue
            
            try:
                # Get or create target webpage
                target_webpage = await self._get_or_create_webpage(session, url, depth + 1)
                
                # Add link
                await self._add_link(
                    session, 
                    source_id=webpage_id, 
                    target_id=target_webpage.id,
                    text=link['text'],
                    rel=link['rel']
                )
                
                links_processed += 1
            except Exception as e:
                logger.error(f"Error processing link {url}: {e}")
        
        return links_processed

    async def _fetch_page(self, requests_session, url, max_retries=3):
        """
        Fetch a webpage with retry logic and error handling using the requests module.
        This is a simplified version that works synchronously but is called from async methods.
        """
        retries = 0
        
        while retries < max_retries:
            try:
                headers = {
                    'User-Agent': DEFAULT_USER_AGENT,
                    'Accept': 'text/html,application/xhtml+xml,application/xml',
                    'Accept-Language': 'en-US,en;q=0.9',
                }
                
                # Use the passed requests_session object
                response = requests_session.get(
                    url,
                    headers=headers,
                    timeout=self.settings['timeout'],
                    verify=self.settings['verify_ssl'],
                    allow_redirects=self.settings['follow_redirects']
                )
                
                # Get response status and content type
                status_code = response.status_code
                content_type = response.headers.get('Content-Type')
                
                # Check content length from headers
                content_length = response.headers.get('Content-Length')
                if content_length and int(content_length) > self.settings['max_content_length']:
                    return None, f"Content too large ({content_length} bytes)", status_code, content_type
                
                # Get content
                content = response.content
                
                # Check actual content length
                if len(content) > self.settings['max_content_length']:
                    return None, f"Content too large (actual: {len(content)} bytes)", status_code, content_type
                
                # Detect encoding if not provided
                encoding = response.encoding or chardet.detect(content)['encoding'] or 'utf-8'
                
                try:
                    html_content = content.decode(encoding, errors='replace')
                    return html_content, None, status_code, content_type
                except UnicodeDecodeError as e:
                    return None, f"Unicode decode error: {e}", status_code, content_type
            
            except requests.Timeout:
                retries += 1
                if retries >= max_retries:
                    return None, f"Timeout after {max_retries} retries", None, None
                # Use asyncio.sleep for compatibility with async context
                await asyncio.sleep(self.settings['delay'] * (2 ** retries))  # Exponential backoff
            
            except requests.RequestException as e:
                retries += 1
                if retries >= max_retries:
                    return None, f"Request error after {max_retries} retries: {e}", None, None
                await asyncio.sleep(self.settings['delay'] * (2 ** retries))
            
            except Exception as e:
                return None, f"Unexpected error: {e}", None, None
    
    async def _crawl_url(self, url, depth, is_seed=False):
        """
        Crawl a URL and store its content in the database.
        """
        if depth > self.settings['max_depth']:
            return None
        
        # Skip file URLs
        if is_file_url(url, self.settings['file_extensions_to_skip']):
            return None
        
        # Skip URLs we've already visited
        if url in self.visited_urls:
            return None
        
        # Validate URL format before proceeding
        try:
            parsed = urlparse(url)
            if not all([parsed.scheme, parsed.netloc]):
                logger.warning(f"Invalid URL format: {url}")
                self.errors.append((url, "Invalid URL format"))
                return None
        except Exception as e:
            logger.warning(f"URL parsing error for {url}: {e}")
            self.errors.append((url, f"URL parsing error: {e}"))
            return None
        
        self.visited_urls.add(url)
        domain = get_domain(url)
        
        # Verify domain can be resolved before attempting to crawl
        try:
            import socket
            ip = socket.gethostbyname(domain)
            logger.info(f"DNS resolution successful: {domain} -> {ip}")
        except socket.gaierror as e:
            err_msg = f"DNS resolution failed for domain: {domain} - {e}"
            logger.warning(err_msg)
            
            # Try with fallback DNS (Google's public DNS)
            try:
                import dns.resolver
                resolver = dns.resolver.Resolver()
                resolver.nameservers = ['8.8.8.8', '8.8.4.4']  # Google's public DNS
                answer = resolver.resolve(domain, 'A')
                ip = answer[0].to_text()
                logger.info(f"Fallback DNS resolution successful: {domain} -> {ip}")
                # Continue with the crawl since we resolved the domain
            except Exception as fallback_err:
                # Both primary and fallback DNS resolution failed
                logger.error(f"All DNS resolution attempts failed: {fallback_err}")
                self.errors.append((url, err_msg))
                return None
        except Exception as e:
            logger.warning(f"Unexpected error during DNS resolution for {domain}: {e}")
            self.errors.append((url, f"DNS resolution error: {e}"))
            return None
        
        # Check robots.txt if enabled
        if self.settings['respect_robots_txt']:
            try:
                robots_rules = await self.robots_parser.async_fetch_robots_txt(url)
                if not self.robots_parser.is_allowed(url, robots_rules):
                    logger.info(f"Skipping {url} (disallowed by robots.txt)")
                    return None
            except Exception as e:
                logger.warning(f"Error checking robots.txt for {url}: {e}")
                # Continue anyway since robots.txt check is optional
        
        # Rate limiting by domain
        if domain in self.visited_domains:
            await asyncio.sleep(self.settings['delay'])
        else:
            self.visited_domains.add(domain)
        
        logger.info(f"Crawling {url} (depth {depth})")
        
        # Try using a custom session for this request with retry capability
        try:
            from requests.adapters import HTTPAdapter
            from urllib3.util.retry import Retry  # Corrected import
            
            custom_session = requests.Session()
            retry_strategy = Retry(
                total=self.settings['max_retries'],
                backoff_factor=0.5,
                status_forcelist=[429, 500, 502, 503, 504],
            )
            adapter = HTTPAdapter(max_retries=retry_strategy)
            custom_session.mount("http://", adapter)
            custom_session.mount("https://", adapter)
            
            # Test connection before proceeding
            test_response = custom_session.head(
                url, 
                timeout=self.settings['timeout']/2,
                verify=self.settings['verify_ssl'],
                allow_redirects=self.settings['follow_redirects']
            )
            logger.info(f"Connection test to {url} successful: Status {test_response.status_code}")
        except Exception as e:
            logger.warning(f"Connection test to {url} failed: {e}")
            # We'll continue anyway and let the fetch_page method handle retries
        
        async with self.session_maker() as session:
            try:
                logger.info(f"Creating session for {url}")
                # Get or create webpage record
                webpage = await self._get_or_create_webpage(session, url, depth, is_seed)
                logger.info(f"Webpage record created/updated: {webpage.id}")
                
                # Fetch the page with error handling
                try:
                    logger.info(f"Fetching {url} with custom session")
                    # Use the custom_session created above
                    html_content, error, status_code, content_type = await self._fetch_page(
                        custom_session, url, max_retries=self.settings['max_retries']
                    )
                    logger.info(f"Fetched {url}: Status {status_code}")
                except Exception as e:
                    logger.error(f"Error fetching {url}: {e}")
                    await self._store_webpage_error(session, webpage.id, str(e))
                    self.errors.append((url, str(e)))
                    return None
                
                # If error occurred, store it and return
                if error:
                    await self._store_webpage_error(session, webpage.id, error)
                    self.errors.append((url, error))
                    return None
                
                logger.info(f"Fetched {url} successfully")

                logger.info(f"Storing content for {url}")
                # Store webpage content
                await self._store_webpage_content(session, webpage.id, html_content, status_code, content_type)

                logger.info(f"Content stored for {url}")



                
                # Process links
                soup = BeautifulSoup(html_content, 'html.parser')
                links_processed = await self._process_links(session, soup, url, webpage.id, depth)
                
                self.urls_crawled += 1
                logger.info(f"Processed {links_processed} links from {url}")
                
                return webpage.id
            
            except Exception as e:
                logger.error(f"Error crawling {url}: {e} at depth {depth}")
                self.errors.append((url, str(e)))
                return None
    
    async def crawl(self, seed_urls, strategy='breadth_first'):
        """
        Crawl a list of seed URLs using the specified strategy.
        
        Args:
            seed_urls: List of URLs to start crawling from
            strategy: Crawl strategy ('breadth_first' or 'depth_first')
            
        Returns:
            Dictionary with crawl statistics
        """
        if isinstance(seed_urls, str):
            seed_urls = [seed_urls]
        
        self.visited_urls = set()
        self.visited_domains = set()
        self.urls_crawled = 0
        self.urls_queued = 0
        self.errors = []
        self.start_time = datetime.now(timezone.utc)
        
        if strategy == 'breadth_first':
            await self._breadth_first_crawl(seed_urls)
        elif strategy == 'depth_first':
            await self._depth_first_crawl(seed_urls)
        else:
            logger.error(f"Unknown crawl strategy: {strategy}")
            return {"error": f"Unknown crawl strategy: {strategy}"}
        
        self.end_time = datetime.now(timezone.utc)
        
        # Calculate statistics
        duration = (self.end_time - self.start_time).total_seconds()
        
        stats = {
            "seed_urls": seed_urls,
            "urls_crawled": self.urls_crawled,
            "urls_queued": self.urls_queued,
            "errors": len(self.errors),
            "duration_seconds": duration,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat(),
            "pages_per_second": self.urls_crawled / duration if duration > 0 else 0,
        }
        
        logger.info(f"Crawl completed: {stats}")
        return stats
    
    async def _breadth_first_crawl(self, seed_urls):
        """
        Perform a breadth-first crawl.
        """
        queue = asyncio.Queue()
        
        # Add seed URLs to queue
        for url in seed_urls:
            await queue.put((url, 0, True))  # (url, depth, is_seed)
            self.urls_queued += 1
        
        # Set up workers
        workers = []
        for _ in range(self.settings['max_concurrent_requests']):
            worker = asyncio.create_task(self._worker(queue))
            workers.append(worker)
        
        # Wait for queue to be empty
        await queue.join()
        
        # Cancel workers
        for worker in workers:
            worker.cancel()
        
        # Wait for workers to complete
        await asyncio.gather(*workers, return_exceptions=True)
    
    async def _worker(self, queue):
        """
        Worker for processing URLs from a queue.
        """
        while True:
            try:
                url, depth, is_seed = await queue.get()
                
                # Crawl the URL
                result = await self._crawl_url(url, depth, is_seed)
                
                # If successful, get outgoing links
                if result:
                    async with self.session_maker() as session:
                        # Get links from this page to other pages
                        query = select(WebpageLink).where(WebpageLink.source_id == result)
                        result = await session.execute(query)
                        links = result.scalars().all()
                        
                        # For each link, get the target webpage
                        for link in links:
                            query = select(Webpage).where(Webpage.id == link.target_id)
                            result = await session.execute(query)
                            target_webpage = result.scalars().first()
                            
                            # If within depth limit and not visited, add to queue
                            if (target_webpage and target_webpage.url not in self.visited_urls and
                                target_webpage.crawl_depth <= self.settings['max_depth']):
                                await queue.put((target_webpage.url, target_webpage.crawl_depth, False))
                                self.urls_queued += 1
                
                queue.task_done()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in worker: {e}")
                queue.task_done()
    
    async def _depth_first_crawl(self, seed_urls):
        """
        Perform a depth-first crawl.
        """
        stack = []
        
        # Add seed URLs to stack
        for url in seed_urls:
            stack.append((url, 0, True))  # (url, depth, is_seed)
            self.urls_queued += 1
        
        # Process stack
        while stack:
            # Get URL from stack
            url, depth, is_seed = stack.pop()
            
            # Crawl the URL
            result = await self._crawl_url(url, depth, is_seed)
            
            # If successful, get outgoing links
            if result:
                async with self.session_maker() as session:
                    # Get links from this page to other pages
                    query = select(WebpageLink).where(WebpageLink.source_id == result)
                    result = await session.execute(query)
                    links = result.scalars().all()
                    
                    # For each link, get the target webpage
                    for link in links:
                        query = select(Webpage).where(Webpage.id == link.target_id)
                        result = await session.execute(query)
                        target_webpage = result.scalars().first()
                        
                        # If within depth limit and not visited, add to stack
                        if (target_webpage and target_webpage.url not in self.visited_urls and
                            target_webpage.crawl_depth <= self.settings['max_depth']):
                            stack.append((target_webpage.url, target_webpage.crawl_depth, False))
                            self.urls_queued += 1
    
    async def crawl_page(self, url, skip_ssl=False, headers=None):
        """
        Crawl a single page and return its content.
        
        Args:
            url: URL to crawl
            skip_ssl: Whether to skip SSL verification
            headers: Custom headers to use
            
        Returns:
            Tuple of (markdown_content, success_flag)
        """
        # Save original verify_ssl setting
        original_verify_ssl = self.settings['verify_ssl']
        
        try:
            # Update settings for this request
            self.settings['verify_ssl'] = not skip_ssl
            
            # Create a new session for this single page crawl
            import requests  # Ensure requests is imported if not already at the top
            with requests.Session() as page_session:
                # Fetch the page
                html_content, error, status_code, content_type = await self._fetch_page(
                    page_session, url, max_retries=self.settings['max_retries']
                )
            
            if error:
                return f"# Error Crawling Page\n\n{error}", False
            
            # Convert to markdown
            markdown_content = html_to_markdown(html_content)
            
            return markdown_content, True
        
        except Exception as e:
            logger.error(f"Error crawling page {url}: {e}")
            return f"# Error Crawling Page\n\n{str(e)}", False
        
        finally:
            # Restore original verify_ssl setting
            self.settings['verify_ssl'] = original_verify_ssl
    
    async def get_page_as_markdown(self, url, skip_ssl=False):
        """
        Get a page as markdown.
        
        Args:
            url: URL to crawl
            skip_ssl: Whether to skip SSL verification
            
        Returns:
            Markdown content of the page
        """
        content, success = await self.crawl_page(url, skip_ssl=skip_ssl)
        return content




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


# Create crawler instance with default settings
crawler = WebCrawler()

async def async_get_page_as_markdown(url: str, skip_ssl_verification: bool = False) -> str:
    """
    Asynchronous function to get a page as markdown.
    
    Args:
        url: URL to crawl
        skip_ssl_verification: Whether to skip SSL verification
        
    Returns:
        Markdown content of the page
    """
    return await crawler.get_page_as_markdown(url, skip_ssl=skip_ssl_verification)


def get_page_as_markdown(url: str, skip_ssl_verification: bool = False) -> str:
    """
    Synchronous function to get a page as markdown.
    
    Args:
        url: URL to crawl
        skip_ssl_verification: Whether to skip SSL verification
        
    Returns:
        Markdown content of the page
    """
    return asyncio.run(async_get_page_as_markdown(url, skip_ssl_verification))


async def crawl_website(seed_url: str, depth: int = 3, concurrent_requests: int = 10, 
                        follow_external: bool = False, strategy: str = 'breadth_first',
                        collection_id: Optional[str] = None, session_maker=None, task_status=None,
                        user_id: Optional[str] = None, api_key_name: Optional[str] = None) -> Dict:
    """
    Crawl a website starting from a seed URL.
    
    Args:
        seed_url: URL to start crawling from
        depth: Maximum depth to crawl
        concurrent_requests: Maximum number of concurrent requests
        follow_external: Whether to follow external links
        strategy: Crawl strategy ('breadth_first' or 'depth_first')
        collection_id: Optional collection ID to group crawled pages
        session_maker: Optional SQLAlchemy session maker for database operations
        task_status: Optional dictionary to update with crawl status
        user_id: User ID for audit trail
        api_key_name: API key name for audit trail
        
    Returns:
        Dictionary with crawl statistics
    """
    settings = DEFAULT_SETTINGS.copy()
    settings.update({
        'max_depth': depth,
        'max_concurrent_requests': concurrent_requests,
        'follow_external_links': follow_external,
        'crawl_strategy': strategy
    })
      # Create crawler instance
    crawler = WebCrawler(settings=settings, collection_id=collection_id, user_id=user_id, api_key_name=api_key_name)
    
    # If session_maker is provided, use it
    if session_maker:
        crawler.session_maker = session_maker
    
    # Start crawl
    result = await crawler.crawl(seed_url, strategy=strategy)
    
    # Update task status if provided
    if task_status and isinstance(task_status, dict):
        task_status.update({
            "urls_crawled": result.get("urls_crawled", 0),
            "total_urls_queued": result.get("urls_queued", 0),
            "errors": result.get("errors", 0)
        })
    
    return result


# Create a tool for LLamaIndex
get_page_as_markdown_tool = FunctionTool.from_defaults(
    name="get_page_as_markdown",
    description="Fetch the content of a webpage and convert it to markdown format",
    fn=get_page_as_markdown
)


if __name__ == "__main__":
    from multiprocessing import cpu_count
    # Example usage
    async def main():
        # Use a reliable test URL (example.com is maintained specifically for testing)
        test_url = "https://example.com/"
        
        try:
            print(f"Testing direct requests access to {test_url}...")
            # Test basic connectivity first
            import socket
            domain = get_domain(test_url)
            try:
                ip = socket.gethostbyname(domain)
                print(f"DNS resolution successful: {domain} -> {ip}")
            except socket.gaierror as e:
                print(f"DNS resolution failed: {e}")
                print("This could indicate network connectivity issues or DNS problems.")
                print("Try using a different DNS server or check your internet connection.")
                
            # Try a basic request
            import requests
            response = requests.get(test_url, timeout=10)
            print(f"Direct request successful: Status {response.status_code}")
            
            # Crawl a website
            print("\nStarting web crawler test...")
            result = await crawl_website(
                seed_url=test_url,
                depth=1,  # Keep depth small for testing
                concurrent_requests=2,  # Smaller number for testing
                follow_external=False,
                strategy='breadth_first'
            )
            print(f"Crawl result: {result}")
            
            # If the test was successful, try the actual target
            target_url = "https://kfcb.go.ke/"
            print(f"\nTrying to crawl target URL: {target_url}")
            result = await crawl_website(
                seed_url=target_url,
                depth=1,
                concurrent_requests=2,
                follow_external=False,
                strategy='breadth_first'
            )
            print(f"Target crawl result: {result}")
            
        except Exception as e:
            print(f"Test failed with error: {e}")
            import traceback
            traceback.print_exc()
        
        # Get a page as markdown
        #markdown = await async_get_page_as_markdown("https://example.com")
        #print(f"Page markdown:\n{markdown}")
        
        from datetime import datetime, timezone
        import time

        start = datetime.now(timezone.utc)
        # Simulate some processing
        time.sleep(2)

        end = datetime.now(timezone.utc)

        duration = (end - start).total_seconds()
        print(f"Processing duration: {duration} seconds")
    
    # Run the example
    asyncio.run(main())