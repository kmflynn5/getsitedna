"""URL and input validation utilities."""

import re
from typing import Optional
from urllib.parse import urlparse, urljoin
from pathlib import Path

import validators


def is_valid_url(url: str) -> bool:
    """Check if a URL is valid."""
    try:
        result = validators.url(url)
        return result is True
    except Exception:
        return False


def normalize_url(url: str) -> str:
    """Normalize a URL by adding protocol and removing trailing slashes."""
    if not url:
        return url
    
    # Add protocol if missing
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    
    # Remove trailing slash for consistency
    url = url.rstrip("/")
    
    return url


def get_domain(url: str) -> Optional[str]:
    """Extract domain from URL."""
    try:
        parsed = urlparse(url)
        return parsed.netloc
    except Exception:
        return None


def is_same_domain(url1: str, url2: str) -> bool:
    """Check if two URLs are from the same domain."""
    domain1 = get_domain(url1)
    domain2 = get_domain(url2)
    return domain1 == domain2 and domain1 is not None


def resolve_url(base_url: str, relative_url: str) -> str:
    """Resolve a relative URL against a base URL."""
    return urljoin(base_url, relative_url)


def is_crawlable_url(url: str, base_domain: str) -> bool:
    """Check if a URL should be crawled based on domain and file type."""
    if not is_valid_url(url):
        return False
    
    # Check if same domain
    url_domain = get_domain(url)
    if url_domain != base_domain:
        return False
    
    # Skip common non-HTML file types
    skip_extensions = {
        '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
        '.zip', '.tar', '.gz', '.rar', '.exe', '.dmg',
        '.jpg', '.jpeg', '.png', '.gif', '.svg', '.webp',
        '.mp3', '.mp4', '.avi', '.mov', '.wmv',
        '.css', '.js', '.json', '.xml', '.txt'
    }
    
    parsed = urlparse(url)
    path = parsed.path.lower()
    
    for ext in skip_extensions:
        if path.endswith(ext):
            return False
    
    # Skip common admin/system paths
    skip_paths = {
        '/admin', '/wp-admin', '/login', '/logout', '/register',
        '/api/', '/rss', '/feed', '/sitemap'
    }
    
    for skip_path in skip_paths:
        if skip_path in path:
            return False
    
    return True


def validate_output_path(path: str) -> bool:
    """Validate output directory path."""
    try:
        path_obj = Path(path)
        # Check if parent directory exists or can be created
        parent = path_obj.parent
        return parent.exists() or parent == path_obj
    except Exception:
        return False


def clean_filename(filename: str) -> str:
    """Clean a filename for safe filesystem usage."""
    # Remove or replace invalid characters
    cleaned = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # Remove multiple underscores
    cleaned = re.sub(r'_+', '_', cleaned)
    # Trim and remove leading/trailing underscores
    cleaned = cleaned.strip('_')
    # Ensure not empty
    if not cleaned:
        cleaned = 'unnamed'
    return cleaned