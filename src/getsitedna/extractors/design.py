"""Design analysis module for colors, typography, and visual patterns."""

import re
from typing import Dict, List, Optional, Set, Tuple, Any
from collections import Counter
from urllib.parse import urljoin

import cssutils
from bs4 import BeautifulSoup

from ..models.page import Page
from ..models.site import Site
from ..models.schemas import ColorInfo, FontInfo, DesignToken


class DesignExtractor:
    """Extract and analyze design elements from web pages."""
    
    def __init__(self):
        # Suppress cssutils warnings
        cssutils.log.setLevel('ERROR')
        
        # Common web-safe colors and their names
        self.named_colors = {
            '#000000': 'black',
            '#ffffff': 'white',
            '#ff0000': 'red',
            '#00ff00': 'green',
            '#0000ff': 'blue',
            '#ffff00': 'yellow',
            '#ff00ff': 'magenta',
            '#00ffff': 'cyan',
            '#808080': 'gray',
            '#c0c0c0': 'silver',
        }
        
        # Common font stacks
        self.font_categories = {
            'serif': ['times', 'georgia', 'garamond', 'palatino'],
            'sans-serif': ['arial', 'helvetica', 'verdana', 'tahoma', 'sans-serif'],
            'monospace': ['courier', 'monaco', 'consolas', 'monospace'],
            'display': ['impact', 'bebas', 'oswald', 'lobster'],
            'script': ['brush', 'pacifico', 'dancing', 'great vibes']
        }
    
    def extract_design(self, page: Page) -> Page:
        """Extract design elements from a page."""
        if not page.html_content:
            page.add_warning("No HTML content available for design extraction")
            return page
        
        soup = BeautifulSoup(page.html_content, 'html.parser')
        
        # Extract colors
        colors = self._extract_colors(soup, page)
        page.design.color_palette = colors
        
        # Extract typography
        fonts = self._extract_typography(soup, page)
        page.design.typography = fonts
        
        # Extract design tokens
        tokens = self._extract_design_tokens(soup, page)
        page.design.design_tokens = tokens
        
        # Analyze spacing system
        spacing = self._analyze_spacing_system(soup)
        page.design.spacing_system = spacing
        
        return page
    
    def _extract_colors(self, soup: BeautifulSoup, page: Page) -> List[ColorInfo]:
        """Extract color information from HTML and CSS."""
        colors = {}
        
        # Extract from inline styles
        self._extract_inline_colors(soup, colors)
        
        # Extract from CSS files
        css_links = soup.find_all('link', rel='stylesheet', href=True)
        for link in css_links:
            css_url = urljoin(str(page.url), link['href'])
            self._extract_css_colors(css_url, colors)
        
        # Extract from style tags
        style_tags = soup.find_all('style')
        for style_tag in style_tags:
            if style_tag.string:
                self._parse_css_colors(style_tag.string, colors)
        
        # Convert to ColorInfo objects
        color_infos = []
        for hex_color, info in colors.items():
            color_info = ColorInfo(
                hex=hex_color,
                rgb=self._hex_to_rgb(hex_color),
                usage_context=info['contexts'],
                frequency=info['frequency']
            )
            color_infos.append(color_info)
        
        # Sort by frequency
        color_infos.sort(key=lambda x: x.frequency, reverse=True)
        
        return color_infos[:20]  # Top 20 colors
    
    def _extract_inline_colors(self, soup: BeautifulSoup, colors: Dict[str, Dict]):
        """Extract colors from inline styles."""
        elements_with_style = soup.find_all(style=True)
        
        for element in elements_with_style:
            style = element.get('style', '')
            element_colors = self._parse_css_colors(style, {})
            
            for hex_color, info in element_colors.items():
                if hex_color not in colors:
                    colors[hex_color] = {'contexts': [], 'frequency': 0}
                
                colors[hex_color]['frequency'] += info['frequency']
                
                # Add context
                tag_name = element.name
                class_names = element.get('class', [])
                context = f"{tag_name}"
                if class_names:
                    context += f".{'.'.join(class_names[:2])}"  # First 2 classes
                
                if context not in colors[hex_color]['contexts']:
                    colors[hex_color]['contexts'].append(context)
    
    def _extract_css_colors(self, css_url: str, colors: Dict[str, Dict]):
        """Extract colors from external CSS files."""
        try:
            import requests
            response = requests.get(css_url, timeout=10)
            if response.status_code == 200:
                self._parse_css_colors(response.text, colors)
        except Exception:
            # Silently fail for CSS extraction
            pass
    
    def _parse_css_colors(self, css_content: str, colors: Dict[str, Dict]) -> Dict[str, Dict]:
        """Parse CSS content for color values."""
        if not colors:
            colors = {}
        
        # Find hex colors
        hex_pattern = r'#([0-9a-fA-F]{3}|[0-9a-fA-F]{6})\b'
        hex_matches = re.findall(hex_pattern, css_content)
        
        for match in hex_matches:
            hex_color = f"#{match.lower()}"
            
            # Convert 3-digit hex to 6-digit
            if len(match) == 3:
                hex_color = f"#{match[0]}{match[0]}{match[1]}{match[1]}{match[2]}{match[2]}"
            
            if hex_color not in colors:
                colors[hex_color] = {'contexts': ['css'], 'frequency': 0}
            
            colors[hex_color]['frequency'] += 1
        
        # Find RGB colors
        rgb_pattern = r'rgb\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)'
        rgb_matches = re.findall(rgb_pattern, css_content)
        
        for r, g, b in rgb_matches:
            hex_color = f"#{int(r):02x}{int(g):02x}{int(b):02x}"
            
            if hex_color not in colors:
                colors[hex_color] = {'contexts': ['css'], 'frequency': 0}
            
            colors[hex_color]['frequency'] += 1
        
        # Find RGBA colors
        rgba_pattern = r'rgba\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*[\d.]+\s*\)'
        rgba_matches = re.findall(rgba_pattern, css_content)
        
        for r, g, b in rgba_matches:
            hex_color = f"#{int(r):02x}{int(g):02x}{int(b):02x}"
            
            if hex_color not in colors:
                colors[hex_color] = {'contexts': ['css'], 'frequency': 0}
            
            colors[hex_color]['frequency'] += 1
        
        return colors
    
    def _extract_typography(self, soup: BeautifulSoup, page: Page) -> List[FontInfo]:
        """Extract typography information."""
        fonts = {}
        
        # Extract from inline styles
        self._extract_inline_fonts(soup, fonts)
        
        # Extract from CSS files
        css_links = soup.find_all('link', rel='stylesheet', href=True)
        for link in css_links:
            css_url = urljoin(str(page.url), link['href'])
            self._extract_css_fonts(css_url, fonts)
        
        # Extract from style tags
        style_tags = soup.find_all('style')
        for style_tag in style_tags:
            if style_tag.string:
                self._parse_css_fonts(style_tag.string, fonts)
        
        # Convert to FontInfo objects
        font_infos = []
        for font_family, info in fonts.items():
            font_info = FontInfo(
                family=font_family,
                weights=list(set(info['weights'])),
                sizes=list(set(info['sizes'])),
                usage_context=info['contexts']
            )
            font_infos.append(font_info)
        
        return font_infos
    
    def _extract_inline_fonts(self, soup: BeautifulSoup, fonts: Dict[str, Dict]):
        """Extract fonts from inline styles."""
        elements_with_style = soup.find_all(style=True)
        
        for element in elements_with_style:
            style = element.get('style', '')
            element_fonts = self._parse_css_fonts(style, {})
            
            for font_family, info in element_fonts.items():
                if font_family not in fonts:
                    fonts[font_family] = {'weights': [], 'sizes': [], 'contexts': []}
                
                fonts[font_family]['weights'].extend(info['weights'])
                fonts[font_family]['sizes'].extend(info['sizes'])
                
                # Add context
                tag_name = element.name
                if tag_name not in fonts[font_family]['contexts']:
                    fonts[font_family]['contexts'].append(tag_name)
    
    def _extract_css_fonts(self, css_url: str, fonts: Dict[str, Dict]):
        """Extract fonts from external CSS files."""
        try:
            import requests
            response = requests.get(css_url, timeout=10)
            if response.status_code == 200:
                # The _parse_css_fonts method modifies the fonts dict in place
                parsed_fonts = self._parse_css_fonts(response.text, fonts)
                # Update fonts with the parsed results
                fonts.update(parsed_fonts)
        except Exception as e:
            # Silently handle CSS fetching errors in production
            pass
    
    def _parse_css_fonts(self, css_content: str, fonts: Dict[str, Dict]) -> Dict[str, Dict]:
        """Parse CSS content for font information."""
        if not fonts:
            fonts = {}
        
        # Parse @font-face declarations (Google Fonts, custom fonts)
        self._parse_font_face_declarations(css_content, fonts)
        
        # Parse regular font-family declarations in CSS rules
        self._parse_font_family_declarations(css_content, fonts)
        
        return fonts
    
    def _parse_font_face_declarations(self, css_content: str, fonts: Dict[str, Dict]):
        """Parse @font-face declarations for comprehensive font information."""
        # Find @font-face blocks
        font_face_pattern = r'@font-face\s*\{([^}]+)\}'
        font_face_matches = re.findall(font_face_pattern, css_content, re.IGNORECASE | re.DOTALL)
        
        
        for font_face_block in font_face_matches:
            # Extract font-family from this block
            family_match = re.search(r'font-family\s*:\s*[\'"]?([^\'";\}]+)[\'"]?', font_face_block, re.IGNORECASE)
            if not family_match:
                continue
                
            font_family = family_match.group(1).strip()
            
            # Initialize font entry if not exists
            if font_family not in fonts:
                fonts[font_family] = {'weights': [], 'sizes': [], 'contexts': ['css']}
            
            # Extract font-weight from this block
            weight_match = re.search(r'font-weight\s*:\s*(\d+|bold|normal|lighter|bolder)', font_face_block, re.IGNORECASE)
            if weight_match:
                weight = weight_match.group(1).lower()
                
                # Convert named weights to numbers
                weight_mapping = {
                    'normal': 400,
                    'bold': 700,
                    'lighter': 300,
                    'bolder': 800
                }
                
                if weight in weight_mapping:
                    weight_num = weight_mapping[weight]
                elif weight.isdigit():
                    weight_num = int(weight)
                else:
                    weight_num = 400  # Default
                
                if weight_num not in fonts[font_family]['weights']:
                    fonts[font_family]['weights'].append(weight_num)
            
            # Extract font-size if present (rare in @font-face but possible)
            size_match = re.search(r'font-size\s*:\s*([^;\}]+)', font_face_block, re.IGNORECASE)
            if size_match:
                size = size_match.group(1).strip()
                if size not in fonts[font_family]['sizes']:
                    fonts[font_family]['sizes'].append(size)
    
    def _parse_font_family_declarations(self, css_content: str, fonts: Dict[str, Dict]):
        """Parse regular font-family declarations in CSS rules."""
        # Find font-family declarations in CSS rules (not @font-face)
        # Remove @font-face blocks first, then search for font-family
        css_without_fontface = re.sub(r'@font-face\s*\{[^}]+\}', '', css_content, flags=re.IGNORECASE | re.DOTALL)
        
        font_family_pattern = r'font-family\s*:\s*([^;]+)'
        font_matches = re.findall(font_family_pattern, css_without_fontface, re.IGNORECASE)
        
        for match in font_matches:
            # Clean up the font family string
            font_families = [f.strip().strip('"\'') for f in match.split(',')]
            
            for font_family in font_families:
                if font_family and font_family.lower() not in ['inherit', 'initial', 'unset']:
                    if font_family not in fonts:
                        fonts[font_family] = {'weights': [], 'sizes': [], 'contexts': ['css']}
        
        # Find font-weight and font-size declarations and try to associate them with context
        self._parse_contextual_font_properties(css_content, fonts)
    
    def _parse_contextual_font_properties(self, css_content: str, fonts: Dict[str, Dict]):
        """Parse font weights and sizes and try to associate them contextually."""
        # Look for CSS rules that contain both font-family and other properties
        css_rule_pattern = r'([^{}]*)\{([^}]+)\}'
        css_rules = re.findall(css_rule_pattern, css_content, re.IGNORECASE | re.DOTALL)
        
        for selector, rule_body in css_rules:
            # Skip @font-face rules (already handled)
            if '@font-face' in selector:
                continue
                
            # Check if this rule has a font-family declaration
            family_match = re.search(r'font-family\s*:\s*([^;]+)', rule_body, re.IGNORECASE)
            if family_match:
                font_families = [f.strip().strip('"\'') for f in family_match.group(1).split(',')]
                
                # Look for font-weight in the same rule
                weight_match = re.search(r'font-weight\s*:\s*(\d+|bold|normal|lighter|bolder)', rule_body, re.IGNORECASE)
                if weight_match:
                    weight = weight_match.group(1).lower()
                    weight_mapping = {
                        'normal': 400,
                        'bold': 700,
                        'lighter': 300,
                        'bolder': 800
                    }
                    
                    if weight in weight_mapping:
                        weight_num = weight_mapping[weight]
                    elif weight.isdigit():
                        weight_num = int(weight)
                    else:
                        weight_num = 400
                    
                    # Add weight to the specific font families in this rule
                    for font_family in font_families:
                        if font_family and font_family.lower() not in ['inherit', 'initial', 'unset']:
                            if font_family not in fonts:
                                fonts[font_family] = {'weights': [], 'sizes': [], 'contexts': ['css']}
                            if weight_num not in fonts[font_family]['weights']:
                                fonts[font_family]['weights'].append(weight_num)
                
                # Look for font-size in the same rule
                size_match = re.search(r'font-size\s*:\s*([^;]+)', rule_body, re.IGNORECASE)
                if size_match:
                    size = size_match.group(1).strip()
                    if size not in ['inherit', 'initial', 'unset']:
                        # Add size to the specific font families in this rule
                        for font_family in font_families:
                            if font_family and font_family.lower() not in ['inherit', 'initial', 'unset']:
                                if font_family not in fonts:
                                    fonts[font_family] = {'weights': [], 'sizes': [], 'contexts': ['css']}
                                if size not in fonts[font_family]['sizes']:
                                    fonts[font_family]['sizes'].append(size)
    
    def _extract_design_tokens(self, soup: BeautifulSoup, page: Page) -> List[DesignToken]:
        """Extract design tokens and CSS custom properties."""
        tokens = []
        
        # Extract CSS custom properties (CSS variables)
        style_tags = soup.find_all('style')
        for style_tag in style_tags:
            if style_tag.string:
                css_tokens = self._parse_css_variables(style_tag.string)
                tokens.extend(css_tokens)
        
        # Look for common design token patterns in classes
        class_tokens = self._extract_class_tokens(soup)
        tokens.extend(class_tokens)
        
        return tokens
    
    def _parse_css_variables(self, css_content: str) -> List[DesignToken]:
        """Parse CSS custom properties as design tokens."""
        tokens = []
        
        # Find CSS custom properties
        var_pattern = r'--([a-zA-Z0-9-]+)\s*:\s*([^;]+)'
        var_matches = re.findall(var_pattern, css_content)
        
        for name, value in var_matches:
            category = self._categorize_token(name, value)
            
            token = DesignToken(
                name=f"--{name}",
                value=value.strip(),
                category=category,
                usage=["css_variable"]
            )
            tokens.append(token)
        
        return tokens
    
    def _extract_class_tokens(self, soup: BeautifulSoup) -> List[DesignToken]:
        """Extract design tokens from common class naming patterns."""
        tokens = []
        
        # Find all elements with classes
        elements_with_classes = soup.find_all(class_=True)
        class_names = []
        
        for element in elements_with_classes:
            class_names.extend(element.get('class', []))
        
        # Count class frequency
        class_counts = Counter(class_names)
        
        # Look for design token patterns
        for class_name, count in class_counts.most_common(50):
            if self._is_design_token_class(class_name):
                category = self._categorize_class_token(class_name)
                
                token = DesignToken(
                    name=class_name,
                    value="class",
                    category=category,
                    usage=[f"used_{count}_times"]
                )
                tokens.append(token)
        
        return tokens
    
    def _analyze_spacing_system(self, soup: BeautifulSoup) -> Dict[str, str]:
        """Analyze spacing patterns in the design."""
        spacing_system = {}
        
        # Look for common spacing classes
        spacing_patterns = {
            'margin': r'm[tblr]?-\d+|margin-\d+',
            'padding': r'p[tblr]?-\d+|padding-\d+',
            'gap': r'gap-\d+|space-[xy]-\d+'
        }
        
        elements_with_classes = soup.find_all(class_=True)
        
        for property_name, pattern in spacing_patterns.items():
            spacing_classes = []
            
            for element in elements_with_classes:
                class_list = element.get('class', [])
                for class_name in class_list:
                    if re.match(pattern, class_name):
                        spacing_classes.append(class_name)
            
            if spacing_classes:
                # Find the most common spacing values
                spacing_counts = Counter(spacing_classes)
                top_spacing = [cls for cls, count in spacing_counts.most_common(5)]
                spacing_system[property_name] = ', '.join(top_spacing)
        
        return spacing_system
    
    def _hex_to_rgb(self, hex_color: str) -> Tuple[int, int, int]:
        """Convert hex color to RGB tuple."""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    def _categorize_token(self, name: str, value: str) -> str:
        """Categorize a design token based on name and value."""
        name_lower = name.lower()
        value_lower = value.lower()
        
        if any(keyword in name_lower for keyword in ['color', 'bg', 'border', 'text']):
            return 'color'
        elif any(keyword in name_lower for keyword in ['font', 'text', 'type']):
            return 'typography'
        elif any(keyword in name_lower for keyword in ['space', 'margin', 'padding', 'gap']):
            return 'spacing'
        elif any(keyword in name_lower for keyword in ['shadow', 'elevation']):
            return 'shadow'
        elif any(keyword in name_lower for keyword in ['radius', 'rounded']):
            return 'border-radius'
        elif any(keyword in name_lower for keyword in ['size', 'width', 'height']):
            return 'sizing'
        else:
            return 'other'
    
    def _is_design_token_class(self, class_name: str) -> bool:
        """Check if a class name represents a design token."""
        # Common design token patterns
        token_patterns = [
            r'^(text|bg|border)-(primary|secondary|accent|gray|red|blue|green)',
            r'^(m|p)[tblr]?-\d+$',
            r'^text-(xs|sm|base|lg|xl|\d+xl)$',
            r'^font-(light|normal|medium|semibold|bold)$',
            r'^rounded(-\w+)?$',
            r'^shadow(-\w+)?$',
            r'^opacity-\d+$',
            r'^z-\d+$'
        ]
        
        return any(re.match(pattern, class_name) for pattern in token_patterns)
    
    def _categorize_class_token(self, class_name: str) -> str:
        """Categorize a class-based design token."""
        if any(prefix in class_name for prefix in ['text-', 'font-']):
            return 'typography'
        elif any(prefix in class_name for prefix in ['bg-', 'border-']):
            return 'color'
        elif any(prefix in class_name for prefix in ['m-', 'p-', 'space-', 'gap-']):
            return 'spacing'
        elif 'rounded' in class_name:
            return 'border-radius'
        elif 'shadow' in class_name:
            return 'shadow'
        elif any(prefix in class_name for prefix in ['w-', 'h-', 'size-']):
            return 'sizing'
        else:
            return 'layout'
    
    def analyze_global_design_system(self, site: Site) -> Site:
        """Analyze global design patterns across all pages."""
        all_colors = {}
        all_fonts = {}
        all_tokens = {}
        
        # Aggregate design elements from all pages
        for page in site.crawled_pages:
            # Aggregate colors
            for color in page.design.color_palette:
                if color.hex not in all_colors:
                    all_colors[color.hex] = color
                else:
                    # Merge usage contexts and frequency
                    existing_color = all_colors[color.hex]
                    existing_color.frequency += color.frequency
                    
                    for context in color.usage_context:
                        if context not in existing_color.usage_context:
                            existing_color.usage_context.append(context)
            
            # Aggregate fonts
            for font in page.design.typography:
                if font.family not in all_fonts:
                    all_fonts[font.family] = font
                else:
                    # Merge weights, sizes, and contexts
                    existing_font = all_fonts[font.family]
                    existing_font.weights = list(set(existing_font.weights + font.weights))
                    existing_font.sizes = list(set(existing_font.sizes + font.sizes))
                    
                    for context in font.usage_context:
                        if context not in existing_font.usage_context:
                            existing_font.usage_context.append(context)
            
            # Aggregate tokens
            for token in page.design.design_tokens:
                if token.name not in all_tokens:
                    all_tokens[token.name] = token
                else:
                    # Merge usage
                    existing_token = all_tokens[token.name]
                    for usage in token.usage:
                        if usage not in existing_token.usage:
                            existing_token.usage.append(usage)
        
        # Sort and set global design system
        site.global_color_palette = sorted(
            all_colors.values(), 
            key=lambda x: x.frequency, 
            reverse=True
        )[:15]  # Top 15 colors
        
        site.global_typography = list(all_fonts.values())
        site.global_design_tokens = list(all_tokens.values())
        
        return site