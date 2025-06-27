"""Tests for content and design extractors."""

import pytest
from unittest.mock import Mock, patch, mock_open
from bs4 import BeautifulSoup

from src.getsitedna.extractors.content import ContentExtractor
from src.getsitedna.extractors.structure import StructureExtractor
from src.getsitedna.extractors.design import DesignExtractor
from src.getsitedna.processors.html_parser import HTMLParser
from src.getsitedna.models.schemas import ContentType, ComponentType


class TestHTMLParser:
    """Test HTML parsing utilities."""
    
    def test_html_parser_initialization(self, sample_html):
        """Test HTMLParser initialization."""
        parser = HTMLParser(sample_html, "https://example.com")
        
        assert parser.html_content == sample_html
        assert parser.base_url == "https://example.com"
        assert parser.soup is not None
    
    def test_noise_removal(self):
        """Test removal of scripts and comments."""
        html_with_noise = """
        <html>
        <head>
            <script>alert('test');</script>
            <!-- This is a comment -->
            <style>body { color: red; }</style>
        </head>
        <body>
            <h1>Content</h1>
            <script>console.log('more noise');</script>
        </body>
        </html>
        """
        
        parser = HTMLParser(html_with_noise)
        
        # Scripts and comments should be removed
        assert "alert('test')" not in parser.soup.get_text()
        assert "This is a comment" not in str(parser.soup)
        assert parser.soup.find('script') is None
    
    def test_text_content_extraction(self, sample_html):
        """Test text content extraction and categorization."""
        parser = HTMLParser(sample_html)
        content = parser.extract_text_content()
        
        # Check headings
        assert any("Welcome to Test Site" in str(h) for h in content["headings"])
        assert any("Feature 1" in str(h) for h in content["headings"])
        
        # Check navigation
        assert len(content["navigation"]) > 0
        assert any("Home" in nav["text"] for nav in content["navigation"])
        
        # Check buttons
        assert len(content["buttons"]) > 0
        assert any("Get Started" in btn["text"] for btn in content["buttons"])
    
    def test_structural_elements_extraction(self, sample_html):
        """Test structural element extraction."""
        parser = HTMLParser(sample_html)
        structure = parser.extract_structural_elements()
        
        assert structure["header"] is not None
        assert structure["footer"] is not None
        assert structure["layout_type"] in ["modern_single_column", "traditional_layout", "simple_layout"]
    
    def test_form_extraction(self, sample_html):
        """Test form extraction."""
        parser = HTMLParser(sample_html)
        forms = parser.extract_forms()
        
        assert len(forms) == 1
        form = forms[0]
        
        assert form["action"] == "/submit"
        assert form["method"] == "POST"
        assert len(form["fields"]) == 3  # name, email, message
        assert form["submit_text"] == "Send Message"
    
    def test_word_count_and_reading_time(self, sample_html):
        """Test word count and reading time calculation."""
        parser = HTMLParser(sample_html)
        
        word_count = parser.get_page_word_count()
        reading_time = parser.get_reading_time()
        
        assert word_count > 0
        assert reading_time >= 1  # Should be at least 1 minute


class TestContentExtractor:
    """Test content extraction functionality."""
    
    def test_content_extraction(self, sample_page):
        """Test complete content extraction."""
        extractor = ContentExtractor()
        result_page = extractor.extract_content(sample_page)
        
        # Check that content was extracted
        assert ContentType.HEADING in result_page.content.text_content
        assert ContentType.CTA in result_page.content.text_content
        assert ContentType.NAVIGATION in result_page.content.text_content
        
        # Check content structure
        assert "main_topic" in result_page.content.content_structure
        assert "categories" in result_page.content.content_structure
    
    def test_content_categorization(self, sample_page):
        """Test content categorization."""
        extractor = ContentExtractor()
        result_page = extractor.extract_content(sample_page)
        
        categories = result_page.content.content_structure.get("categories", [])
        
        # Should identify at least one category
        assert len(categories) > 0
        assert "general" in categories or any(cat in ["business", "landing_page"] for cat in categories)
    
    def test_form_processing(self, sample_page):
        """Test form processing."""
        extractor = ContentExtractor()
        result_page = extractor.extract_content(sample_page)
        
        assert len(result_page.technical.forms) == 1
        form = result_page.technical.forms[0]
        
        assert form.action == "/submit"
        assert form.method == "POST"
        assert len(form.fields) == 3
    
    def test_content_metrics(self, sample_page):
        """Test content metrics calculation."""
        extractor = ContentExtractor()
        result_page = extractor.extract_content(sample_page)
        
        metrics = result_page.content.content_structure.get("metrics", {})
        
        assert "word_count" in metrics
        assert "reading_time_minutes" in metrics
        assert "heading_count" in metrics
        assert metrics["word_count"] > 0
    
    def test_key_phrases_extraction(self):
        """Test key phrase extraction."""
        extractor = ContentExtractor()
        
        text = "This is a test website for analyzing content and extracting key phrases from web pages"
        phrases = extractor.extract_key_phrases(text, max_phrases=5)
        
        assert len(phrases) > 0
        assert all(len(phrase.split()) in [2, 3] for phrase in phrases)
    
    def test_sentiment_analysis(self):
        """Test basic sentiment analysis."""
        extractor = ContentExtractor()
        
        positive_text = "This is an amazing and wonderful website with excellent features"
        negative_text = "This is a terrible and awful website with horrible problems"
        neutral_text = "This website contains information about various topics"
        
        assert extractor.analyze_content_sentiment(positive_text) == "positive"
        assert extractor.analyze_content_sentiment(negative_text) == "negative"
        assert extractor.analyze_content_sentiment(neutral_text) == "neutral"


