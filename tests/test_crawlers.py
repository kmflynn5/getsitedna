"""Tests for crawling functionality."""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import asyncio

from src.getsitedna.crawlers.static_crawler import StaticCrawler
from src.getsitedna.crawlers.dynamic_crawler import DynamicCrawler
from src.getsitedna.models.site import Site
from src.getsitedna.models.page import Page
from src.getsitedna.models.schemas import CrawlStatus
from src.getsitedna.utils.http import HTTPSession, RobotsChecker


class TestStaticCrawler:
    """Test static HTML crawler."""
    
    def test_crawler_initialization(self, sample_site):
        """Test crawler initialization."""
        crawler = StaticCrawler(sample_site)
        
        assert crawler.site == sample_site
        assert crawler.session is not None
        assert crawler.robots_checker is not None
        assert isinstance(crawler.discovered_urls, set)
        assert isinstance(crawler.crawled_urls, set)
    
    @pytest.mark.asyncio
    async def test_discover_initial_urls(self, sample_site):
        """Test initial URL discovery."""
        crawler = StaticCrawler(sample_site)
        
        await crawler._discover_initial_urls()
        
        # Should add base URL
        assert str(sample_site.base_url) in crawler.discovered_urls
        assert sample_site.has_page(str(sample_site.base_url))
    
    def test_add_discovered_url(self, sample_site):
        """Test URL discovery and validation."""
        crawler = StaticCrawler(sample_site)
        
        # Test valid URL
        crawler._add_discovered_url("https://example.com/page1", depth=1)
        assert "https://example.com/page1" in crawler.discovered_urls
        assert sample_site.has_page("https://example.com/page1")
        
        # Test duplicate URL (should not add twice)
        initial_count = len(crawler.discovered_urls)
        crawler._add_discovered_url("https://example.com/page1", depth=1)
        assert len(crawler.discovered_urls) == initial_count
        
        # Test external URL (should not add)
        crawler._add_discovered_url("https://external.com/page", depth=1)
        assert "https://external.com/page" not in crawler.discovered_urls
    
    def test_depth_limit_enforcement(self, sample_site):
        """Test depth limit enforcement."""
        sample_site.config.max_depth = 2
        crawler = StaticCrawler(sample_site)
        
        # Should add URLs within depth limit
        crawler._add_discovered_url("https://example.com/page1", depth=1)
        crawler._add_discovered_url("https://example.com/page2", depth=2)
        assert len(crawler.discovered_urls) == 2
        
        # Should not add URLs beyond depth limit
        crawler._add_discovered_url("https://example.com/page3", depth=3)
        assert len(crawler.discovered_urls) == 2
    
    def test_page_limit_enforcement(self, sample_site):
        """Test page limit enforcement."""
        sample_site.config.max_pages = 2
        crawler = StaticCrawler(sample_site)
        
        # Add URLs up to limit
        crawler._add_discovered_url("https://example.com/page1", depth=1)
        crawler._add_discovered_url("https://example.com/page2", depth=1)
        assert len(crawler.discovered_urls) == 2
        
        # Should not add beyond limit
        crawler._add_discovered_url("https://example.com/page3", depth=1)
        assert len(crawler.discovered_urls) == 2
    
    @patch('src.getsitedna.crawlers.static_crawler.requests')
    def test_sitemap_parsing(self, mock_requests, sample_site):
        """Test XML sitemap parsing."""
        # Mock sitemap XML response
        sitemap_xml = """<?xml version="1.0" encoding="UTF-8"?>
        <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
            <url>
                <loc>https://example.com/</loc>
            </url>
            <url>
                <loc>https://example.com/page1</loc>
            </url>
            <url>
                <loc>https://example.com/page2</loc>
            </url>
        </urlset>"""
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = sitemap_xml.encode()
        mock_requests.get.return_value = mock_response
        
        crawler = StaticCrawler(sample_site)
        
        # Test sitemap parsing
        asyncio.run(crawler._parse_sitemap("https://example.com/sitemap.xml"))
        
        # Should have discovered URLs from sitemap
        assert len(crawler.discovered_urls) > 0
        assert "https://example.com/page1" in crawler.discovered_urls
        assert "https://example.com/page2" in crawler.discovered_urls
    
    def test_link_extraction(self, sample_site, sample_html):
        """Test link extraction from HTML."""
        crawler = StaticCrawler(sample_site)
        
        # Create a page with HTML content
        page = Page(url="https://example.com/")
        page.html_content = sample_html
        
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(sample_html, 'html.parser')
        
        crawler._extract_links(page, soup)
        
        # Should extract internal links
        assert len(page.internal_links) > 0
        
        # Check specific links from sample HTML
        internal_urls = [str(url) for url in page.internal_links]
        assert any("/about" in url for url in internal_urls)
        assert any("/contact" in url for url in internal_urls)
    
    def test_asset_extraction(self, sample_site, sample_html):
        """Test asset extraction from HTML."""
        crawler = StaticCrawler(sample_site)
        
        page = Page(url="https://example.com/")
        page.html_content = sample_html
        
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(sample_html, 'html.parser')
        
        crawler._extract_assets(page, soup)
        
        # Should extract some assets (at least CSS from style tag won't be extracted as external)
        # But we can test the method doesn't crash
        assert isinstance(page.assets, list)
    
    @patch('src.getsitedna.crawlers.static_crawler.HTTPSession')
    @pytest.mark.asyncio
    async def test_crawl_page(self, mock_session_class, sample_site, sample_html):
        """Test crawling a single page."""
        # Mock HTTP session
        mock_session = Mock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = sample_html
        mock_response.headers = {'content-type': 'text/html'}
        mock_session.get = AsyncMock(return_value=mock_response)
        mock_session_class.return_value = mock_session
        
        crawler = StaticCrawler(sample_site)
        crawler.session = mock_session
        
        # Create a page to crawl
        page = Page(url="https://example.com/test")
        
        await crawler._crawl_page(page)
        
        # Check page was processed
        assert page.status == CrawlStatus.COMPLETED
        assert page.html_content == sample_html
        assert page.title is not None


