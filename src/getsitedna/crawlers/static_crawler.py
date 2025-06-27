"""Static HTML crawler using BeautifulSoup."""

import asyncio
from typing import Dict, List, Optional, Set
from urllib.parse import urljoin, urlparse
import xml.etree.ElementTree as ET

import requests
from bs4 import BeautifulSoup, Tag
from pydantic import HttpUrl

from ..models.site import Site
from ..models.page import Page
from ..models.schemas import CrawlStatus, AssetInfo
from ..utils.http import HTTPSession, RobotsChecker
from ..utils.validation import is_valid_url, is_same_domain, resolve_url, normalize_url


class StaticCrawler:
    """Static HTML crawler for traditional websites."""
    
    def __init__(self, site: Site):
        self.site = site
        self.session = HTTPSession(
            rate_limit_delay=site.config.rate_limit_delay,
            timeout=site.config.timeout,
            user_agent=site.config.user_agent
        )
        self.robots_checker = RobotsChecker(str(site.base_url))
        self.discovered_urls: Set[str] = set()
        self.crawled_urls: Set[str] = set()
        
    async def crawl_site(self) -> Site:
        """Crawl the entire site starting from base URL."""
        try:
            # Load robots.txt if respecting it
            if self.site.config.respect_robots_txt:
                robots_loaded = self.robots_checker.load_robots_txt()
                if robots_loaded:
                    # Update rate limit based on robots.txt
                    crawl_delay = self.robots_checker.get_crawl_delay()
                    if crawl_delay and crawl_delay > self.site.config.rate_limit_delay:
                        self.site.config.rate_limit_delay = crawl_delay
                        self.session.rate_limiter.delay = crawl_delay
            
            # Discover initial URLs
            await self._discover_initial_urls()
            
            # Crawl pages level by level
            await self._crawl_by_depth()
            
            return self.site
            
        finally:
            self.session.close()
    
    async def _discover_initial_urls(self):
        """Discover initial URLs from sitemaps and base URL."""
        # Add base URL
        self._add_discovered_url(str(self.site.base_url), depth=0)
        
        # Try to find sitemaps
        sitemap_urls = await self._discover_sitemaps()
        for sitemap_url in sitemap_urls:
            await self._parse_sitemap(sitemap_url)
    
    async def _discover_sitemaps(self) -> List[str]:
        """Discover sitemap URLs."""
        sitemaps = []
        
        # From robots.txt
        if self.site.config.respect_robots_txt:
            robot_sitemaps = self.robots_checker.get_sitemaps()
            sitemaps.extend(robot_sitemaps)
        
        # Common sitemap locations
        common_locations = [
            "/sitemap.xml",
            "/sitemap_index.xml",
            "/sitemaps.xml",
            "/sitemap/",
        ]
        
        for location in common_locations:
            sitemap_url = urljoin(str(self.site.base_url), location)
            if sitemap_url not in sitemaps:
                sitemaps.append(sitemap_url)
        
        return sitemaps
    
    async def _parse_sitemap(self, sitemap_url: str):
        """Parse an XML sitemap and extract URLs."""
        try:
            response = await self.session.get(sitemap_url)
            if response.status_code == 200:
                self.site.sitemap_urls.append(HttpUrl(sitemap_url))
                
                # Parse XML
                root = ET.fromstring(response.content)
                
                # Handle namespace
                namespaces = {
                    'sitemap': 'http://www.sitemaps.org/schemas/sitemap/0.9'
                }
                
                # Look for URL elements
                for url_elem in root.findall('.//sitemap:url/sitemap:loc', namespaces):
                    if url_elem.text:
                        self._add_discovered_url(url_elem.text, depth=1)
                
                # Look for nested sitemaps
                for sitemap_elem in root.findall('.//sitemap:sitemap/sitemap:loc', namespaces):
                    if sitemap_elem.text:
                        await self._parse_sitemap(sitemap_elem.text)
                        
        except Exception as e:
            self.site.add_warning(f"Failed to parse sitemap {sitemap_url}: {e}")
    
    def _add_discovered_url(self, url: str, depth: int = 0, parent_url: Optional[str] = None):
        """Add a discovered URL to the crawl queue."""
        normalized_url = normalize_url(url)
        
        # Skip if already discovered
        if normalized_url in self.discovered_urls:
            return
        
        # Validate URL
        if not is_valid_url(normalized_url):
            return
        
        # Check domain
        if not is_same_domain(normalized_url, str(self.site.base_url)):
            return
        
        # Check depth limit
        if depth > self.site.config.max_depth:
            return
        
        # Check page limit
        if len(self.discovered_urls) >= self.site.config.max_pages:
            return
        
        # Check robots.txt
        if self.site.config.respect_robots_txt and not self.robots_checker.can_fetch(normalized_url):
            return
        
        # Add to discovered URLs
        self.discovered_urls.add(normalized_url)
        
        # Create page object
        page = Page(
            url=HttpUrl(normalized_url),
            depth=depth,
            parent_url=HttpUrl(parent_url) if parent_url else None,
        )
        
        self.site.add_page(page)
    
    async def _crawl_by_depth(self):
        """Crawl pages level by level to respect depth limits."""
        for depth in range(self.site.config.max_depth + 1):
            pages_at_depth = self.site.get_pages_by_depth(depth)
            uncrawled_pages = [p for p in pages_at_depth if p.status == CrawlStatus.PENDING]
            
            if not uncrawled_pages:
                continue
            
            # Crawl pages at this depth
            for page in uncrawled_pages:
                if len(self.crawled_urls) >= self.site.config.max_pages:
                    break
                
                await self._crawl_page(page)
    
    async def _crawl_page(self, page: Page):
        """Crawl a single page."""
        url = str(page.url)
        
        if url in self.crawled_urls:
            return
        
        try:
            page.status = CrawlStatus.CRAWLING
            response = await self.session.get(url)
            
            # Update page with response info
            page.mark_crawled(response.status_code, response.headers.get('content-type'))
            
            if not page.is_successful:
                page.add_error(f"HTTP {response.status_code}")
                return
            
            # Store HTML content
            page.html_content = response.text
            page.content_length = len(response.text)
            
            # Parse HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract basic page info
            self._extract_basic_info(page, soup)
            
            # Extract links for further crawling
            self._extract_links(page, soup)
            
            # Extract assets
            self._extract_assets(page, soup)
            
            self.crawled_urls.add(url)
            
        except Exception as e:
            page.status = CrawlStatus.FAILED
            page.add_error(f"Crawl failed: {e}")
    
    def _extract_basic_info(self, page: Page, soup: BeautifulSoup):
        """Extract basic page information."""
        # Title
        title_tag = soup.find('title')
        if title_tag:
            page.title = title_tag.get_text().strip()
        
        # Meta description
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc and meta_desc.get('content'):
            page.seo.description = meta_desc['content']
        
        # Meta keywords
        meta_keywords = soup.find('meta', attrs={'name': 'keywords'})
        if meta_keywords and meta_keywords.get('content'):
            page.seo.keywords = [k.strip() for k in meta_keywords['content'].split(',')]
        
        # Open Graph
        og_title = soup.find('meta', property='og:title')
        if og_title and og_title.get('content'):
            page.seo.og_title = og_title['content']
        
        og_desc = soup.find('meta', property='og:description')
        if og_desc and og_desc.get('content'):
            page.seo.og_description = og_desc['content']
        
        og_image = soup.find('meta', property='og:image')
        if og_image and og_image.get('content'):
            page.seo.og_image = og_image['content']
        
        # Canonical URL
        canonical = soup.find('link', rel='canonical')
        if canonical and canonical.get('href'):
            try:
                page.seo.canonical_url = HttpUrl(canonical['href'])
            except Exception:
                pass
    
    def _extract_links(self, page: Page, soup: BeautifulSoup):
        """Extract links from the page."""
        links = soup.find_all('a', href=True)
        
        for link in links:
            href = link['href']
            absolute_url = resolve_url(str(page.url), href)
            normalized_url = normalize_url(absolute_url)
            
            if not is_valid_url(normalized_url):
                continue
            
            if is_same_domain(normalized_url, str(self.site.base_url)):
                page.add_internal_link(HttpUrl(normalized_url))
                
                # Add to crawl queue if not already discovered
                if normalized_url not in self.discovered_urls:
                    self._add_discovered_url(
                        normalized_url, 
                        depth=page.depth + 1,
                        parent_url=str(page.url)
                    )
            else:
                page.add_external_link(HttpUrl(normalized_url))
    
    def _extract_assets(self, page: Page, soup: BeautifulSoup):
        """Extract asset information from the page."""
        # Images
        images = soup.find_all('img', src=True)
        for img in images:
            src = img['src']
            absolute_url = resolve_url(str(page.url), src)
            
            asset = AssetInfo(
                url=absolute_url,
                type="image",
                alt_text=img.get('alt', ''),
            )
            
            # Try to extract dimensions
            width = img.get('width')
            height = img.get('height')
            if width and height:
                try:
                    asset.dimensions = (int(width), int(height))
                except ValueError:
                    pass
            
            page.add_asset(asset)
        
        # CSS files
        css_links = soup.find_all('link', rel='stylesheet', href=True)
        for css_link in css_links:
            href = css_link['href']
            absolute_url = resolve_url(str(page.url), href)
            
            asset = AssetInfo(
                url=absolute_url,
                type="css",
            )
            page.add_asset(asset)
        
        # JavaScript files
        js_scripts = soup.find_all('script', src=True)
        for script in js_scripts:
            src = script['src']
            absolute_url = resolve_url(str(page.url), src)
            
            asset = AssetInfo(
                url=absolute_url,
                type="javascript",
            )
            page.add_asset(asset)