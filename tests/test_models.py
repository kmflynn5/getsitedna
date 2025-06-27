"""Tests for data models."""

import pytest
from datetime import datetime
from pydantic import ValidationError

from src.getsitedna.models.page import Page
from src.getsitedna.models.site import Site
from src.getsitedna.models.schemas import (
    ColorInfo, FontInfo, ComponentSpec, ComponentType,
    AnalysisPhilosophy, TargetFramework, CrawlStatus
)


class TestPage:
    """Test Page model functionality."""
    
    def test_page_creation(self):
        """Test basic page creation."""
        page = Page(url="https://example.com/")
        
        assert str(page.url) == "https://example.com/"
        assert page.status == CrawlStatus.PENDING
        assert page.depth == 0
        assert page.domain == "example.com"
        assert page.path == "/"
    
    def test_page_url_validation(self):
        """Test URL validation and normalization."""
        # Test with protocol
        page1 = Page(url="https://example.com/page")
        assert str(page1.url) == "https://example.com/page"
        
        # Test without protocol (should be added)
        page2 = Page(url="example.com/page")
        assert str(page2.url) == "https://example.com/page"
    
    def test_page_status_tracking(self):
        """Test page status and crawling tracking."""
        page = Page(url="https://example.com/")
        
        assert not page.is_crawled
        assert not page.is_successful
        
        page.mark_crawled(200, "text/html")
        
        assert page.is_crawled
        assert page.is_successful
        assert page.status_code == 200
        assert page.content_type == "text/html"
    
    def test_page_links_management(self):
        """Test adding and managing links."""
        page = Page(url="https://example.com/")
        
        # Add internal links
        page.add_internal_link("https://example.com/about")
        page.add_internal_link("https://example.com/contact")
        
        # Add external links
        page.add_external_link("https://google.com")
        
        assert len(page.internal_links) == 2
        assert len(page.external_links) == 1
        
        # Test duplicate prevention
        page.add_internal_link("https://example.com/about")
        assert len(page.internal_links) == 2  # Should not duplicate
    
    def test_page_error_handling(self):
        """Test error and warning tracking."""
        page = Page(url="https://example.com/")
        
        page.add_error("Test error")
        page.add_warning("Test warning")
        
        assert "Test error" in page.errors
        assert "Test warning" in page.warnings
        
        # Test duplicate prevention
        page.add_error("Test error")
        assert len(page.errors) == 1
    
    def test_page_summary(self):
        """Test page summary generation."""
        page = Page(url="https://example.com/")
        page.title = "Test Page"
        page.mark_crawled(200, "text/html")
        page.add_internal_link("https://example.com/about")
        
        summary = page.get_summary()
        
        assert summary["url"] == "https://example.com/"
        assert summary["title"] == "Test Page"
        assert summary["status"] == "completed"
        assert summary["status_code"] == 200
        assert summary["internal_links_count"] == 1