class TestDynamicCrawler:
    """Test dynamic content crawler."""
    
    def test_crawler_initialization(self, sample_site):
        """Test dynamic crawler initialization."""
        crawler = DynamicCrawler(sample_site)
        
        assert crawler.site == sample_site
        assert isinstance(crawler.discovered_urls, set)
        assert isinstance(crawler.crawled_urls, set)
        assert isinstance(crawler.network_requests, dict)
    
    @pytest.mark.asyncio
    async def test_crawl_site_structure(self, sample_site):
        """Test the overall crawl site structure."""
        with patch('src.getsitedna.crawlers.dynamic_crawler.async_playwright') as mock_playwright:
            # Mock playwright context
            mock_context = AsyncMock()
            mock_browser = AsyncMock()
            mock_p = AsyncMock()
            mock_browser_type = AsyncMock()
            
            mock_browser_type.launch.return_value = mock_browser
            mock_browser.new_context.return_value = mock_context
            mock_p.chromium = mock_browser_type
            mock_playwright.return_value.__aenter__.return_value = mock_p
            
            crawler = DynamicCrawler(sample_site)
            
            # Mock the discovery and crawling methods
            crawler._discover_initial_urls = AsyncMock()
            crawler._crawl_by_depth = AsyncMock()
            
            result = await crawler.crawl_site()
            
            # Verify methods were called
            crawler._discover_initial_urls.assert_called_once()
            crawler._crawl_by_depth.assert_called_once()
            assert result == sample_site
    
    def test_request_handling(self, sample_site):
        """Test request interception for API discovery."""
        crawler = DynamicCrawler(sample_site)
        
        # Mock request object
        mock_request = Mock()
        mock_request.url = "https://example.com/api/data"
        mock_frame = Mock()
        mock_frame.url = "https://example.com/page"
        mock_request.frame = mock_frame
        
        # Test API request detection
        asyncio.run(crawler._handle_request(mock_request))
        
        # Should track API requests
        assert "https://example.com/page" in crawler.network_requests
        assert "https://example.com/api/data" in crawler.network_requests["https://example.com/page"]
    
    @pytest.mark.asyncio
    async def test_framework_detection(self, mock_playwright_page):
        """Test JavaScript framework detection."""
        crawler = DynamicCrawler(Site(base_url="https://example.com"))
        
        # Mock framework detection
        mock_playwright_page.evaluate.side_effect = [
            True,   # React detected
            False,  # Vue not detected
            False,  # Angular not detected
            True,   # jQuery detected
        ]
        
        frameworks = await crawler._detect_frameworks(mock_playwright_page)
        
        assert "React" in frameworks
        assert "jQuery" in frameworks
        assert "Vue" not in frameworks
    
    @pytest.mark.asyncio
    async def test_performance_metrics_extraction(self, mock_playwright_page):
        """Test performance metrics extraction."""
        crawler = DynamicCrawler(Site(base_url="https://example.com"))
        
        # Mock performance metrics
        expected_metrics = {
            "page_load_time": 1200,
            "dom_content_loaded": 800,
            "first_paint": 600,
            "dom_size": 150
        }
        mock_playwright_page.evaluate.return_value = expected_metrics
        
        metrics = await crawler._extract_performance_metrics(mock_playwright_page)
        
        assert metrics == expected_metrics
        assert metrics["page_load_time"] == 1200
        assert metrics["dom_size"] == 150
    
    @pytest.mark.asyncio
    async def test_dynamic_content_extraction(self, mock_playwright_page):
        """Test dynamic content extraction after JS execution."""
        crawler = DynamicCrawler(Site(base_url="https://example.com"))
        page = Page(url="https://example.com/test")
        
        # Mock playwright page methods
        mock_playwright_page.content.return_value = "<html><body><h1>Rendered Content</h1></body></html>"
        mock_playwright_page.title.return_value = "Test Page"
        
        await crawler._extract_dynamic_content(page, mock_playwright_page)
        
        assert page.rendered_html == "<html><body><h1>Rendered Content</h1></body></html>"
        assert page.title == "Test Page"
        assert page.html_content == page.rendered_html


