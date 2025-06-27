"""Dynamic content crawler using Playwright for JavaScript-heavy sites."""

import asyncio
from typing import Dict, List, Optional, Set, Any
from urllib.parse import urljoin
import json

from playwright.async_api import async_playwright, Browser, BrowserContext, Page as PlaywrightPage
from pydantic import HttpUrl

from ..models.site import Site
from ..models.page import Page
from ..models.schemas import CrawlStatus, AssetInfo
from ..utils.validation import is_valid_url, is_same_domain, normalize_url


class DynamicCrawler:
    """Dynamic content crawler for JavaScript-heavy websites."""
    
    def __init__(self, site: Site):
        self.site = site
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.discovered_urls: Set[str] = set()
        self.crawled_urls: Set[str] = set()
        self.network_requests: Dict[str, List[str]] = {}  # Track API calls per page
        
    async def crawl_site(self) -> Site:
        """Crawl the site using Playwright for dynamic content."""
        async with async_playwright() as p:
            try:
                # Launch browser
                browser_type = getattr(p, self.site.config.browser_engine)
                self.browser = await browser_type.launch(
                    headless=True,
                    args=['--no-sandbox', '--disable-dev-shm-usage']
                )
                
                # Create context with realistic settings
                self.context = await self.browser.new_context(
                    viewport={'width': 1920, 'height': 1080},
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                )
                
                # Enable request interception for API discovery
                await self._setup_request_interception()
                
                # Start crawling from base URL
                await self._discover_initial_urls()
                
                # Crawl pages with depth control
                await self._crawl_by_depth()
                
                return self.site
                
            finally:
                if self.context:
                    await self.context.close()
                if self.browser:
                    await self.browser.close()
    
    async def _setup_request_interception(self):
        """Set up request interception to track API calls and assets."""
        self.context.on('request', self._handle_request)
        self.context.on('response', self._handle_response)
    
    async def _handle_request(self, request):
        """Handle intercepted requests to track API calls."""
        url = request.url
        
        # Track API endpoints (JSON, GraphQL, etc.)
        if any(keyword in url.lower() for keyword in ['api/', 'graphql', 'json', 'ajax']):
            page_url = request.frame.url if request.frame else "unknown"
            if page_url not in self.network_requests:
                self.network_requests[page_url] = []
            self.network_requests[page_url].append(url)
    
    async def _handle_response(self, response):
        """Handle responses to analyze content types and performance."""
        # Could be used for performance metrics in the future
        pass
    
    async def _discover_initial_urls(self):
        """Discover initial URLs including the base URL."""
        self._add_discovered_url(str(self.site.base_url), depth=0)
    
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
        
        # Add to discovered URLs
        self.discovered_urls.add(normalized_url)
        
        # Create or update page object
        if not self.site.has_page(normalized_url):
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
            
            # Process pages with concurrency control
            semaphore = asyncio.Semaphore(self.site.config.concurrent_requests)
            tasks = []
            
            for page in uncrawled_pages:
                if len(self.crawled_urls) >= self.site.config.max_pages:
                    break
                
                task = self._crawl_page_with_semaphore(semaphore, page)
                tasks.append(task)
            
            # Wait for all pages at this depth to complete
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)
            
            # Rate limiting between depth levels
            if depth < self.site.config.max_depth:
                await asyncio.sleep(self.site.config.rate_limit_delay)
    
    async def _crawl_page_with_semaphore(self, semaphore: asyncio.Semaphore, page: Page):
        """Crawl a page with concurrency control."""
        async with semaphore:
            await self._crawl_page(page)
    
    async def _crawl_page(self, page: Page):
        """Crawl a single page with Playwright."""
        url = str(page.url)
        
        if url in self.crawled_urls:
            return
        
        playwright_page = None
        try:
            page.status = CrawlStatus.CRAWLING
            
            # Create new page
            playwright_page = await self.context.new_page()
            
            # Set timeout
            playwright_page.set_default_timeout(self.site.config.timeout * 1000)
            
            # Navigate to page
            response = await playwright_page.goto(url, wait_until='networkidle')
            
            if not response:
                page.add_error("Failed to load page")
                page.status = CrawlStatus.FAILED
                return
            
            # Update page with response info
            page.mark_crawled(response.status, response.headers.get('content-type'))
            
            if not page.is_successful:
                page.add_error(f"HTTP {response.status}")
                return
            
            # Wait for dynamic content to load
            await self._wait_for_dynamic_content(playwright_page)
            
            # Extract content after JavaScript execution
            await self._extract_dynamic_content(page, playwright_page)
            
            # Extract links for further crawling
            await self._extract_dynamic_links(page, playwright_page)
            
            # Extract assets
            await self._extract_dynamic_assets(page, playwright_page)
            
            # Track API endpoints discovered during page load
            if url in self.network_requests:
                page.technical.api_endpoints = self.network_requests[url]
            
            self.crawled_urls.add(url)
            
        except Exception as e:
            page.status = CrawlStatus.FAILED
            page.add_error(f"Dynamic crawl failed: {e}")
            
        finally:
            if playwright_page:
                await playwright_page.close()
    
    async def _wait_for_dynamic_content(self, playwright_page: PlaywrightPage):
        """Wait for dynamic content to fully load."""
        try:
            # Wait for common loading indicators to disappear
            loading_selectors = [
                '[class*="loading"]',
                '[class*="spinner"]',
                '[id*="loading"]',
                '.loader',
                '.preloader'
            ]
            
            for selector in loading_selectors:
                try:
                    await playwright_page.wait_for_selector(selector, state='detached', timeout=5000)
                except:
                    pass  # Selector not found or timeout, continue
            
            # Wait for network to be idle
            await playwright_page.wait_for_load_state('networkidle')
            
            # Additional wait for common JavaScript frameworks
            await self._wait_for_frameworks(playwright_page)
            
        except Exception as e:
            # Don't fail the entire crawl if waiting fails
            pass
    
    async def _wait_for_frameworks(self, playwright_page: PlaywrightPage):
        """Wait for common JavaScript frameworks to finish rendering."""
        # React
        try:
            await playwright_page.wait_for_function(
                'window.React || document.querySelector("[data-reactroot]") || document.querySelector(".react-app")',
                timeout=3000
            )
        except:
            pass
        
        # Vue
        try:
            await playwright_page.wait_for_function(
                'window.Vue || document.querySelector("[data-v-]") || document.querySelector("#app")',
                timeout=3000
            )
        except:
            pass
        
        # Angular
        try:
            await playwright_page.wait_for_function(
                'window.ng || document.querySelector("[ng-app]") || document.querySelector("app-root")',
                timeout=3000
            )
        except:
            pass
    
    async def _extract_dynamic_content(self, page: Page, playwright_page: PlaywrightPage):
        """Extract content after JavaScript execution."""
        # Get rendered HTML
        page.rendered_html = await playwright_page.content()
        page.html_content = page.rendered_html  # Use rendered HTML as primary content
        page.content_length = len(page.rendered_html)
        
        # Extract page title
        page.title = await playwright_page.title()
        
        # Extract meta information
        await self._extract_meta_tags(page, playwright_page)
        
        # Detect JavaScript frameworks
        frameworks = await self._detect_frameworks(playwright_page)
        page.technical.javascript_frameworks = frameworks
        
        # Extract performance metrics
        performance_metrics = await self._extract_performance_metrics(playwright_page)
        page.technical.performance_metrics = performance_metrics
    
    async def _extract_meta_tags(self, page: Page, playwright_page: PlaywrightPage):
        """Extract meta tags and SEO information."""
        # Description
        try:
            desc_element = await playwright_page.query_selector('meta[name="description"]')
            if desc_element:
                page.seo.description = await desc_element.get_attribute('content')
        except:
            pass
        
        # Keywords
        try:
            keywords_element = await playwright_page.query_selector('meta[name="keywords"]')
            if keywords_element:
                keywords_content = await keywords_element.get_attribute('content')
                if keywords_content:
                    page.seo.keywords = [k.strip() for k in keywords_content.split(',')]
        except:
            pass
        
        # Open Graph
        og_tags = {
            'og:title': 'og_title',
            'og:description': 'og_description',
            'og:image': 'og_image'
        }
        
        for og_property, attr_name in og_tags.items():
            try:
                element = await playwright_page.query_selector(f'meta[property="{og_property}"]')
                if element:
                    content = await element.get_attribute('content')
                    if content:
                        setattr(page.seo, attr_name, content)
            except:
                pass
        
        # Canonical URL
        try:
            canonical_element = await playwright_page.query_selector('link[rel="canonical"]')
            if canonical_element:
                canonical_href = await canonical_element.get_attribute('href')
                if canonical_href:
                    page.seo.canonical_url = HttpUrl(canonical_href)
        except:
            pass
    
    async def _detect_frameworks(self, playwright_page: PlaywrightPage) -> List[str]:
        """Detect JavaScript frameworks and libraries."""
        frameworks = []
        
        # Check for various frameworks and libraries
        framework_checks = {
            'React': 'window.React',
            'Vue': 'window.Vue',
            'Angular': 'window.ng || window.angular',
            'jQuery': 'window.jQuery || window.$',
            'Next.js': 'window.__NEXT_DATA__',
            'Nuxt.js': 'window.__NUXT__',
            'Svelte': 'window.__SVELTE__',
            'Gatsby': 'window.___gatsby',
            'Alpine.js': 'window.Alpine',
            'Stimulus': 'window.Stimulus',
            'Turbo': 'window.Turbo'
        }
        
        for framework_name, check_script in framework_checks.items():
            try:
                result = await playwright_page.evaluate(f'typeof ({check_script}) !== "undefined"')
                if result:
                    frameworks.append(framework_name)
            except:
                pass
        
        return frameworks
    
    async def _extract_performance_metrics(self, playwright_page: PlaywrightPage) -> Dict[str, Any]:
        """Extract performance metrics using Navigation Timing API."""
        try:
            metrics = await playwright_page.evaluate('''
                () => {
                    const timing = performance.timing;
                    const navigation = performance.getEntriesByType('navigation')[0];
                    
                    return {
                        page_load_time: timing.loadEventEnd - timing.navigationStart,
                        dom_content_loaded: timing.domContentLoadedEventEnd - timing.navigationStart,
                        first_paint: performance.getEntriesByName('first-paint')[0]?.startTime || null,
                        first_contentful_paint: performance.getEntriesByName('first-contentful-paint')[0]?.startTime || null,
                        dom_size: document.querySelectorAll('*').length,
                        script_count: document.querySelectorAll('script').length,
                        stylesheet_count: document.querySelectorAll('link[rel="stylesheet"]').length,
                        image_count: document.querySelectorAll('img').length,
                        resource_count: navigation ? navigation.transferSize : null
                    };
                }
            ''')
            return metrics
        except:
            return {}
    
    async def _extract_dynamic_links(self, page: Page, playwright_page: PlaywrightPage):
        """Extract links from the dynamically rendered page."""
        try:
            links = await playwright_page.evaluate('''
                () => {
                    const links = Array.from(document.querySelectorAll('a[href]'));
                    return links.map(link => ({
                        href: link.href,
                        text: link.textContent.trim()
                    }));
                }
            ''')
            
            for link_data in links:
                href = link_data['href']
                normalized_url = normalize_url(href)
                
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
                    
        except Exception as e:
            page.add_warning(f"Failed to extract dynamic links: {e}")
    
    async def _extract_dynamic_assets(self, page: Page, playwright_page: PlaywrightPage):
        """Extract assets from the dynamically rendered page."""
        try:
            assets = await playwright_page.evaluate('''
                () => {
                    const assets = [];
                    
                    // Images
                    document.querySelectorAll('img[src]').forEach(img => {
                        assets.push({
                            url: img.src,
                            type: 'image',
                            alt_text: img.alt || '',
                            width: img.naturalWidth || null,
                            height: img.naturalHeight || null
                        });
                    });
                    
                    // CSS files
                    document.querySelectorAll('link[rel="stylesheet"][href]').forEach(css => {
                        assets.push({
                            url: css.href,
                            type: 'css'
                        });
                    });
                    
                    // JavaScript files
                    document.querySelectorAll('script[src]').forEach(script => {
                        assets.push({
                            url: script.src,
                            type: 'javascript'
                        });
                    });
                    
                    return assets;
                }
            ''')
            
            for asset_data in assets:
                asset = AssetInfo(
                    url=asset_data['url'],
                    type=asset_data['type'],
                    alt_text=asset_data.get('alt_text', ''),
                )
                
                # Add dimensions for images
                if asset_data['type'] == 'image':
                    width = asset_data.get('width')
                    height = asset_data.get('height')
                    if width and height:
                        asset.dimensions = (width, height)
                
                page.add_asset(asset)
                
        except Exception as e:
            page.add_warning(f"Failed to extract dynamic assets: {e}")