class TestSite:
    """Test Site model functionality."""
    
    def test_site_creation(self):
        """Test basic site creation."""
        site = Site(base_url="https://example.com")
        
        assert str(site.base_url) == "https://example.com"
        assert site.domain == "example.com"
        assert site.total_pages == 0
    
    def test_site_url_normalization(self):
        """Test URL normalization."""
        # Test with trailing slash removal
        site1 = Site(base_url="https://example.com/")
        assert str(site1.base_url) == "https://example.com"
        
        # Test protocol addition
        site2 = Site(base_url="example.com")
        assert str(site2.base_url) == "https://example.com"
    
    def test_page_management(self):
        """Test adding and managing pages."""
        site = Site(base_url="https://example.com")
        
        page1 = Page(url="https://example.com/")
        page2 = Page(url="https://example.com/about")
        
        site.add_page(page1)
        site.add_page(page2)
        
        assert site.total_pages == 2
        assert site.has_page("https://example.com/")
        assert site.get_page("https://example.com/") == page1
    
    def test_pages_by_depth(self):
        """Test filtering pages by depth."""
        site = Site(base_url="https://example.com")
        
        page1 = Page(url="https://example.com/", depth=0)
        page2 = Page(url="https://example.com/about", depth=1)
        page3 = Page(url="https://example.com/contact", depth=1)
        
        site.add_page(page1)
        site.add_page(page2)
        site.add_page(page3)
        
        depth_0_pages = site.get_pages_by_depth(0)
        depth_1_pages = site.get_pages_by_depth(1)
        
        assert len(depth_0_pages) == 1
        assert len(depth_1_pages) == 2
    
    def test_crawled_pages_filter(self):
        """Test filtering successfully crawled pages."""
        site = Site(base_url="https://example.com")
        
        page1 = Page(url="https://example.com/")
        page1.mark_crawled(200, "text/html")
        
        page2 = Page(url="https://example.com/about")
        page2.mark_crawled(404, "text/html")
        
        page3 = Page(url="https://example.com/contact")
        # Not crawled
        
        site.add_page(page1)
        site.add_page(page2)
        site.add_page(page3)
        
        crawled_pages = site.crawled_pages
        failed_pages = site.failed_pages
        
        assert len(crawled_pages) == 1
        assert len(failed_pages) == 1
        assert crawled_pages[0] == page1
    
    def test_design_system_management(self):
        """Test design system components management."""
        site = Site(base_url="https://example.com")
        
        # Test colors
        color1 = ColorInfo(hex="#ff0000", rgb=(255, 0, 0))
        color2 = ColorInfo(hex="#00ff00", rgb=(0, 255, 0))
        
        site.add_global_color(color1)
        site.add_global_color(color2)
        
        assert len(site.global_color_palette) == 2
        
        # Test duplicate prevention
        site.add_global_color(color1)
        assert len(site.global_color_palette) == 2
        
        # Test fonts
        font1 = FontInfo(family="Arial", weights=[400], sizes=["16px"])
        site.add_global_font(font1)
        
        assert len(site.global_typography) == 1
    
    def test_analysis_completion(self):
        """Test analysis completion tracking."""
        site = Site(base_url="https://example.com")
        
        assert not site.is_analysis_complete
        
        site.mark_analysis_complete()
        
        assert site.is_analysis_complete
        assert site.analysis_completed_at is not None
        assert site.stats.analysis_duration_seconds is not None
    
    def test_site_summary(self):
        """Test site summary generation."""
        site = Site(base_url="https://example.com")
        
        page = Page(url="https://example.com/")
        page.mark_crawled(200, "text/html")
        site.add_page(page)
        
        color = ColorInfo(hex="#ff0000", rgb=(255, 0, 0))
        site.add_global_color(color)
        
        summary = site.get_site_summary()
        
        assert summary["base_url"] == "https://example.com"
        assert summary["domain"] == "example.com"
        assert summary["stats"]["total_pages_discovered"] == 1
        assert summary["global_colors_count"] == 1


class TestSchemas:
    """Test schema models."""
    
    def test_color_info_validation(self):
        """Test ColorInfo validation."""
        # Valid color
        color = ColorInfo(hex="#ff0000", rgb=(255, 0, 0))
        assert color.hex == "#ff0000"
        assert color.rgb == (255, 0, 0)
        
        # Invalid hex format should raise validation error
        with pytest.raises(ValidationError):
            ColorInfo(hex="invalid", rgb=(255, 0, 0))
    
    def test_component_spec(self):
        """Test ComponentSpec creation."""
        component = ComponentSpec(
            component_name="TestComponent",
            component_type=ComponentType.BUTTON,
            design_intent="A test button component"
        )
        
        assert component.component_name == "TestComponent"
        assert component.component_type == ComponentType.BUTTON
        assert component.design_intent == "A test button component"
    
    def test_font_info(self):
        """Test FontInfo model."""
        font = FontInfo(
            family="Arial",
            weights=[400, 700],
            sizes=["14px", "16px", "18px"],
            usage_context=["body", "headings"]
        )
        
        assert font.family == "Arial"
        assert 400 in font.weights
        assert "16px" in font.sizes
        assert "body" in font.usage_context
    
    def test_enum_values(self):
        """Test enum value validation."""
        # Test valid enum values
        assert AnalysisPhilosophy.MODERN_INTERPRETATION.value == "modern_interpretation"
        assert TargetFramework.REACT_NEXTJS.value == "react_nextjs"
        assert ComponentType.HERO.value == "hero"
        assert CrawlStatus.COMPLETED.value == "completed"
    
    def test_default_values(self):
        """Test default values in models."""
        page = Page(url="https://example.com/")
        
        assert page.status == CrawlStatus.PENDING
        assert page.depth == 0
        assert page.errors == []
        assert page.warnings == []
        assert page.internal_links == []
        
        site = Site(base_url="https://example.com")
        
        assert site.pages == {}
        assert site.errors == []
        assert site.global_color_palette == []