class TestStructureExtractor:
    """Test structure extraction functionality."""
    
    def test_structure_extraction(self, sample_page):
        """Test complete structure extraction."""
        extractor = StructureExtractor()
        result_page = extractor.extract_structure(sample_page)
        
        # Check components were identified
        assert len(result_page.structure.components) > 0
        
        # Check layout analysis
        assert result_page.structure.layout_type is not None
        assert result_page.structure.navigation_structure is not None
    
    def test_component_identification(self, sample_page):
        """Test component identification."""
        extractor = StructureExtractor()
        result_page = extractor.extract_structure(sample_page)
        
        components = result_page.structure.components
        component_types = [comp.component_type for comp in components]
        
        # Should identify common components
        assert ComponentType.HEADER in component_types
        assert ComponentType.FOOTER in component_types
        assert ComponentType.FORM in component_types
    
    def test_layout_analysis(self, sample_page):
        """Test layout analysis."""
        extractor = StructureExtractor()
        result_page = extractor.extract_structure(sample_page)
        
        layout_type = result_page.structure.layout_type
        nav_structure = result_page.structure.navigation_structure
        
        assert layout_type in ["traditional_layout", "simple_layout", "modern_single_column"]
        assert "nav_count" in nav_structure
    
    def test_component_deduplication(self):
        """Test component deduplication."""
        extractor = StructureExtractor()
        
        # Create duplicate components
        components = [
            Mock(component_type=ComponentType.HEADER, component_name="Header1"),
            Mock(component_type=ComponentType.HEADER, component_name="Header1"),
            Mock(component_type=ComponentType.FOOTER, component_name="Footer1"),
        ]
        
        deduplicated = extractor._deduplicate_components(components)
        
        assert len(deduplicated) == 2  # Should remove one duplicate


class TestDesignExtractor:
    """Test design extraction functionality."""
    
    def test_design_extraction(self, sample_page):
        """Test complete design extraction."""
        extractor = DesignExtractor()
        result_page = extractor.extract_design(sample_page)
        
        # Check colors were extracted
        assert len(result_page.design.color_palette) > 0
        
        # Check fonts were extracted
        assert len(result_page.design.typography) > 0
    
    def test_color_extraction(self, sample_page):
        """Test color extraction from CSS."""
        extractor = DesignExtractor()
        result_page = extractor.extract_design(sample_page)
        
        colors = result_page.design.color_palette
        
        # Should find colors from the sample HTML
        color_hexes = [color.hex for color in colors]
        assert any("#ff6b6b" in hex_color for hex_color in color_hexes)
        assert any("#4ecdc4" in hex_color for hex_color in color_hexes)
    
    def test_typography_extraction(self, sample_page):
        """Test typography extraction."""
        extractor = DesignExtractor()
        result_page = extractor.extract_design(sample_page)
        
        fonts = result_page.design.typography
        
        # Should find Arial font from sample HTML
        font_families = [font.family for font in fonts]
        assert "Arial" in font_families
    
    def test_hex_to_rgb_conversion(self):
        """Test hex to RGB conversion."""
        extractor = DesignExtractor()
        
        rgb = extractor._hex_to_rgb("#ff6b6b")
        assert rgb == (255, 107, 107)
        
        rgb = extractor._hex_to_rgb("#ffffff")
        assert rgb == (255, 255, 255)
        
        rgb = extractor._hex_to_rgb("#000000")
        assert rgb == (0, 0, 0)
    
    def test_css_color_parsing(self):
        """Test CSS color parsing."""
        extractor = DesignExtractor()
        
        css_content = """
        .header { background-color: #ff0000; color: rgb(255, 255, 255); }
        .footer { background: rgba(0, 255, 0, 0.5); }
        .button { color: #00f; }
        """
        
        colors = extractor._parse_css_colors(css_content, {})
        
        assert "#ff0000" in colors
        assert "#ffffff" in colors
        assert "#00ff00" in colors
        assert "#0000ff" in colors  # #00f should be expanded
    
    def test_css_font_parsing(self):
        """Test CSS font parsing."""
        extractor = DesignExtractor()
        
        css_content = """
        body { font-family: 'Arial', sans-serif; font-size: 16px; }
        h1 { font-family: 'Georgia', serif; font-weight: bold; }
        .title { font-weight: 600; font-size: 24px; }
        """
        
        fonts = extractor._parse_css_fonts(css_content, {})
        
        assert "Arial" in fonts
        assert "Georgia" in fonts
        assert "sans-serif" in fonts
    
    @patch('requests.get')
    def test_external_css_extraction(self, mock_get):
        """Test extraction from external CSS files."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = ".test { color: #ff0000; }"
        mock_get.return_value = mock_response
        
        extractor = DesignExtractor()
        colors = {}
        
        extractor._extract_css_colors("https://example.com/style.css", colors)
        
        assert "#ff0000" in colors
        mock_get.assert_called_once()
    
    def test_global_design_system_analysis(self, populated_site):
        """Test global design system analysis."""
        extractor = DesignExtractor()
        
        # Add colors to pages first
        for page in populated_site.pages.values():
            page.design.color_palette = [
                Mock(hex="#ff0000", frequency=3, usage_context=["header"]),
                Mock(hex="#00ff00", frequency=1, usage_context=["footer"])
            ]
        
        result_site = extractor.analyze_global_design_system(populated_site)
        
        # Should aggregate colors across pages
        assert len(result_site.global_color_palette) > 0