"""API endpoint discovery and analysis module."""

import re
import json
from typing import Dict, List, Optional, Set, Any, Tuple
from urllib.parse import urljoin, urlparse
from collections import defaultdict

from bs4 import BeautifulSoup
import requests

from ..models.page import Page
from ..models.site import Site


class APIDiscovery:
    """Discover and analyze API endpoints from web pages."""
    
    def __init__(self):
        self.api_patterns = [
            # REST API patterns
            r'/api/v?\d*/[\w/-]+',
            r'/rest/[\w/-]+',
            r'/services/[\w/-]+',
            
            # GraphQL patterns
            r'/graphql/?',
            r'/graph/?',
            
            # Common API paths
            r'/data/[\w/-]+',
            r'/feed/[\w/-]*',
            r'/json/[\w/-]*',
            r'/ajax/[\w/-]+',
            
            # WordPress REST API
            r'/wp-json/[\w/-]+',
            
            # Specific API services
            r'/search\.json',
            r'/sitemap\.xml',
            r'/rss\.xml',
            r'/atom\.xml',
        ]
        
        # Common API response indicators
        self.api_indicators = [
            'application/json',
            'application/xml',
            'text/xml',
            'application/rss+xml',
            'application/atom+xml',
            'application/hal+json',
            'application/vnd.api+json'
        ]
        
        # HTTP methods to test
        self.http_methods = ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS']
        
    def discover_apis(self, site: Site) -> Site:
        """Discover API endpoints across all pages in the site."""
        discovered_endpoints = set()
        api_metadata = {}
        
        # Collect endpoints from all pages
        for page in site.crawled_pages:
            page_endpoints = self._extract_page_apis(page)
            discovered_endpoints.update(page_endpoints.keys())
            api_metadata.update(page_endpoints)
        
        # Additional discovery methods
        additional_endpoints = self._discover_common_endpoints(site.base_url)
        discovered_endpoints.update(additional_endpoints.keys())
        api_metadata.update(additional_endpoints)
        
        # Analyze discovered endpoints
        analyzed_endpoints = self._analyze_endpoints(discovered_endpoints, api_metadata, site.base_url)
        
        # Store results in site
        site.technical_modernization.api_endpoints = list(analyzed_endpoints.keys())
        
        # Add API documentation to modernization recommendations
        if analyzed_endpoints:
            api_docs = self._generate_api_documentation(analyzed_endpoints)
            site.technical_modernization.api_documentation = api_docs
        
        return site
    
    def _extract_page_apis(self, page: Page) -> Dict[str, Dict[str, Any]]:
        """Extract API endpoints from a single page."""
        endpoints = {}
        
        if not page.html_content:
            return endpoints
        
        # Parse HTML content
        soup = BeautifulSoup(page.html_content, 'html.parser')
        
        # Extract from JavaScript code
        js_endpoints = self._extract_from_javascript(page.html_content, str(page.url))
        endpoints.update(js_endpoints)
        
        # Extract from data attributes
        data_endpoints = self._extract_from_data_attributes(soup, str(page.url))
        endpoints.update(data_endpoints)
        
        # Extract from form actions
        form_endpoints = self._extract_from_forms(soup, str(page.url))
        endpoints.update(form_endpoints)
        
        # Extract from AJAX requests (already captured during crawling)
        if page.technical.api_endpoints:
            for endpoint in page.technical.api_endpoints:
                endpoints[endpoint] = {
                    'source': 'network_request',
                    'method': 'GET',  # Default assumption
                    'page_url': str(page.url)
                }
        
        return endpoints
    
    def _extract_from_javascript(self, html_content: str, page_url: str) -> Dict[str, Dict[str, Any]]:
        """Extract API endpoints from JavaScript code."""
        endpoints = {}
        
        # Find script tags
        soup = BeautifulSoup(html_content, 'html.parser')
        scripts = soup.find_all('script')
        
        for script in scripts:
            if script.string:
                js_content = script.string
                
                # Look for fetch() calls
                fetch_pattern = r'fetch\s*\(\s*[\'"`]([^\'"`]+)[\'"`]'
                fetch_matches = re.findall(fetch_pattern, js_content, re.IGNORECASE)
                
                for match in fetch_matches:
                    endpoint = self._resolve_endpoint(match, page_url)
                    if self._is_api_endpoint(endpoint):
                        endpoints[endpoint] = {
                            'source': 'javascript_fetch',
                            'method': 'GET',
                            'page_url': page_url
                        }
                
                # Look for XMLHttpRequest calls
                xhr_pattern = r'\.open\s*\(\s*[\'"`](\w+)[\'"`]\s*,\s*[\'"`]([^\'"`]+)[\'"`]'
                xhr_matches = re.findall(xhr_pattern, js_content, re.IGNORECASE)
                
                for method, url in xhr_matches:
                    endpoint = self._resolve_endpoint(url, page_url)
                    if self._is_api_endpoint(endpoint):
                        endpoints[endpoint] = {
                            'source': 'javascript_xhr',
                            'method': method.upper(),
                            'page_url': page_url
                        }
                
                # Look for axios calls
                axios_pattern = r'axios\s*\.\s*(\w+)\s*\(\s*[\'"`]([^\'"`]+)[\'"`]'
                axios_matches = re.findall(axios_pattern, js_content, re.IGNORECASE)
                
                for method, url in axios_matches:
                    endpoint = self._resolve_endpoint(url, page_url)
                    if self._is_api_endpoint(endpoint):
                        endpoints[endpoint] = {
                            'source': 'javascript_axios',
                            'method': method.upper(),
                            'page_url': page_url
                        }
                
                # Look for jQuery AJAX calls
                jquery_pattern = r'\$\.(?:get|post|ajax)\s*\(\s*[\'"`]([^\'"`]+)[\'"`]'
                jquery_matches = re.findall(jquery_pattern, js_content, re.IGNORECASE)
                
                for match in jquery_matches:
                    endpoint = self._resolve_endpoint(match, page_url)
                    if self._is_api_endpoint(endpoint):
                        endpoints[endpoint] = {
                            'source': 'javascript_jquery',
                            'method': 'GET',
                            'page_url': page_url
                        }
        
        return endpoints
    
    def _extract_from_data_attributes(self, soup: BeautifulSoup, page_url: str) -> Dict[str, Dict[str, Any]]:
        """Extract API endpoints from data attributes."""
        endpoints = {}
        
        # Look for data-url, data-api, data-endpoint attributes
        data_attrs = ['data-url', 'data-api', 'data-endpoint', 'data-src', 'data-action']
        
        for attr in data_attrs:
            elements = soup.find_all(attrs={attr: True})
            
            for element in elements:
                url = element.get(attr)
                if url:
                    endpoint = self._resolve_endpoint(url, page_url)
                    if self._is_api_endpoint(endpoint):
                        endpoints[endpoint] = {
                            'source': f'data_attribute_{attr}',
                            'method': 'GET',
                            'page_url': page_url,
                            'element': element.name
                        }
        
        return endpoints
    
    def _extract_from_forms(self, soup: BeautifulSoup, page_url: str) -> Dict[str, Dict[str, Any]]:
        """Extract API endpoints from form actions."""
        endpoints = {}
        
        forms = soup.find_all('form', action=True)
        
        for form in forms:
            action = form.get('action')
            method = form.get('method', 'GET').upper()
            
            if action:
                endpoint = self._resolve_endpoint(action, page_url)
                if self._is_api_endpoint(endpoint):
                    endpoints[endpoint] = {
                        'source': 'form_action',
                        'method': method,
                        'page_url': page_url,
                        'form_fields': len(form.find_all(['input', 'textarea', 'select']))
                    }
        
        return endpoints
    
    def _discover_common_endpoints(self, base_url: str) -> Dict[str, Dict[str, Any]]:
        """Discover common API endpoints by testing standard paths."""
        endpoints = {}
        
        common_paths = [
            '/api',
            '/api/v1',
            '/api/v2',
            '/rest',
            '/graphql',
            '/wp-json/wp/v2',
            '/sitemap.xml',
            '/robots.txt',
            '/feed',
            '/rss',
            '/atom.xml',
            '/.well-known/security.txt',
            '/manifest.json',
            '/sw.js'
        ]
        
        for path in common_paths:
            endpoint = urljoin(base_url, path)
            
            # Test if endpoint exists
            try:
                response = requests.head(endpoint, timeout=5, allow_redirects=True)
                if response.status_code < 400:
                    endpoints[endpoint] = {
                        'source': 'common_path_discovery',
                        'method': 'GET',
                        'status_code': response.status_code,
                        'content_type': response.headers.get('content-type', ''),
                        'exists': True
                    }
            except Exception:
                # Endpoint doesn't exist or is unreachable
                pass
        
        return endpoints
    
    def _analyze_endpoints(self, endpoints: Set[str], metadata: Dict[str, Dict], base_url: str) -> Dict[str, Dict[str, Any]]:
        """Analyze discovered endpoints for detailed information."""
        analyzed = {}
        
        for endpoint in endpoints:
            analysis = metadata.get(endpoint, {})
            
            # Categorize endpoint
            analysis['category'] = self._categorize_endpoint(endpoint)
            
            # Determine API type
            analysis['api_type'] = self._determine_api_type(endpoint)
            
            # Check if it's internal or external
            analysis['is_internal'] = self._is_internal_endpoint(endpoint, base_url)
            
            # Analyze endpoint structure
            analysis['path_structure'] = self._analyze_path_structure(endpoint)
            
            # Test endpoint if it's internal and safe
            if analysis['is_internal'] and analysis.get('method', 'GET') == 'GET':
                test_result = self._test_endpoint(endpoint)
                analysis.update(test_result)
            
            analyzed[endpoint] = analysis
        
        return analyzed
    
    def _categorize_endpoint(self, endpoint: str) -> str:
        """Categorize the endpoint based on its path."""
        endpoint_lower = endpoint.lower()
        
        if 'graphql' in endpoint_lower:
            return 'graphql'
        elif '/api/' in endpoint_lower or endpoint_lower.endswith('/api'):
            return 'rest_api'
        elif any(feed in endpoint_lower for feed in ['rss', 'atom', 'feed']):
            return 'feed'
        elif 'sitemap' in endpoint_lower:
            return 'sitemap'
        elif 'search' in endpoint_lower:
            return 'search'
        elif any(auth in endpoint_lower for auth in ['login', 'auth', 'oauth']):
            return 'authentication'
        elif 'wp-json' in endpoint_lower:
            return 'wordpress_api'
        elif any(ext in endpoint_lower for ext in ['.json', '.xml']):
            return 'data_file'
        else:
            return 'other'
    
    def _determine_api_type(self, endpoint: str) -> str:
        """Determine the type of API based on URL patterns."""
        if '/graphql' in endpoint.lower():
            return 'GraphQL'
        elif '/rest' in endpoint.lower():
            return 'REST'
        elif '/soap' in endpoint.lower():
            return 'SOAP'
        elif endpoint.endswith('.xml'):
            return 'XML'
        elif endpoint.endswith('.json'):
            return 'JSON'
        else:
            return 'Unknown'
    
    def _is_internal_endpoint(self, endpoint: str, base_url: str) -> bool:
        """Check if endpoint belongs to the same domain."""
        endpoint_domain = urlparse(endpoint).netloc
        base_domain = urlparse(base_url).netloc
        return endpoint_domain == base_domain or not endpoint_domain
    
    def _analyze_path_structure(self, endpoint: str) -> Dict[str, Any]:
        """Analyze the structure of the endpoint path."""
        parsed = urlparse(endpoint)
        path_parts = [part for part in parsed.path.split('/') if part]
        
        structure = {
            'depth': len(path_parts),
            'has_version': any(re.match(r'v\d+', part) for part in path_parts),
            'has_id_pattern': any(re.match(r'\d+', part) for part in path_parts),
            'file_extension': None,
            'query_params': len(parsed.query.split('&')) if parsed.query else 0
        }
        
        # Check for file extension
        if path_parts:
            last_part = path_parts[-1]
            if '.' in last_part:
                structure['file_extension'] = last_part.split('.')[-1]
        
        return structure
    
    def _test_endpoint(self, endpoint: str) -> Dict[str, Any]:
        """Test an endpoint to gather additional information."""
        test_result = {
            'tested': False,
            'accessible': False,
            'response_type': None,
            'requires_auth': False
        }
        
        try:
            response = requests.head(endpoint, timeout=5, allow_redirects=True)
            test_result['tested'] = True
            test_result['status_code'] = response.status_code
            test_result['accessible'] = response.status_code < 400
            test_result['content_type'] = response.headers.get('content-type', '')
            
            # Check if it requires authentication
            if response.status_code in [401, 403]:
                test_result['requires_auth'] = True
            
            # Determine response type
            content_type = response.headers.get('content-type', '').lower()
            if 'json' in content_type:
                test_result['response_type'] = 'JSON'
            elif 'xml' in content_type:
                test_result['response_type'] = 'XML'
            elif 'html' in content_type:
                test_result['response_type'] = 'HTML'
            else:
                test_result['response_type'] = 'Other'
            
        except Exception as e:
            test_result['error'] = str(e)
        
        return test_result
    
    def _resolve_endpoint(self, url: str, base_url: str) -> str:
        """Resolve relative URLs to absolute URLs."""
        if url.startswith(('http://', 'https://')):
            return url
        else:
            return urljoin(base_url, url)
    
    def _is_api_endpoint(self, url: str) -> bool:
        """Check if a URL looks like an API endpoint."""
        url_lower = url.lower()
        
        # Check against patterns
        for pattern in self.api_patterns:
            if re.search(pattern, url_lower):
                return True
        
        # Check for API indicators in the URL
        api_keywords = ['api', 'rest', 'graphql', 'json', 'xml', 'ajax', 'data', 'service']
        return any(keyword in url_lower for keyword in api_keywords)
    
    def _generate_api_documentation(self, endpoints: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Generate API documentation from discovered endpoints."""
        documentation = {
            'total_endpoints': len(endpoints),
            'categories': defaultdict(list),
            'api_types': defaultdict(int),
            'authentication_required': [],
            'public_endpoints': [],
            'recommendations': []
        }
        
        for endpoint, info in endpoints.items():
            category = info.get('category', 'other')
            documentation['categories'][category].append({
                'url': endpoint,
                'method': info.get('method', 'GET'),
                'source': info.get('source', 'unknown')
            })
            
            api_type = info.get('api_type', 'Unknown')
            documentation['api_types'][api_type] += 1
            
            if info.get('requires_auth'):
                documentation['authentication_required'].append(endpoint)
            elif info.get('accessible'):
                documentation['public_endpoints'].append(endpoint)
        
        # Generate recommendations
        if documentation['categories']['rest_api']:
            documentation['recommendations'].append(
                "REST API endpoints detected. Consider implementing OpenAPI/Swagger documentation."
            )
        
        if documentation['categories']['graphql']:
            documentation['recommendations'].append(
                "GraphQL endpoint detected. Implement GraphQL introspection and playground."
            )
        
        if len(documentation['authentication_required']) > 0:
            documentation['recommendations'].append(
                f"{len(documentation['authentication_required'])} endpoints require authentication. "
                "Implement proper API key management and OAuth flows."
            )
        
        return dict(documentation)


def discover_site_apis(site: Site) -> Site:
    """Entry point for API discovery across a site."""
    api_discovery = APIDiscovery()
    return api_discovery.discover_apis(site)