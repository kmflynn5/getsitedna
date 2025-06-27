"""Shared test fixtures and configuration."""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, AsyncMock
import json

from src.getsitedna.models.site import Site
from src.getsitedna.models.page import Page
from src.getsitedna.models.schemas import (
    AnalysisMetadata, CrawlConfig, ComponentSpec, ComponentType,
    ColorInfo, FontInfo, ExperiencePattern
)


@pytest.fixture
def sample_html():
    """Sample HTML content for testing."""
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <title>Test Page</title>
        <meta name="description" content="A test page for GetSiteDNA">
        <meta name="keywords" content="test, getsitedna, analysis">
        <style>
            .hero { background-color: #ff6b6b; color: #ffffff; }
            .card { background-color: #4ecdc4; }
            body { font-family: 'Arial', sans-serif; }
        </style>
    </head>
    <body>
        <header class="header">
            <nav class="navigation">
                <ul>
                    <li><a href="/">Home</a></li>
                    <li><a href="/about">About</a></li>
                    <li><a href="/contact">Contact</a></li>
                </ul>
            </nav>
        </header>
        
        <main>
            <section class="hero">
                <h1>Welcome to Test Site</h1>
                <p>This is a test page for analyzing website structure.</p>
                <button class="cta-button">Get Started</button>
            </section>
            
            <section class="features">
                <div class="card">
                    <h2>Feature 1</h2>
                    <p>Description of feature 1</p>
                </div>
                <div class="card">
                    <h2>Feature 2</h2>
                    <p>Description of feature 2</p>
                </div>
            </section>
            
            <form class="contact-form" action="/submit" method="post">
                <input type="text" name="name" placeholder="Your Name" required>
                <input type="email" name="email" placeholder="Your Email" required>
                <textarea name="message" placeholder="Your Message"></textarea>
                <button type="submit">Send Message</button>
            </form>
        </main>
        
        <footer class="footer">
            <p>&copy; 2025 Test Site. All rights reserved.</p>
        </footer>
    </body>
    </html>
    """


@pytest.fixture
def sample_page(sample_html):
    """Create a sample Page object for testing."""
    page = Page(url="https://example.com/")
    page.html_content = sample_html
    page.title = "Test Page"
    page.status_code = 200
    page.content_type = "text/html"
    page.mark_crawled(200, "text/html")
    return page


@pytest.fixture
def sample_site():
    """Create a sample Site object for testing."""
    site = Site(base_url="https://example.com")
    site.config = CrawlConfig()
    site.metadata = AnalysisMetadata()
    return site


@pytest.fixture
def populated_site(sample_site, sample_page):
    """Create a site with sample pages and data."""
    site = sample_site
    
    # Add sample page
    site.add_page(sample_page)
    
    # Add some sample components
    hero_component = ComponentSpec(
        component_name="HeroSection",
        component_type=ComponentType.HERO,
        design_intent="Main hero section with call-to-action"
    )
    site.add_component_spec(hero_component)
    
    # Add sample colors
    primary_color = ColorInfo(
        hex="#ff6b6b",
        rgb=(255, 107, 107),
        usage_context=["hero", "buttons"],
        frequency=5
    )
    site.add_global_color(primary_color)
    
    # Add sample fonts
    primary_font = FontInfo(
        family="Arial",
        weights=[400, 700],
        sizes=["16px", "24px", "32px"],
        usage_context=["body", "headings"]
    )
    site.add_global_font(primary_font)
    
    # Add sample experience pattern
    hero_pattern = ExperiencePattern(
        pattern_name="Hero Section",
        original_intent="Capture attention and communicate value proposition",
        modern_implementation={"responsive": True, "performance": "optimized"},
        user_benefit="Clear value communication",
        technical_requirements=["responsive design", "performance optimization"]
    )
    site.add_experience_pattern(hero_pattern)
    
    return site


@pytest.fixture
def temp_directory():
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def mock_requests():
    """Mock requests for HTTP calls."""
    mock = Mock()
    mock.get.return_value.status_code = 200
    mock.get.return_value.text = """
    <html>
        <head><title>Mock Page</title></head>
        <body><h1>Mock Content</h1></body>
    </html>
    """
    mock.get.return_value.headers = {'content-type': 'text/html'}
    return mock


@pytest.fixture
def mock_playwright_page():
    """Mock Playwright page for browser automation tests."""
    mock_page = AsyncMock()
    mock_page.goto.return_value.status = 200
    mock_page.title.return_value = "Mock Page Title"
    mock_page.content.return_value = """
    <html>
        <head><title>Mock Page Title</title></head>
        <body><h1>Mock Content</h1></body>
    </html>
    """
    mock_page.evaluate.return_value = {
        "page_load_time": 1200,
        "dom_content_loaded": 800,
        "dom_size": 150
    }
    return mock_page


@pytest.fixture
def sample_json_output():
    """Sample JSON output for validation testing."""
    return {
        "metadata": {
            "analysis_philosophy": "modern_interpretation",
            "target_framework": "react_nextjs",
            "analysis_date": "2025-01-01T12:00:00",
            "base_url": "https://example.com"
        },
        "design_intent": {
            "brand_personality": ["modern", "professional"],
            "user_experience_goals": ["clear navigation", "fast loading"]
        },
        "component_specifications": [
            {
                "component_name": "Header",
                "component_type": "header",
                "design_intent": "Site navigation and branding"
            }
        ],
        "design_system": {
            "color_palette": [
                {"hex": "#ff6b6b", "rgb": [255, 107, 107]}
            ],
            "typography": [
                {"family": "Arial", "weights": [400, 700]}
            ]
        }
    }


@pytest.fixture
def create_test_files():
    """Factory function to create test files in a directory."""
    def _create_files(directory: Path, files: dict):
        """Create files with given content in directory."""
        directory.mkdir(parents=True, exist_ok=True)
        
        for filename, content in files.items():
            file_path = directory / filename
            
            if isinstance(content, dict):
                # JSON content
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(content, f, indent=2)
            else:
                # Text content
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
    
    return _create_files


@pytest.fixture(autouse=True)
def reset_global_state():
    """Reset any global state before each test."""
    # Reset error handler state if needed
    from src.getsitedna.utils.error_handling import default_error_handler
    default_error_handler.error_stats = {
        "total_errors": 0,
        "by_category": {},
        "by_severity": {},
        "recent_errors": []
    }
    
    yield
    
    # Cleanup after test if needed