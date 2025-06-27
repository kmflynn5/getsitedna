"""Structure extraction and analysis module."""

import re
from typing import Dict, List, Optional, Set, Any, Tuple
from collections import defaultdict

from bs4 import BeautifulSoup, Tag

from ..models.page import Page
from ..models.schemas import ComponentSpec, ComponentType


class StructureExtractor:
    """Extract and analyze page structure and layout."""
    
    def __init__(self):
        self.component_patterns = {
            ComponentType.HEADER: [
                r'header', r'top', r'banner', r'masthead', r'site-header'
            ],
            ComponentType.FOOTER: [
                r'footer', r'bottom', r'site-footer', r'page-footer'
            ],
            ComponentType.NAVIGATION: [
                r'nav', r'menu', r'navbar', r'navigation', r'main-nav'
            ],
            ComponentType.HERO: [
                r'hero', r'banner', r'jumbotron', r'intro', r'splash'
            ],
            ComponentType.SIDEBAR: [
                r'sidebar', r'aside', r'secondary', r'widget'
            ],
            ComponentType.CARD: [
                r'card', r'item', r'post', r'article-card', r'product'
            ],
            ComponentType.BUTTON: [
                r'btn', r'button', r'cta', r'action'
            ],
            ComponentType.FORM: [
                r'form', r'contact', r'signup', r'login', r'search'
            ],
            ComponentType.MODAL: [
                r'modal', r'popup', r'dialog', r'overlay'
            ],
            ComponentType.CAROUSEL: [
                r'carousel', r'slider', r'slideshow', r'gallery'
            ]
        }
    
    def extract_structure(self, page: Page) -> Page:
        """Extract structural information from a page."""
        if not page.html_content:
            page.add_warning("No HTML content available for structure extraction")
            return page
        
        soup = BeautifulSoup(page.html_content, 'html.parser')
        
        # Identify components
        components = self._identify_components(soup)
        page.structure.components = components
        
        # Analyze layout
        layout_info = self._analyze_layout(soup)
        page.structure.layout_type = layout_info["type"]
        page.structure.grid_system = layout_info.get("grid_system")
        page.structure.responsive_breakpoints = layout_info.get("breakpoints", [])
        
        # Analyze navigation structure
        nav_structure = self._analyze_navigation(soup)
        page.structure.navigation_structure = nav_structure
        
        return page
    
    def _identify_components(self, soup: BeautifulSoup) -> List[ComponentSpec]:
        """Identify UI components on the page."""
        components = []
        
        # Find semantic HTML elements first
        semantic_components = self._find_semantic_components(soup)
        components.extend(semantic_components)
        
        # Find components by class patterns
        pattern_components = self._find_pattern_components(soup)
        components.extend(pattern_components)
        
        # Find interactive components
        interactive_components = self._find_interactive_components(soup)
        components.extend(interactive_components)
        
        # Remove duplicates and return
        return self._deduplicate_components(components)
    
    def _find_semantic_components(self, soup: BeautifulSoup) -> List[ComponentSpec]:
        """Find components using semantic HTML elements."""
        components = []
        
        # Header
        header = soup.find('header')
        if header:
            components.append(ComponentSpec(
                component_name="MainHeader",
                component_type=ComponentType.HEADER,
                design_intent="Primary page header with site branding and navigation",
                modern_features={
                    "sticky_behavior": "auto-hide on scroll",
                    "responsive_design": "mobile-first navigation"
                }
            ))
        
        # Footer
        footer = soup.find('footer')
        if footer:
            components.append(ComponentSpec(
                component_name="MainFooter",
                component_type=ComponentType.FOOTER,
                design_intent="Site footer with links, contact info, and legal information",
                modern_features={
                    "responsive_layout": "stacked on mobile",
                    "accessibility": "proper semantic structure"
                }
            ))
        
        # Navigation
        nav_elements = soup.find_all('nav')
        for i, nav in enumerate(nav_elements):
            components.append(ComponentSpec(
                component_name=f"Navigation_{i+1}",
                component_type=ComponentType.NAVIGATION,
                design_intent="Site navigation menu for user wayfinding",
                modern_features={
                    "keyboard_navigation": "full keyboard support",
                    "mobile_menu": "collapsible hamburger menu"
                }
            ))
        
        # Main content
        main = soup.find('main')
        if main:
            # Analyze main content for hero sections
            hero_indicators = main.find_all(class_=re.compile(r'hero|banner|jumbotron'))
            if hero_indicators:
                components.append(ComponentSpec(
                    component_name="HeroSection",
                    component_type=ComponentType.HERO,
                    design_intent="Primary hero section to capture attention and communicate value",
                    modern_features={
                        "responsive_images": "optimized for all screen sizes",
                        "performance": "above-the-fold optimization"
                    }
                ))
        
        # Aside/Sidebar
        aside_elements = soup.find_all('aside')
        for i, aside in enumerate(aside_elements):
            components.append(ComponentSpec(
                component_name=f"Sidebar_{i+1}",
                component_type=ComponentType.SIDEBAR,
                design_intent="Secondary content area for additional information",
                modern_features={
                    "responsive_behavior": "reorders below main content on mobile"
                }
            ))
        
        # Articles (can be cards)
        articles = soup.find_all('article')
        if len(articles) > 1:  # Multiple articles suggest a card layout
            components.append(ComponentSpec(
                component_name="ArticleCards",
                component_type=ComponentType.CARD,
                design_intent="Content cards displaying article previews or product information",
                modern_features={
                    "grid_layout": "responsive CSS Grid",
                    "hover_effects": "subtle animations and state changes"
                }
            ))
        
        return components
    
    def _find_pattern_components(self, soup: BeautifulSoup) -> List[ComponentSpec]:
        """Find components using class name patterns."""
        components = []
        
        for component_type, patterns in self.component_patterns.items():
            found_elements = []
            
            for pattern in patterns:
                # Find by class name
                elements = soup.find_all(class_=re.compile(pattern, re.IGNORECASE))
                found_elements.extend(elements)
                
                # Find by id
                elements = soup.find_all(id=re.compile(pattern, re.IGNORECASE))
                found_elements.extend(elements)
            
            # Create component specs for found elements
            for i, element in enumerate(found_elements[:3]):  # Limit to 3 per type
                component_name = f"{component_type.value.title()}_{i+1}"
                
                intent = self._generate_component_intent(component_type, element)
                features = self._analyze_component_features(element)
                
                components.append(ComponentSpec(
                    component_name=component_name,
                    component_type=component_type,
                    design_intent=intent,
                    modern_features=features
                ))
        
        return components
    
    def _find_interactive_components(self, soup: BeautifulSoup) -> List[ComponentSpec]:
        """Find interactive components like forms, buttons, modals."""
        components = []
        
        # Forms
        forms = soup.find_all('form')
        for i, form in enumerate(forms):
            form_purpose = self._determine_form_purpose(form)
            components.append(ComponentSpec(
                component_name=f"Form_{form_purpose}",
                component_type=ComponentType.FORM,
                design_intent=f"User input form for {form_purpose} functionality",
                modern_features={
                    "validation": "real-time client-side validation",
                    "accessibility": "proper labels and error handling",
                    "ux": "progressive enhancement"
                }
            ))
        
        # Buttons (excluding those already in forms)
        buttons = soup.find_all(['button', 'input'])
        button_count = 0
        for button in buttons:
            if button.find_parent('form'):
                continue  # Skip buttons inside forms
            
            button_count += 1
            if button_count <= 3:  # Limit to 3 standalone buttons
                components.append(ComponentSpec(
                    component_name=f"ActionButton_{button_count}",
                    component_type=ComponentType.BUTTON,
                    design_intent="Interactive button for user actions",
                    modern_features={
                        "states": "hover, focus, active, disabled states",
                        "accessibility": "keyboard navigation and screen reader support"
                    }
                ))
        
        # Carousels/Sliders
        carousel_indicators = soup.find_all(class_=re.compile(r'carousel|slider|slideshow'))
        if carousel_indicators:
            components.append(ComponentSpec(
                component_name="ImageCarousel",
                component_type=ComponentType.CAROUSEL,
                design_intent="Image or content carousel for showcasing multiple items",
                modern_features={
                    "touch_gestures": "swipe support on mobile",
                    "accessibility": "keyboard navigation and screen reader announcements",
                    "performance": "lazy loading for images"
                }
            ))
        
        return components
    
    def _analyze_layout(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Analyze the overall page layout."""
        layout_info = {
            "type": "unknown",
            "grid_system": None,
            "breakpoints": [],
            "layout_patterns": []
        }
        
        # Check for CSS Grid/Flexbox indicators
        grid_indicators = soup.find_all(class_=re.compile(r'grid|flex|container'))
        if grid_indicators:
            layout_info["grid_system"] = "CSS Grid/Flexbox"
            layout_info["type"] = "modern_grid"
        
        # Check for Bootstrap/Foundation
        bootstrap_indicators = soup.find_all(class_=re.compile(r'col-|row|container'))
        if len(bootstrap_indicators) > 5:
            layout_info["grid_system"] = "Bootstrap-like"
            layout_info["type"] = "framework_grid"
        
        # Analyze responsive breakpoints from CSS classes
        breakpoint_patterns = [
            r'sm-|small-', r'md-|medium-', r'lg-|large-', r'xl-|xlarge-'
        ]
        
        for pattern in breakpoint_patterns:
            if soup.find_all(class_=re.compile(pattern)):
                # Common breakpoints
                if 'sm' in pattern or 'small' in pattern:
                    layout_info["breakpoints"].append(576)
                elif 'md' in pattern or 'medium' in pattern:
                    layout_info["breakpoints"].append(768)
                elif 'lg' in pattern or 'large' in pattern:
                    layout_info["breakpoints"].append(992)
                elif 'xl' in pattern or 'xlarge' in pattern:
                    layout_info["breakpoints"].append(1200)
        
        # Determine layout type based on structure
        has_sidebar = bool(soup.find('aside') or soup.find(class_=re.compile(r'sidebar')))
        has_header = bool(soup.find('header'))
        has_footer = bool(soup.find('footer'))
        
        if layout_info["type"] == "unknown":
            if has_sidebar:
                layout_info["type"] = "sidebar_layout"
            elif has_header and has_footer:
                layout_info["type"] = "traditional_layout"
            else:
                layout_info["type"] = "simple_layout"
        
        return layout_info
    
    def _analyze_navigation(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Analyze navigation structure and patterns."""
        nav_structure = {
            "primary_nav": None,
            "secondary_nav": [],
            "breadcrumbs": None,
            "nav_count": 0,
            "nav_style": "unknown"
        }
        
        nav_elements = soup.find_all('nav')
        nav_structure["nav_count"] = len(nav_elements)
        
        # Find primary navigation (usually the first or largest)
        if nav_elements:
            primary_nav = nav_elements[0]
            nav_links = primary_nav.find_all('a')
            
            nav_structure["primary_nav"] = {
                "link_count": len(nav_links),
                "has_dropdown": bool(primary_nav.find_all(class_=re.compile(r'dropdown|submenu'))),
                "style": self._determine_nav_style(primary_nav)
            }
        
        # Look for breadcrumbs
        breadcrumb_indicators = soup.find_all(class_=re.compile(r'breadcrumb|crumb'))
        if breadcrumb_indicators:
            nav_structure["breadcrumbs"] = {
                "present": True,
                "levels": len(breadcrumb_indicators[0].find_all('a')) if breadcrumb_indicators else 0
            }
        
        return nav_structure
    
    def _generate_component_intent(self, component_type: ComponentType, element: Tag) -> str:
        """Generate design intent description for a component."""
        intents = {
            ComponentType.HEADER: "Primary site header for branding and navigation",
            ComponentType.FOOTER: "Site footer with links and information",
            ComponentType.NAVIGATION: "Navigation menu for site wayfinding",
            ComponentType.HERO: "Hero section to capture attention and communicate value",
            ComponentType.CARD: "Content card for displaying information in digestible chunks",
            ComponentType.BUTTON: "Interactive button for user actions",
            ComponentType.FORM: "User input form for data collection",
            ComponentType.MODAL: "Modal dialog for focused user interaction",
            ComponentType.CAROUSEL: "Content carousel for showcasing multiple items",
            ComponentType.SIDEBAR: "Secondary content area for additional information"
        }
        
        return intents.get(component_type, "UI component for user interaction")
    
    def _analyze_component_features(self, element: Tag) -> Dict[str, str]:
        """Analyze modern features of a component."""
        features = {}
        
        # Check for responsive classes
        classes = element.get('class', [])
        class_string = ' '.join(classes) if classes else ''
        
        if re.search(r'responsive|mobile|tablet|desktop', class_string, re.IGNORECASE):
            features["responsive_design"] = "responsive layout adapts to screen size"
        
        # Check for animation/transition indicators
        if re.search(r'animate|transition|fade|slide', class_string, re.IGNORECASE):
            features["animations"] = "smooth transitions and animations"
        
        # Check for accessibility features
        if element.get('aria-label') or element.get('role'):
            features["accessibility"] = "ARIA labels and semantic markup"
        
        # Check for interactive states
        if re.search(r'hover|focus|active', class_string, re.IGNORECASE):
            features["interaction_states"] = "hover and focus states for better UX"
        
        return features
    
    def _determine_form_purpose(self, form: Tag) -> str:
        """Determine the purpose of a form based on its fields and context."""
        # Check form action and method
        action = form.get('action', '').lower()
        
        if 'contact' in action or 'mail' in action:
            return "Contact"
        elif 'login' in action or 'signin' in action:
            return "Login"
        elif 'register' in action or 'signup' in action:
            return "Registration"
        elif 'search' in action:
            return "Search"
        elif 'subscribe' in action or 'newsletter' in action:
            return "Newsletter"
        
        # Check input types and names
        inputs = form.find_all(['input', 'textarea', 'select'])
        input_types = [inp.get('type', '').lower() for inp in inputs]
        input_names = [inp.get('name', '').lower() for inp in inputs]
        
        if 'email' in input_types and 'password' in input_types:
            if any('confirm' in name for name in input_names):
                return "Registration"
            else:
                return "Login"
        elif 'email' in input_types and len(inputs) == 1:
            return "Newsletter"
        elif any('message' in name or 'comment' in name for name in input_names):
            return "Contact"
        elif 'search' in input_names or any('q' == name for name in input_names):
            return "Search"
        
        return "General"
    
    def _determine_nav_style(self, nav: Tag) -> str:
        """Determine the style of navigation."""
        classes = nav.get('class', [])
        class_string = ' '.join(classes) if classes else ''
        
        if re.search(r'horizontal|inline|flex', class_string, re.IGNORECASE):
            return "horizontal"
        elif re.search(r'vertical|sidebar|side', class_string, re.IGNORECASE):
            return "vertical"
        elif re.search(r'hamburger|mobile|toggle', class_string, re.IGNORECASE):
            return "mobile_hamburger"
        elif re.search(r'mega|dropdown', class_string, re.IGNORECASE):
            return "mega_menu"
        
        # Default determination based on structure
        links = nav.find_all('a')
        if len(links) > 6:
            return "horizontal_condensed"
        else:
            return "horizontal"
    
    def _deduplicate_components(self, components: List[ComponentSpec]) -> List[ComponentSpec]:
        """Remove duplicate components based on type and name."""
        seen = set()
        unique_components = []
        
        for component in components:
            key = (component.component_type, component.component_name)
            if key not in seen:
                seen.add(key)
                unique_components.append(component)
        
        return unique_components