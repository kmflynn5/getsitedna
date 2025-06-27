"""HTML parsing utilities for content extraction."""

import re
from typing import Dict, List, Optional, Set, Tuple
from urllib.parse import urljoin

from bs4 import BeautifulSoup, Tag, NavigableString, Comment


class HTMLParser:
    """Advanced HTML parsing and analysis utilities."""
    
    def __init__(self, html_content: str, base_url: str = ""):
        self.html_content = html_content
        self.base_url = base_url
        self.soup = BeautifulSoup(html_content, 'html.parser')
        self._remove_noise()
    
    def _remove_noise(self):
        """Remove script tags, comments, and other noise from HTML."""
        # Remove scripts and styles
        for tag in self.soup(["script", "style", "noscript"]):
            tag.decompose()
        
        # Remove comments
        for comment in self.soup.find_all(string=lambda text: isinstance(text, Comment)):
            comment.extract()
    
    def extract_text_content(self) -> Dict[str, List[str]]:
        """Extract and categorize text content."""
        content = {
            "headings": [],
            "paragraphs": [],
            "navigation": [],
            "buttons": [],
            "links": [],
            "lists": [],
            "meta_text": [],
        }
        
        # Headings (h1-h6)
        for i in range(1, 7):
            headings = self.soup.find_all(f'h{i}')
            for heading in headings:
                text = self._clean_text(heading.get_text())
                if text:
                    content["headings"].append({
                        "level": i,
                        "text": text,
                        "id": heading.get('id'),
                        "classes": heading.get('class', [])
                    })
        
        # Paragraphs
        paragraphs = self.soup.find_all('p')
        for p in paragraphs:
            text = self._clean_text(p.get_text())
            if text and len(text) > 10:  # Filter out very short paragraphs
                content["paragraphs"].append(text)
        
        # Navigation elements
        nav_elements = self.soup.find_all(['nav', 'menu'])
        nav_elements.extend(self.soup.find_all(class_=re.compile(r'nav|menu|header')))
        for nav in nav_elements:
            links = nav.find_all('a')
            nav_items = []
            for link in links:
                text = self._clean_text(link.get_text())
                if text:
                    nav_items.append({
                        "text": text,
                        "href": link.get('href'),
                        "title": link.get('title')
                    })
            if nav_items:
                content["navigation"].extend(nav_items)
        
        # Buttons and CTAs
        buttons = self.soup.find_all(['button', 'input'])
        buttons.extend(self.soup.find_all('a', class_=re.compile(r'btn|button|cta')))
        for button in buttons:
            text = self._clean_text(button.get_text())
            if not text and button.get('value'):
                text = button['value']
            if not text and button.get('title'):
                text = button['title']
            if text:
                content["buttons"].append({
                    "text": text,
                    "type": button.name,
                    "classes": button.get('class', [])
                })
        
        # Links
        links = self.soup.find_all('a', href=True)
        for link in links:
            text = self._clean_text(link.get_text())
            if text:
                content["links"].append({
                    "text": text,
                    "href": link['href'],
                    "title": link.get('title')
                })
        
        # Lists
        lists = self.soup.find_all(['ul', 'ol'])
        for list_elem in lists:
            items = []
            for li in list_elem.find_all('li'):
                text = self._clean_text(li.get_text())
                if text:
                    items.append(text)
            if items:
                content["lists"].append({
                    "type": list_elem.name,
                    "items": items
                })
        
        return content
    
    def extract_structural_elements(self) -> Dict[str, any]:
        """Extract structural information about the page."""
        structure = {
            "header": None,
            "footer": None,
            "main_content": None,
            "sidebar": None,
            "navigation": [],
            "sections": [],
            "layout_type": "unknown"
        }
        
        # Header
        header = self.soup.find('header')
        if not header:
            header = self.soup.find(class_=re.compile(r'header|top'))
        if header:
            structure["header"] = self._analyze_component(header, "header")
        
        # Footer
        footer = self.soup.find('footer')
        if not footer:
            footer = self.soup.find(class_=re.compile(r'footer|bottom'))
        if footer:
            structure["footer"] = self._analyze_component(footer, "footer")
        
        # Main content
        main = self.soup.find('main')
        if not main:
            main = self.soup.find(class_=re.compile(r'main|content|primary'))
        if main:
            structure["main_content"] = self._analyze_component(main, "main")
        
        # Sidebar
        sidebar = self.soup.find('aside')
        if not sidebar:
            sidebar = self.soup.find(class_=re.compile(r'sidebar|secondary'))
        if sidebar:
            structure["sidebar"] = self._analyze_component(sidebar, "sidebar")
        
        # Navigation
        nav_elements = self.soup.find_all('nav')
        for nav in nav_elements:
            structure["navigation"].append(self._analyze_component(nav, "navigation"))
        
        # Sections
        sections = self.soup.find_all('section')
        for section in sections:
            structure["sections"].append(self._analyze_component(section, "section"))
        
        # Determine layout type
        structure["layout_type"] = self._determine_layout_type()
        
        return structure
    
    def _analyze_component(self, element: Tag, component_type: str) -> Dict[str, any]:
        """Analyze a structural component."""
        return {
            "type": component_type,
            "classes": element.get('class', []),
            "id": element.get('id'),
            "text_content": self._clean_text(element.get_text())[:200],  # First 200 chars
            "child_count": len(element.find_all()),
            "has_form": bool(element.find('form')),
            "has_images": bool(element.find('img')),
            "has_links": bool(element.find('a')),
        }
    
    def _determine_layout_type(self) -> str:
        """Determine the overall layout type of the page."""
        # Look for common layout indicators
        has_sidebar = bool(self.soup.find(['aside']) or 
                          self.soup.find(class_=re.compile(r'sidebar|secondary')))
        
        has_header = bool(self.soup.find('header') or 
                         self.soup.find(class_=re.compile(r'header')))
        
        has_footer = bool(self.soup.find('footer') or 
                         self.soup.find(class_=re.compile(r'footer')))
        
        has_nav = bool(self.soup.find('nav'))
        
        # Check for grid/flexbox layouts
        grid_indicators = self.soup.find_all(class_=re.compile(r'grid|flex|container|row|col'))
        has_modern_layout = len(grid_indicators) > 5
        
        # Determine layout type
        if has_modern_layout:
            if has_sidebar:
                return "modern_with_sidebar"
            else:
                return "modern_single_column"
        elif has_sidebar:
            return "traditional_with_sidebar"
        elif has_header and has_footer and has_nav:
            return "traditional_three_section"
        else:
            return "simple_layout"
    
    def extract_forms(self) -> List[Dict[str, any]]:
        """Extract form information."""
        forms = []
        
        for form in self.soup.find_all('form'):
            form_data = {
                "action": form.get('action', ''),
                "method": form.get('method', 'GET').upper(),
                "fields": [],
                "submit_text": ""
            }
            
            # Extract form fields
            inputs = form.find_all(['input', 'textarea', 'select'])
            for input_elem in inputs:
                field = {
                    "name": input_elem.get('name', ''),
                    "type": input_elem.get('type', input_elem.name),
                    "label": "",
                    "placeholder": input_elem.get('placeholder', ''),
                    "required": input_elem.has_attr('required'),
                    "pattern": input_elem.get('pattern', '')
                }
                
                # Find associated label
                field_id = input_elem.get('id')
                if field_id:
                    label = form.find('label', {'for': field_id})
                    if label:
                        field["label"] = self._clean_text(label.get_text())
                
                if field["type"] != "submit":
                    form_data["fields"].append(field)
                else:
                    form_data["submit_text"] = input_elem.get('value', 'Submit')
            
            # Look for submit button
            submit_button = form.find(['button', 'input'], type='submit')
            if submit_button and not form_data["submit_text"]:
                form_data["submit_text"] = self._clean_text(submit_button.get_text()) or submit_button.get('value', 'Submit')
            
            forms.append(form_data)
        
        return forms
    
    def extract_semantic_content(self) -> Dict[str, any]:
        """Extract semantic content and meaning."""
        semantic = {
            "main_topic": "",
            "key_phrases": [],
            "content_categories": [],
            "call_to_actions": [],
            "value_propositions": [],
        }
        
        # Extract main topic from title and h1
        title = self.soup.find('title')
        h1 = self.soup.find('h1')
        
        if title:
            semantic["main_topic"] = self._clean_text(title.get_text())
        elif h1:
            semantic["main_topic"] = self._clean_text(h1.get_text())
        
        # Extract CTAs
        cta_patterns = [
            r'\b(buy|purchase|order|subscribe|sign up|register|download|get|start|try|learn more|contact)\b',
            r'\b(free trial|demo|quote|consultation)\b'
        ]
        
        for pattern in cta_patterns:
            matches = re.finditer(pattern, self.html_content, re.IGNORECASE)
            for match in matches:
                semantic["call_to_actions"].append(match.group())
        
        # Remove duplicates
        semantic["call_to_actions"] = list(set(semantic["call_to_actions"]))
        
        return semantic
    
    def identify_unique_content(self) -> Dict[str, List[str]]:
        """Identify unique vs boilerplate content."""
        all_text = self._clean_text(self.soup.get_text())
        paragraphs = [self._clean_text(p.get_text()) for p in self.soup.find_all('p')]
        
        # Simple heuristic: content in main/article tags is likely unique
        unique_containers = self.soup.find_all(['main', 'article', 'section'])
        unique_content = []
        
        for container in unique_containers:
            text = self._clean_text(container.get_text())
            if len(text) > 50:  # Filter out short snippets
                unique_content.append(text)
        
        # If no semantic containers, use paragraphs as fallback
        if not unique_content and paragraphs:
            unique_content = [p for p in paragraphs if len(p) > 50]
        
        # Identify potential boilerplate (headers, footers, navigation)
        boilerplate_containers = self.soup.find_all(['header', 'footer', 'nav'])
        boilerplate_content = []
        
        for container in boilerplate_containers:
            text = self._clean_text(container.get_text())
            if text:
                boilerplate_content.append(text)
        
        return {
            "unique": unique_content[:10],  # Limit to first 10 items
            "boilerplate": boilerplate_content
        }
    
    def extract_meta_information(self) -> Dict[str, any]:
        """Extract meta information and structured data."""
        meta_info = {
            "viewport": "",
            "charset": "",
            "robots": "",
            "schema_markup": {},
            "social_meta": {}
        }
        
        # Viewport
        viewport = self.soup.find('meta', attrs={'name': 'viewport'})
        if viewport:
            meta_info["viewport"] = viewport.get('content', '')
        
        # Charset
        charset = self.soup.find('meta', attrs={'charset': True})
        if charset:
            meta_info["charset"] = charset.get('charset', '')
        
        # Robots
        robots = self.soup.find('meta', attrs={'name': 'robots'})
        if robots:
            meta_info["robots"] = robots.get('content', '')
        
        # Schema.org structured data
        scripts = self.soup.find_all('script', type='application/ld+json')
        for script in scripts:
            try:
                import json
                data = json.loads(script.string)
                if isinstance(data, dict) and '@type' in data:
                    meta_info["schema_markup"][data['@type']] = data
            except (json.JSONDecodeError, TypeError):
                pass
        
        # Social media meta tags
        social_tags = ['og:title', 'og:description', 'og:image', 'og:url', 'og:type',
                      'twitter:card', 'twitter:title', 'twitter:description', 'twitter:image']
        
        for tag in social_tags:
            meta_tag = self.soup.find('meta', property=tag) or self.soup.find('meta', attrs={'name': tag})
            if meta_tag:
                meta_info["social_meta"][tag] = meta_tag.get('content', '')
        
        return meta_info
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text content."""
        if not text:
            return ""
        
        # Remove extra whitespace and newlines
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        
        # Remove common unwanted characters
        text = text.replace('\u00a0', ' ')  # Non-breaking space
        text = text.replace('\u200b', '')   # Zero-width space
        
        return text
    
    def get_page_word_count(self) -> int:
        """Get total word count of meaningful content."""
        main_text = self._clean_text(self.soup.get_text())
        words = main_text.split()
        return len(words)
    
    def get_reading_time(self) -> int:
        """Estimate reading time in minutes (assuming 200 WPM)."""
        word_count = self.get_page_word_count()
        return max(1, round(word_count / 200))