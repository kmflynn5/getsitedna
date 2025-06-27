"""Pattern recognition for UX components and design patterns."""

import re
from typing import Dict, List, Optional, Set, Tuple, Any
from collections import Counter, defaultdict

from bs4 import BeautifulSoup, Tag

from ..models.site import Site
from ..models.page import Page
from ..models.schemas import ExperiencePattern, ComponentSpec, ComponentType


class PatternRecognizer:
    """Recognize common UX patterns and design components across pages."""
    
    def __init__(self):
        self.ux_patterns = {
            'hero_section': {
                'indicators': ['hero', 'banner', 'jumbotron', 'splash', 'intro'],
                'elements': ['h1', 'h2', 'large image', 'cta button'],
                'description': 'Large prominent section at the top of the page'
            },
            'card_layout': {
                'indicators': ['card', 'item', 'product', 'article-card'],
                'elements': ['image', 'title', 'description', 'link'],
                'description': 'Repeating card-based content layout'
            },
            'navigation_menu': {
                'indicators': ['nav', 'menu', 'navbar', 'navigation'],
                'elements': ['ul', 'li', 'links'],
                'description': 'Site navigation structure'
            },
            'call_to_action': {
                'indicators': ['cta', 'button', 'action', 'signup', 'download'],
                'elements': ['button', 'link', 'form'],
                'description': 'Prominent action-oriented buttons or sections'
            },
            'testimonial': {
                'indicators': ['testimonial', 'review', 'quote', 'feedback'],
                'elements': ['quote', 'author', 'image', 'rating'],
                'description': 'Customer testimonials or reviews'
            },
            'feature_grid': {
                'indicators': ['features', 'benefits', 'services', 'grid'],
                'elements': ['grid layout', 'icons', 'titles', 'descriptions'],
                'description': 'Grid layout showcasing features or services'
            },
            'contact_form': {
                'indicators': ['contact', 'form', 'inquiry', 'message'],
                'elements': ['form', 'input fields', 'submit button'],
                'description': 'Contact or inquiry form'
            },
            'social_proof': {
                'indicators': ['logos', 'clients', 'partners', 'brands'],
                'elements': ['logo grid', 'company names'],
                'description': 'Display of client logos or partner brands'
            },
            'pricing_table': {
                'indicators': ['pricing', 'plans', 'packages', 'subscription'],
                'elements': ['columns', 'prices', 'features', 'buttons'],
                'description': 'Pricing comparison table or plans'
            },
            'breadcrumb_navigation': {
                'indicators': ['breadcrumb', 'breadcrumbs', 'path'],
                'elements': ['ordered list', 'separators', 'links'],
                'description': 'Hierarchical navigation showing current location'
            },
            'image_gallery': {
                'indicators': ['gallery', 'photos', 'images', 'portfolio'],
                'elements': ['image grid', 'thumbnails', 'lightbox'],
                'description': 'Collection of images in grid or carousel format'
            },
            'search_functionality': {
                'indicators': ['search', 'find', 'query'],
                'elements': ['search input', 'search button', 'filters'],
                'description': 'Search interface and functionality'
            },
            'footer_links': {
                'indicators': ['footer', 'bottom', 'links'],
                'elements': ['columns', 'links', 'copyright'],
                'description': 'Footer with organized link sections'
            },
            'modal_dialog': {
                'indicators': ['modal', 'popup', 'dialog', 'overlay'],
                'elements': ['overlay', 'close button', 'content'],
                'description': 'Modal dialog or popup window'
            },
            'accordion_faq': {
                'indicators': ['accordion', 'faq', 'expand', 'collapse'],
                'elements': ['expandable sections', 'toggle buttons'],
                'description': 'Expandable content sections or FAQ'
            }
        }
        
        # Component combination patterns
        self.layout_patterns = {
            'landing_page': ['hero_section', 'feature_grid', 'call_to_action', 'testimonial'],
            'product_page': ['hero_section', 'feature_grid', 'pricing_table', 'call_to_action'],
            'blog_layout': ['navigation_menu', 'card_layout', 'search_functionality'],
            'portfolio_site': ['hero_section', 'image_gallery', 'contact_form'],
            'corporate_site': ['hero_section', 'feature_grid', 'social_proof', 'contact_form']
        }
    
    def recognize_patterns(self, site: Site) -> Site:
        """Recognize UX patterns across all pages in the site."""
        # Collect pattern occurrences
        pattern_occurrences = defaultdict(list)
        component_combinations = defaultdict(int)
        
        for page in site.crawled_pages:
            page_patterns = self._analyze_page_patterns(page)
            
            for pattern_name, pattern_info in page_patterns.items():
                pattern_occurrences[pattern_name].append({
                    'page_url': str(page.url),
                    'page_title': page.title,
                    'confidence': pattern_info['confidence'],
                    'elements': pattern_info['elements']
                })
            
            # Track component combinations
            pattern_names = list(page_patterns.keys())
            for i, pattern1 in enumerate(pattern_names):
                for pattern2 in pattern_names[i+1:]:
                    combo = tuple(sorted([pattern1, pattern2]))
                    component_combinations[combo] += 1
        
        # Generate experience patterns
        experience_patterns = self._generate_experience_patterns(pattern_occurrences, site)
        site.experience_patterns = experience_patterns
        
        # Identify layout types
        layout_analysis = self._analyze_layout_patterns(pattern_occurrences, component_combinations)
        site.design_intent.visual_hierarchy = layout_analysis
        
        return site
    
    def _analyze_page_patterns(self, page: Page) -> Dict[str, Dict[str, Any]]:
        """Analyze patterns on a single page."""
        if not page.html_content:
            return {}
        
        soup = BeautifulSoup(page.html_content, 'html.parser')
        detected_patterns = {}
        
        for pattern_name, pattern_config in self.ux_patterns.items():
            confidence, elements = self._detect_pattern(soup, pattern_config)
            
            if confidence > 0.3:  # Threshold for pattern detection
                detected_patterns[pattern_name] = {
                    'confidence': confidence,
                    'elements': elements,
                    'description': pattern_config['description']
                }
        
        return detected_patterns
    
    def _detect_pattern(self, soup: BeautifulSoup, pattern_config: Dict) -> Tuple[float, List[str]]:
        """Detect a specific pattern in the HTML."""
        indicators = pattern_config['indicators']
        expected_elements = pattern_config['elements']
        
        confidence = 0.0
        found_elements = []
        
        # Check for class/id indicators
        indicator_score = 0
        for indicator in indicators:
            # Check classes
            class_matches = soup.find_all(class_=re.compile(indicator, re.IGNORECASE))
            if class_matches:
                indicator_score += len(class_matches) * 0.3
                found_elements.extend([f"class:{indicator}" for _ in class_matches[:3]])
            
            # Check IDs
            id_matches = soup.find_all(id=re.compile(indicator, re.IGNORECASE))
            if id_matches:
                indicator_score += len(id_matches) * 0.4
                found_elements.extend([f"id:{indicator}" for _ in id_matches[:3]])
        
        # Normalize indicator score
        confidence += min(indicator_score / len(indicators), 0.6)
        
        # Check for expected elements
        element_score = 0
        for element in expected_elements:
            if self._has_element_pattern(soup, element):
                element_score += 1
                found_elements.append(element)
        
        # Normalize element score
        confidence += (element_score / len(expected_elements)) * 0.4
        
        return min(confidence, 1.0), found_elements
    
    def _has_element_pattern(self, soup: BeautifulSoup, element_pattern: str) -> bool:
        """Check if the soup contains a specific element pattern."""
        element_pattern_lower = element_pattern.lower()
        
        if element_pattern_lower == 'h1':
            return bool(soup.find('h1'))
        elif element_pattern_lower == 'h2':
            return bool(soup.find('h2'))
        elif 'image' in element_pattern_lower:
            return bool(soup.find('img'))
        elif 'button' in element_pattern_lower:
            return bool(soup.find('button') or soup.find('input', type='submit'))
        elif 'form' in element_pattern_lower:
            return bool(soup.find('form'))
        elif 'ul' in element_pattern_lower or 'list' in element_pattern_lower:
            return bool(soup.find('ul'))
        elif 'grid' in element_pattern_lower:
            # Look for grid-like structures
            grid_indicators = soup.find_all(class_=re.compile(r'grid|row|col', re.IGNORECASE))
            return len(grid_indicators) > 2
        elif 'quote' in element_pattern_lower:
            return bool(soup.find('blockquote') or soup.find(class_=re.compile('quote', re.IGNORECASE)))
        elif 'input' in element_pattern_lower:
            return bool(soup.find('input'))
        elif 'link' in element_pattern_lower:
            return bool(soup.find('a'))
        else:
            # Generic text search
            return element_pattern_lower in soup.get_text().lower()
    
    def _generate_experience_patterns(self, pattern_occurrences: Dict, site: Site) -> List[ExperiencePattern]:
        """Generate experience patterns from detected occurrences."""
        experience_patterns = []
        
        for pattern_name, occurrences in pattern_occurrences.items():
            if len(occurrences) >= 2:  # Pattern appears on multiple pages
                # Calculate average confidence
                avg_confidence = sum(occ['confidence'] for occ in occurrences) / len(occurrences)
                
                # Generate modern implementation suggestions
                modern_impl = self._suggest_modern_implementation(pattern_name, occurrences)
                
                # Determine user benefit
                user_benefit = self._determine_user_benefit(pattern_name)
                
                # Generate technical requirements
                tech_requirements = self._generate_tech_requirements(pattern_name, site.metadata.target_framework)
                
                experience_pattern = ExperiencePattern(
                    pattern_name=pattern_name.replace('_', ' ').title(),
                    original_intent=self.ux_patterns[pattern_name]['description'],
                    modern_implementation=modern_impl,
                    user_benefit=user_benefit,
                    technical_requirements=tech_requirements
                )
                
                experience_patterns.append(experience_pattern)
        
        return experience_patterns
    
    def _suggest_modern_implementation(self, pattern_name: str, occurrences: List[Dict]) -> Dict[str, Any]:
        """Suggest modern implementation approach for a pattern."""
        framework_suggestions = {
            'hero_section': {
                'component_structure': 'Responsive hero component with optimized images',
                'accessibility': 'Proper heading hierarchy and alt text',
                'performance': 'Lazy loading for background images',
                'responsive_design': 'Mobile-first approach with breakpoint-specific layouts'
            },
            'card_layout': {
                'component_structure': 'Reusable card component with consistent spacing',
                'accessibility': 'Semantic markup with proper heading levels',
                'performance': 'Virtualization for large lists',
                'responsive_design': 'CSS Grid with auto-fit columns'
            },
            'navigation_menu': {
                'component_structure': 'Accessible navigation with keyboard support',
                'accessibility': 'ARIA labels and focus management',
                'performance': 'Code splitting for mobile menu',
                'responsive_design': 'Hamburger menu for mobile devices'
            },
            'call_to_action': {
                'component_structure': 'Consistent button variants and states',
                'accessibility': 'Clear button text and focus indicators',
                'performance': 'Optimized event handlers',
                'responsive_design': 'Touch-friendly sizing on mobile'
            }
        }
        
        return framework_suggestions.get(pattern_name, {
            'component_structure': 'Modern component-based implementation',
            'accessibility': 'WCAG 2.1 AA compliance',
            'performance': 'Optimized rendering and interactions',
            'responsive_design': 'Mobile-first responsive design'
        })
    
    def _determine_user_benefit(self, pattern_name: str) -> str:
        """Determine the user benefit of a pattern."""
        benefits = {
            'hero_section': 'Immediately communicates value proposition and captures attention',
            'card_layout': 'Easy scanning of content with clear visual hierarchy',
            'navigation_menu': 'Intuitive site navigation and wayfinding',
            'call_to_action': 'Clear pathways for user engagement and conversion',
            'testimonial': 'Builds trust through social proof and credibility',
            'feature_grid': 'Quick understanding of product/service capabilities',
            'contact_form': 'Simple way for users to get in touch',
            'social_proof': 'Establishes credibility through association',
            'pricing_table': 'Easy comparison of options and pricing',
            'breadcrumb_navigation': 'Helps users understand their location in the site',
            'image_gallery': 'Visual showcase of work or products',
            'search_functionality': 'Quick access to specific content',
            'footer_links': 'Secondary navigation and important links',
            'modal_dialog': 'Focused interaction without page navigation',
            'accordion_faq': 'Organized information that reduces cognitive load'
        }
        
        return benefits.get(pattern_name, 'Improves user experience and interface usability')
    
    def _generate_tech_requirements(self, pattern_name: str, target_framework) -> List[str]:
        """Generate technical requirements for implementing a pattern."""
        base_requirements = [
            f"Implement using {target_framework.value.replace('_', ' ').title()} components",
            "Ensure responsive design across all breakpoints",
            "Follow accessibility best practices",
            "Optimize for performance and Core Web Vitals"
        ]
        
        pattern_specific = {
            'hero_section': [
                "Implement lazy loading for hero images",
                "Use next-gen image formats (WebP, AVIF)",
                "Optimize for Largest Contentful Paint (LCP)"
            ],
            'card_layout': [
                "Implement CSS Grid or Flexbox layout",
                "Add skeleton loading states",
                "Consider virtualization for large datasets"
            ],
            'navigation_menu': [
                "Implement keyboard navigation",
                "Add ARIA navigation landmarks",
                "Use semantic HTML5 nav element"
            ],
            'call_to_action': [
                "Implement button variants and states",
                "Add loading and disabled states",
                "Ensure minimum touch target size (44px)"
            ],
            'contact_form': [
                "Implement form validation",
                "Add proper error handling",
                "Include CSRF protection"
            ],
            'modal_dialog': [
                "Implement focus trapping",
                "Add escape key handling",
                "Ensure proper ARIA attributes"
            ],
            'image_gallery': [
                "Implement lazy loading",
                "Add keyboard navigation",
                "Optimize image delivery"
            ]
        }
        
        specific_reqs = pattern_specific.get(pattern_name, [])
        return base_requirements + specific_reqs
    
    def _analyze_layout_patterns(self, pattern_occurrences: Dict, combinations: Dict) -> Dict[str, str]:
        """Analyze overall layout patterns and hierarchy."""
        layout_analysis = {}
        
        # Determine primary layout type
        if 'hero_section' in pattern_occurrences and 'feature_grid' in pattern_occurrences:
            layout_analysis['primary_layout'] = 'marketing_focused'
        elif 'card_layout' in pattern_occurrences and len(pattern_occurrences.get('card_layout', [])) > 3:
            layout_analysis['primary_layout'] = 'content_heavy'
        elif 'image_gallery' in pattern_occurrences:
            layout_analysis['primary_layout'] = 'visual_portfolio'
        else:
            layout_analysis['primary_layout'] = 'standard_informational'
        
        # Analyze navigation complexity
        nav_patterns = len(pattern_occurrences.get('navigation_menu', []))
        if nav_patterns > 1:
            layout_analysis['navigation_complexity'] = 'multi_level'
        elif nav_patterns == 1:
            layout_analysis['navigation_complexity'] = 'single_level'
        else:
            layout_analysis['navigation_complexity'] = 'minimal'
        
        # Determine conversion focus
        cta_count = len(pattern_occurrences.get('call_to_action', []))
        if cta_count > 5:
            layout_analysis['conversion_focus'] = 'high'
        elif cta_count > 2:
            layout_analysis['conversion_focus'] = 'medium'
        else:
            layout_analysis['conversion_focus'] = 'low'
        
        # Content organization
        if 'accordion_faq' in pattern_occurrences or 'search_functionality' in pattern_occurrences:
            layout_analysis['content_organization'] = 'information_dense'
        elif 'card_layout' in pattern_occurrences:
            layout_analysis['content_organization'] = 'modular'
        else:
            layout_analysis['content_organization'] = 'linear'
        
        return layout_analysis


def recognize_site_patterns(site: Site) -> Site:
    """Entry point for pattern recognition across a site."""
    recognizer = PatternRecognizer()
    return recognizer.recognize_patterns(site)