class TestHTTPUtilities:
    """Test HTTP utilities and rate limiting."""
    
    def test_rate_limiter(self):
        """Test rate limiter functionality."""
        from src.getsitedna.utils.http import RateLimiter
        import time
        
        limiter = RateLimiter(delay=0.1)  # 100ms delay
        
        start_time = time.time()
        
        # First request should be immediate
        asyncio.run(limiter.wait())
        first_request_time = time.time() - start_time
        
        # Second request should be delayed
        asyncio.run(limiter.wait())
        second_request_time = time.time() - start_time
        
        assert first_request_time < 0.05  # Should be almost immediate
        assert second_request_time >= 0.1  # Should be delayed
    
    @patch('src.getsitedna.utils.http.requests.Session')
    def test_http_session_retry(self, mock_session_class):
        """Test HTTP session retry logic."""
        from src.getsitedna.utils.http import HTTPSession
        
        mock_session = Mock()
        mock_session_class.return_value = mock_session
        
        http_session = HTTPSession(rate_limit_delay=0.1, timeout=5)
        
        # Verify session was configured
        assert http_session.timeout == 5
        assert http_session.rate_limiter.delay == 0.1
    
    def test_robots_checker_initialization(self):
        """Test robots.txt checker initialization."""
        checker = RobotsChecker("https://example.com")
        
        assert checker.base_url == "https://example.com"
        assert checker.user_agent == "*"
        assert not checker._loaded
    
    @patch('urllib.robotparser.RobotFileParser.read')
    def test_robots_txt_loading(self, mock_read):
        """Test robots.txt loading."""
        checker = RobotsChecker("https://example.com")
        
        # Mock successful loading
        mock_read.return_value = None
        result = checker.load_robots_txt()
        
        assert result is True
        assert checker._loaded is True
    
    @patch('urllib.robotparser.RobotFileParser.can_fetch')
    @patch('urllib.robotparser.RobotFileParser.read')
    def test_can_fetch_check(self, mock_read, mock_can_fetch):
        """Test URL fetch permission checking."""
        checker = RobotsChecker("https://example.com")
        
        # Mock robots.txt loaded
        mock_read.return_value = None
        mock_can_fetch.return_value = True
        
        checker.load_robots_txt()
        result = checker.can_fetch("https://example.com/page")
        
        assert result is True
        mock_can_fetch.assert_called_with("*", "https://example.com/page")
    
    def test_can_fetch_without_loading(self):
        """Test can_fetch when robots.txt is not loaded."""
        checker = RobotsChecker("https://example.com")
        
        # Should default to allowing when robots.txt not loaded
        result = checker.can_fetch("https://example.com/page")
        assert result is True