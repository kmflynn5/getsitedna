"""HTTP utilities and rate limiting."""

import asyncio
import time
from typing import Optional, Dict, Any
from urllib.robotparser import RobotFileParser

import aiohttp
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


class RateLimiter:
    """Simple rate limiter for HTTP requests."""
    
    def __init__(self, delay: float = 1.0):
        self.delay = delay
        self.last_request_time = 0.0
    
    async def wait(self):
        """Wait if necessary to respect rate limit."""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.delay:
            await asyncio.sleep(self.delay - time_since_last)
        
        self.last_request_time = time.time()


class HTTPSession:
    """HTTP session with retry logic and rate limiting."""
    
    def __init__(self, 
                 rate_limit_delay: float = 1.0,
                 timeout: int = 30,
                 user_agent: Optional[str] = None):
        self.rate_limiter = RateLimiter(rate_limit_delay)
        self.timeout = timeout
        self.user_agent = user_agent or "GetSiteDNA/0.1.0 (Website Analysis Tool)"
        
        # Setup session with retry strategy
        self.session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # Set default headers
        self.session.headers.update({
            'User-Agent': self.user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        })
    
    async def get(self, url: str, **kwargs) -> requests.Response:
        """Make a GET request with rate limiting."""
        await self.rate_limiter.wait()
        
        kwargs.setdefault('timeout', self.timeout)
        response = self.session.get(url, **kwargs)
        return response
    
    def get_sync(self, url: str, **kwargs) -> requests.Response:
        """Make a synchronous GET request."""
        kwargs.setdefault('timeout', self.timeout)
        return self.session.get(url, **kwargs)
    
    def close(self):
        """Close the session."""
        self.session.close()


class AsyncHTTPSession:
    """Async HTTP session for concurrent requests."""
    
    def __init__(self,
                 rate_limit_delay: float = 1.0,
                 timeout: int = 30,
                 concurrent_limit: int = 5,
                 user_agent: Optional[str] = None):
        self.rate_limiter = RateLimiter(rate_limit_delay)
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.concurrent_limit = concurrent_limit
        self.user_agent = user_agent or "GetSiteDNA/0.1.0 (Website Analysis Tool)"
        self.semaphore = asyncio.Semaphore(concurrent_limit)
        self._session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        headers = {
            'User-Agent': self.user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
        }
        
        self._session = aiohttp.ClientSession(
            timeout=self.timeout,
            headers=headers,
            connector=aiohttp.TCPConnector(limit=self.concurrent_limit)
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._session:
            await self._session.close()
    
    def get(self, url: str, **kwargs):
        """Make an async GET request with rate limiting and concurrency control."""
        return _AsyncRequestContext(self, url, **kwargs)


class _AsyncRequestContext:
    """Context manager for async HTTP requests with rate limiting."""
    
    def __init__(self, session: 'AsyncHTTPSession', url: str, **kwargs):
        self.session = session
        self.url = url
        self.kwargs = kwargs
        self.response = None
    
    async def __aenter__(self):
        async with self.session.semaphore:
            await self.session.rate_limiter.wait()
            
            if not self.session._session:
                raise RuntimeError("Session not initialized. Use async with.")
            
            self.response = await self.session._session.get(self.url, **self.kwargs)
            return await self.response.__aenter__()
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.response:
            return await self.response.__aexit__(exc_type, exc_val, exc_tb)


class RobotsChecker:
    """Check robots.txt compliance."""
    
    def __init__(self, base_url: str, user_agent: str = "*"):
        self.base_url = base_url.rstrip("/")
        self.user_agent = user_agent
        self.robots_parser = RobotFileParser()
        self.robots_parser.set_url(f"{self.base_url}/robots.txt")
        self._loaded = False
    
    def load_robots_txt(self) -> bool:
        """Load and parse robots.txt file."""
        try:
            self.robots_parser.read()
            self._loaded = True
            return True
        except Exception:
            self._loaded = False
            return False
    
    def can_fetch(self, url: str) -> bool:
        """Check if URL can be fetched according to robots.txt."""
        if not self._loaded:
            # If robots.txt couldn't be loaded, assume allowed
            return True
        
        try:
            return self.robots_parser.can_fetch(self.user_agent, url)
        except Exception:
            # If there's an error checking, assume allowed
            return True
    
    def get_crawl_delay(self) -> Optional[float]:
        """Get crawl delay from robots.txt."""
        if not self._loaded:
            return None
        
        try:
            delay = self.robots_parser.crawl_delay(self.user_agent)
            return float(delay) if delay else None
        except Exception:
            return None
    
    def get_sitemaps(self) -> list[str]:
        """Get sitemap URLs from robots.txt."""
        if not self._loaded:
            return []
        
        try:
            return list(self.robots_parser.site_maps())
        except Exception:
            return []