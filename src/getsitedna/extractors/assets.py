"""Asset extraction and analysis module."""

import asyncio
import hashlib
import io
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from urllib.parse import urljoin, urlparse
import mimetypes

import aiohttp
import requests
from PIL import Image
import cv2
import numpy as np

from ..models.page import Page
from ..models.site import Site
from ..models.schemas import AssetInfo
from ..utils.http import AsyncHTTPSession
from ..utils.validation import clean_filename


class AssetExtractor:
    """Extract and analyze website assets."""
    
    def __init__(self, site: Site, download_assets: bool = False):
        self.site = site
        self.download_assets = download_assets
        self.asset_directory = None
        
        if download_assets and site.output_directory:
            self.asset_directory = site.output_directory / "assets"
            self.asset_directory.mkdir(parents=True, exist_ok=True)
    
    async def extract_assets(self, page: Page) -> Page:
        """Extract and analyze assets from a page."""
        if not page.assets:
            page.add_warning("No assets found on page")
            return page
        
        # Process assets in parallel
        if self.download_assets:
            async with AsyncHTTPSession() as session:
                tasks = []
                for asset in page.assets:
                    task = self._process_asset(asset, session)
                    tasks.append(task)
                
                if tasks:
                    await asyncio.gather(*tasks, return_exceptions=True)
        else:
            # Just analyze without downloading
            for asset in page.assets:
                await self._analyze_asset_info(asset)
        
        return page
    
    async def _process_asset(self, asset: AssetInfo, session: AsyncHTTPSession):
        """Process a single asset (download and analyze)."""
        try:
            # Download asset
            if self.download_assets:
                local_path = await self._download_asset(asset, session)
                if local_path:
                    asset.local_path = local_path
                    
                    # Analyze downloaded asset
                    await self._analyze_downloaded_asset(asset)
            
            # Get basic info without downloading
            await self._analyze_asset_info(asset)
            
        except Exception as e:
            # Don't fail the entire extraction for one asset
            pass
    
    async def _download_asset(self, asset: AssetInfo, session: AsyncHTTPSession) -> Optional[Path]:
        """Download an asset to local storage."""
        if not self.asset_directory:
            return None
        
        try:
            async with session.get(asset.url) as response:
                if response.status == 200:
                    # Create safe filename
                    parsed_url = urlparse(asset.url)
                    filename = Path(parsed_url.path).name
                    if not filename or '.' not in filename:
                        # Generate filename based on asset type
                        ext = self._get_extension_from_content_type(
                            response.headers.get('content-type', '')
                        )
                        filename = f"asset_{abs(hash(asset.url)) % 10000}{ext}"
                    
                    safe_filename = clean_filename(filename)
                    
                    # Create subdirectory based on asset type
                    asset_subdir = self.asset_directory / asset.type
                    asset_subdir.mkdir(exist_ok=True)
                    
                    local_path = asset_subdir / safe_filename
                    
                    # Save file
                    content = await response.read()
                    with open(local_path, 'wb') as f:
                        f.write(content)
                    
                    # Update asset info
                    asset.size = len(content)
                    
                    return local_path
                    
        except Exception as e:
            # Log error but don't fail
            return None
        
        return None
    
    async def _analyze_asset_info(self, asset: AssetInfo):
        """Analyze asset information without downloading."""
        try:
            # Get content type and size via HEAD request
            async with aiohttp.ClientSession() as session:
                async with session.head(asset.url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status == 200:
                        content_type = response.headers.get('content-type', '')
                        content_length = response.headers.get('content-length')
                        
                        if content_length:
                            asset.size = int(content_length)
                        
                        # Update asset type based on content type
                        if not asset.type or asset.type == 'unknown':
                            asset.type = self._determine_asset_type(content_type, asset.url)
                            
        except Exception:
            # Silently continue if HEAD request fails
            pass
    
    async def _analyze_downloaded_asset(self, asset: AssetInfo):
        """Analyze a downloaded asset file."""
        if not asset.local_path or not asset.local_path.exists():
            return
        
        try:
            if asset.type == 'image':
                await self._analyze_image(asset)
            elif asset.type == 'css':
                await self._analyze_css(asset)
            elif asset.type == 'javascript':
                await self._analyze_javascript(asset)
            
        except Exception as e:
            # Don't fail for analysis errors
            pass
    
    async def _analyze_image(self, asset: AssetInfo):
        """Analyze image assets."""
        try:
            with Image.open(asset.local_path) as img:
                # Basic image info
                asset.dimensions = img.size
                
                # File size
                if not asset.size:
                    asset.size = asset.local_path.stat().st_size
                
                # Color analysis
                colors = self._extract_dominant_colors(img)
                if colors:
                    # Store color info in a simple format
                    asset.alt_text = f"Dominant colors: {', '.join(colors)}"
                
        except Exception as e:
            pass
    
    def _extract_dominant_colors(self, img: Image.Image, num_colors: int = 5) -> List[str]:
        """Extract dominant colors from an image."""
        try:
            # Convert to RGB if necessary
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Resize for faster processing
            img.thumbnail((150, 150))
            
            # Convert to numpy array
            img_array = np.array(img)
            
            # Reshape to list of pixels
            pixels = img_array.reshape(-1, 3)
            
            # Use k-means clustering to find dominant colors
            from sklearn.cluster import KMeans
            
            kmeans = KMeans(n_clusters=num_colors, random_state=42, n_init=10)
            kmeans.fit(pixels)
            
            # Convert colors to hex
            colors = []
            for color in kmeans.cluster_centers_:
                hex_color = "#{:02x}{:02x}{:02x}".format(
                    int(color[0]), int(color[1]), int(color[2])
                )
                colors.append(hex_color)
            
            return colors
            
        except ImportError:
            # sklearn not available, use simpler method
            return self._extract_colors_simple(img)
        except Exception:
            return []
    
    def _extract_colors_simple(self, img: Image.Image) -> List[str]:
        """Simple color extraction without sklearn."""
        try:
            # Get the most common colors
            colors = img.getcolors(maxcolors=256*256*256)
            if colors:
                # Sort by frequency and take top 5
                colors.sort(key=lambda x: x[0], reverse=True)
                hex_colors = []
                
                for count, color in colors[:5]:
                    if isinstance(color, int):
                        # Grayscale
                        hex_color = "#{:02x}{:02x}{:02x}".format(color, color, color)
                    else:
                        # RGB
                        hex_color = "#{:02x}{:02x}{:02x}".format(*color[:3])
                    hex_colors.append(hex_color)
                
                return hex_colors
            
        except Exception:
            pass
        
        return []
    
    async def _analyze_css(self, asset: AssetInfo):
        """Analyze CSS assets."""
        try:
            with open(asset.local_path, 'r', encoding='utf-8', errors='ignore') as f:
                css_content = f.read()
            
            # Extract fonts, colors, etc.
            analysis = self._analyze_css_content(css_content)
            
            # Store analysis results (could be expanded)
            if not asset.size:
                asset.size = asset.local_path.stat().st_size
                
        except Exception:
            pass
    
    def _analyze_css_content(self, css_content: str) -> Dict[str, Any]:
        """Analyze CSS content for design patterns."""
        analysis = {
            'colors': [],
            'fonts': [],
            'media_queries': []
        }
        
        try:
            import re
            
            # Extract colors
            hex_colors = re.findall(r'#[0-9a-fA-F]{3,6}', css_content)
            rgb_colors = re.findall(r'rgb\([^)]+\)', css_content)
            analysis['colors'] = list(set(hex_colors + rgb_colors))
            
            # Extract font families
            font_matches = re.findall(r'font-family\s*:\s*([^;]+)', css_content, re.IGNORECASE)
            analysis['fonts'] = [font.strip().strip('"\'') for font in font_matches]
            
            # Extract media queries
            media_matches = re.findall(r'@media[^{]+', css_content, re.IGNORECASE)
            analysis['media_queries'] = media_matches
            
        except Exception:
            pass
        
        return analysis
    
    async def _analyze_javascript(self, asset: AssetInfo):
        """Analyze JavaScript assets."""
        try:
            with open(asset.local_path, 'r', encoding='utf-8', errors='ignore') as f:
                js_content = f.read()
            
            # Basic analysis
            if not asset.size:
                asset.size = asset.local_path.stat().st_size
            
            # Could analyze for frameworks, libraries, etc.
            
        except Exception:
            pass
    
    def _determine_asset_type(self, content_type: str, url: str) -> str:
        """Determine asset type from content type or URL."""
        content_type = content_type.lower()
        url = url.lower()
        
        if 'image' in content_type:
            return 'image'
        elif 'text/css' in content_type or url.endswith('.css'):
            return 'css'
        elif 'javascript' in content_type or url.endswith('.js'):
            return 'javascript'
        elif 'font' in content_type or any(url.endswith(ext) for ext in ['.woff', '.woff2', '.ttf', '.otf']):
            return 'font'
        elif 'video' in content_type:
            return 'video'
        elif 'audio' in content_type:
            return 'audio'
        elif 'application/pdf' in content_type:
            return 'pdf'
        else:
            return 'other'
    
    def _get_extension_from_content_type(self, content_type: str) -> str:
        """Get file extension from content type."""
        extensions = {
            'image/jpeg': '.jpg',
            'image/png': '.png',
            'image/gif': '.gif',
            'image/svg+xml': '.svg',
            'image/webp': '.webp',
            'text/css': '.css',
            'application/javascript': '.js',
            'text/javascript': '.js',
            'font/woff': '.woff',
            'font/woff2': '.woff2',
            'font/ttf': '.ttf',
            'application/pdf': '.pdf',
        }
        
        return extensions.get(content_type.lower(), '.bin')
    
    def get_asset_summary(self, site: Site) -> Dict[str, Any]:
        """Generate summary of all assets across the site."""
        summary = {
            'total_assets': 0,
            'by_type': {},
            'total_size': 0,
            'largest_assets': [],
            'most_common_types': []
        }
        
        all_assets = []
        for page in site.pages.values():
            all_assets.extend(page.assets)
        
        summary['total_assets'] = len(all_assets)
        
        # Group by type
        type_counts = {}
        type_sizes = {}
        
        for asset in all_assets:
            asset_type = asset.type
            type_counts[asset_type] = type_counts.get(asset_type, 0) + 1
            
            if asset.size:
                type_sizes[asset_type] = type_sizes.get(asset_type, 0) + asset.size
                summary['total_size'] += asset.size
        
        summary['by_type'] = {
            'counts': type_counts,
            'sizes': type_sizes
        }
        
        # Find largest assets
        assets_with_size = [asset for asset in all_assets if asset.size]
        assets_with_size.sort(key=lambda x: x.size, reverse=True)
        summary['largest_assets'] = [
            {
                'url': asset.url,
                'type': asset.type,
                'size': asset.size
            }
            for asset in assets_with_size[:10]
        ]
        
        # Most common types
        summary['most_common_types'] = sorted(
            type_counts.items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:5]
        
        return summary