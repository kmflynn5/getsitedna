"""Content extraction and analysis module."""

import re
from typing import Dict, List, Optional, Set, Any
from collections import Counter

from bs4 import BeautifulSoup

from ..models.page import Page
from ..models.schemas import ContentType, FormField, FormInfo
from ..processors.html_parser import HTMLParser


class ContentExtractor:
    """Extract and analyze page content."""
    
    def __init__(self):
        self.stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with',
            'by', 'from', 'up', 'about', 'into', 'through', 'during', 'before', 'after',
            'above', 'below', 'between', 'among', 'is', 'are', 'was', 'were', 'be', 'been',
            'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
            'should', 'may', 'might', 'must', 'can', 'this', 'that', 'these', 'those'
        }
    
    def extract_content(self, page: Page) -> Page:
        """Extract all content from a page."""
        if not page.html_content:
            page.add_warning("No HTML content available for content extraction")
            return page
        
        parser = HTMLParser(page.html_content, str(page.url))
        
        # Extract text content
        text_content = parser.extract_text_content()
        self._categorize_content(page, text_content)
        
        # Extract structural information
        structure = parser.extract_structural_elements()
        self._analyze_structure(page, structure)
        
        # Extract forms
        forms = parser.extract_forms()
        self._process_forms(page, forms)
        
        # Extract semantic content
        semantic = parser.extract_semantic_content()
        self._analyze_semantic_content(page, semantic)
        
        # Identify unique vs boilerplate content
        content_analysis = parser.identify_unique_content()
        self._classify_content_uniqueness(page, content_analysis)
        
        # Extract meta information
        meta_info = parser.extract_meta_information()
        self._process_meta_information(page, meta_info)
        
        # Calculate content metrics
        self._calculate_content_metrics(page, parser)
        
        return page
    
    def _categorize_content(self, page: Page, text_content: Dict[str, Any]):
        """Categorize extracted text content."""
        # Process headings
        headings = []
        for heading_data in text_content.get("headings", []):
            headings.append(heading_data["text"])
        page.content.text_content[ContentType.HEADING] = headings
        
        # Process paragraphs as body text
        paragraphs = text_content.get("paragraphs", [])
        page.content.text_content[ContentType.BODY_TEXT] = paragraphs
        
        # Process navigation
        nav_items = []
        for nav_data in text_content.get("navigation", []):
            nav_items.append(nav_data["text"])
        page.content.text_content[ContentType.NAVIGATION] = nav_items
        
        # Process buttons as CTAs
        cta_texts = []
        for button_data in text_content.get("buttons", []):
            cta_texts.append(button_data["text"])
        page.content.text_content[ContentType.CTA] = cta_texts
    
    def _analyze_structure(self, page: Page, structure: Dict[str, Any]):
        """Analyze page structure."""
        from ..models.schemas import ComponentSpec, ComponentType
        
        # Identify main components
        components = []
        
        if structure.get("header"):
            component = ComponentSpec(
                component_name="Header",
                component_type=ComponentType.HEADER,
                design_intent="Main page header with navigation and branding"
            )
            components.append(component)
        
        if structure.get("footer"):
            component = ComponentSpec(
                component_name="Footer",
                component_type=ComponentType.FOOTER,
                design_intent="Page footer with links and additional information"
            )
            components.append(component)
        
        if structure.get("navigation"):
            for i, nav in enumerate(structure["navigation"]):
                component = ComponentSpec(
                    component_name=f"Navigation_{i+1}",
                    component_type=ComponentType.NAVIGATION,
                    design_intent="Site navigation menu"
                )
                components.append(component)
        
        page.structure.components = components
        page.structure.layout_type = structure.get("layout_type", "unknown")
        
        # Analyze navigation structure
        nav_structure = {}
        if structure.get("navigation"):
            nav_structure["primary_nav"] = len(structure["navigation"]) > 0
            nav_structure["nav_count"] = len(structure["navigation"])
        
        page.structure.navigation_structure = nav_structure
    
    def _process_forms(self, page: Page, forms: List[Dict[str, Any]]):
        """Process form information."""
        for form_data in forms:
            form_fields = []
            
            for field_data in form_data.get("fields", []):
                form_field = FormField(
                    name=field_data.get("name", ""),
                    type=field_data.get("type", "text"),
                    label=field_data.get("label", ""),
                    placeholder=field_data.get("placeholder", ""),
                    required=field_data.get("required", False),
                    validation_pattern=field_data.get("pattern", "")
                )
                form_fields.append(form_field)
            
            form_info = FormInfo(
                action=form_data.get("action", ""),
                method=form_data.get("method", "GET"),
                fields=form_fields,
                submit_text=form_data.get("submit_text", "")
            )
            
            page.technical.forms.append(form_info)
    
    def _analyze_semantic_content(self, page: Page, semantic: Dict[str, Any]):
        """Analyze semantic content and meaning."""
        # Extract key topics and themes
        main_topic = semantic.get("main_topic", "")
        if main_topic:
            page.content.content_structure["main_topic"] = main_topic
        
        # Analyze call-to-actions
        ctas = semantic.get("call_to_actions", [])
        if ctas:
            page.content.content_structure["primary_ctas"] = ctas[:5]  # Top 5 CTAs
        
        # Content categorization based on patterns
        content_categories = self._identify_content_categories(page)
        page.content.content_structure["categories"] = content_categories
    
    def _identify_content_categories(self, page: Page) -> List[str]:
        """Identify content categories based on text analysis."""
        categories = []
        
        # Get all text content
        all_text = ""
        for content_list in page.content.text_content.values():
            all_text += " ".join(content_list) + " "
        
        all_text = all_text.lower()
        
        # Business/Commercial indicators
        business_keywords = ['business', 'company', 'service', 'product', 'buy', 'price', 'cost', 'sale']
        if any(keyword in all_text for keyword in business_keywords):
            categories.append("business")
        
        # Blog/Content indicators
        blog_keywords = ['blog', 'article', 'post', 'read more', 'author', 'published', 'comments']
        if any(keyword in all_text for keyword in blog_keywords):
            categories.append("blog")
        
        # E-commerce indicators
        ecommerce_keywords = ['cart', 'checkout', 'shipping', 'payment', 'order', 'shop', 'store']
        if any(keyword in all_text for keyword in ecommerce_keywords):
            categories.append("ecommerce")
        
        # Portfolio/Creative indicators
        portfolio_keywords = ['portfolio', 'gallery', 'work', 'project', 'design', 'creative']
        if any(keyword in all_text for keyword in portfolio_keywords):
            categories.append("portfolio")
        
        # Landing page indicators
        landing_keywords = ['sign up', 'get started', 'free trial', 'demo', 'contact us']
        if any(keyword in all_text for keyword in landing_keywords):
            categories.append("landing_page")
        
        # News/Media indicators
        news_keywords = ['news', 'breaking', 'report', 'journalist', 'press', 'media']
        if any(keyword in all_text for keyword in news_keywords):
            categories.append("news")
        
        return categories if categories else ["general"]
    
    def _classify_content_uniqueness(self, page: Page, content_analysis: Dict[str, List[str]]):
        """Classify content as unique or boilerplate."""
        page.content.unique_copy = content_analysis.get("unique", [])
        page.content.boilerplate_text = content_analysis.get("boilerplate", [])
        
        # Calculate uniqueness ratio
        unique_length = sum(len(text) for text in page.content.unique_copy)
        boilerplate_length = sum(len(text) for text in page.content.boilerplate_text)
        total_length = unique_length + boilerplate_length
        
        if total_length > 0:
            uniqueness_ratio = unique_length / total_length
            page.content.content_structure["uniqueness_ratio"] = uniqueness_ratio
    
    def _process_meta_information(self, page: Page, meta_info: Dict[str, Any]):
        """Process meta information and structured data."""
        # Update SEO metadata
        social_meta = meta_info.get("social_meta", {})
        
        # Update schema markup
        schema_markup = meta_info.get("schema_markup", {})
        page.seo.schema_markup = schema_markup
        
        # Store additional meta information
        page.content.content_structure["meta_info"] = {
            "viewport": meta_info.get("viewport", ""),
            "charset": meta_info.get("charset", ""),
            "robots": meta_info.get("robots", "")
        }
    
    def _calculate_content_metrics(self, page: Page, parser: HTMLParser):
        """Calculate content quality and readability metrics."""
        metrics = {}
        
        # Word count
        word_count = parser.get_page_word_count()
        metrics["word_count"] = word_count
        
        # Reading time
        reading_time = parser.get_reading_time()
        metrics["reading_time_minutes"] = reading_time
        
        # Content density (words per HTML element)
        soup = BeautifulSoup(page.html_content, 'html.parser')
        element_count = len(soup.find_all())
        if element_count > 0:
            metrics["content_density"] = word_count / element_count
        
        # Heading structure score
        headings = page.content.text_content.get(ContentType.HEADING, [])
        metrics["heading_count"] = len(headings)
        
        # Calculate heading hierarchy score
        if page.html_content:
            h1_count = len(soup.find_all('h1'))
            h2_count = len(soup.find_all('h2'))
            h3_count = len(soup.find_all('h3'))
            
            # Good hierarchy: 1 h1, multiple h2s, some h3s
            hierarchy_score = 1.0
            if h1_count != 1:
                hierarchy_score *= 0.7  # Penalize for not having exactly 1 h1
            if h2_count < 2:
                hierarchy_score *= 0.8  # Penalize for too few h2s
            if h3_count > h2_count * 2:
                hierarchy_score *= 0.9  # Penalize for too many h3s relative to h2s
            
            metrics["heading_hierarchy_score"] = hierarchy_score
        
        # Link density
        links = page.content.text_content.get(ContentType.NAVIGATION, [])
        if word_count > 0:
            metrics["link_density"] = len(page.internal_links + page.external_links) / word_count
        
        # Content-to-code ratio
        if page.html_content:
            content_length = len(parser._clean_text(soup.get_text()))
            html_length = len(page.html_content)
            if html_length > 0:
                metrics["content_to_code_ratio"] = content_length / html_length
        
        page.content.content_structure["metrics"] = metrics
    
    def extract_key_phrases(self, text: str, max_phrases: int = 10) -> List[str]:
        """Extract key phrases from text content."""
        if not text:
            return []
        
        # Clean and tokenize
        text = re.sub(r'[^\w\s]', ' ', text.lower())
        words = text.split()
        
        # Remove stop words
        meaningful_words = [word for word in words if word not in self.stop_words and len(word) > 2]
        
        # Generate 2-3 word phrases
        phrases = []
        for i in range(len(meaningful_words) - 1):
            two_word = f"{meaningful_words[i]} {meaningful_words[i+1]}"
            phrases.append(two_word)
            
            if i < len(meaningful_words) - 2:
                three_word = f"{meaningful_words[i]} {meaningful_words[i+1]} {meaningful_words[i+2]}"
                phrases.append(three_word)
        
        # Count frequency and return top phrases
        phrase_counts = Counter(phrases)
        return [phrase for phrase, count in phrase_counts.most_common(max_phrases)]
    
    def analyze_content_sentiment(self, text: str) -> str:
        """Basic sentiment analysis of content."""
        if not text:
            return "neutral"
        
        text = text.lower()
        
        positive_words = [
            'great', 'excellent', 'amazing', 'wonderful', 'fantastic', 'outstanding',
            'perfect', 'best', 'love', 'awesome', 'brilliant', 'superb', 'exceptional'
        ]
        
        negative_words = [
            'terrible', 'awful', 'horrible', 'bad', 'worst', 'hate', 'disappointing',
            'poor', 'failed', 'problem', 'issue', 'difficult', 'hard', 'struggle'
        ]
        
        positive_count = sum(1 for word in positive_words if word in text)
        negative_count = sum(1 for word in negative_words if word in text)
        
        if positive_count > negative_count:
            return "positive"
        elif negative_count > positive_count:
            return "negative"
        else:
            return "neutral"