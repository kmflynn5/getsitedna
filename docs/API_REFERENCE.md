# GetSiteDNA API Reference

This document provides comprehensive API documentation for GetSiteDNA.

## Table of Contents

- [Core API](#core-api)
- [Data Models](#data-models)
- [Analyzers](#analyzers)
- [Crawlers](#crawlers)
- [Extractors](#extractors)
- [Outputs](#outputs)
- [Utilities](#utilities)
- [CLI Interface](#cli-interface)

## Core API

### analyze_website()

The main entry point for website analysis.

```python
async def analyze_website(
    url: str, 
    config: Optional[Dict[str, Any]] = None,
    output_dir: Optional[Path] = None
) -> Site
```

**Parameters:**
- `url` (str): The website URL to analyze
- `config` (Dict, optional): Configuration dictionary
- `output_dir` (Path, optional): Output directory for results

**Returns:**
- `Site`: Complete site analysis object

**Example:**
```python
from getsitedna.core.analyzer import analyze_website

# Basic usage
site = await analyze_website("https://example.com")

# With configuration
config = {
    "crawl_config": {
        "max_depth": 3,
        "max_pages": 50
    },
    "use_dynamic_crawler": True
}
site = await analyze_website("https://example.com", config=config)
```

### SiteAnalyzer

Advanced analyzer class for customized analysis workflows.

```python
class SiteAnalyzer:
    def __init__(
        self, 
        output_directory: Optional[Path] = None,
        use_dynamic_crawler: bool = True,
        generate_markdown: bool = True,
        download_assets: bool = False
    )
```

**Methods:**

#### analyze_site()
```python
async def analyze_site(
    self, 
    url: str, 
    config: Optional[CrawlConfig] = None,
    metadata: Optional[AnalysisMetadata] = None
) -> Site
```

Perform complete site analysis with custom configuration.

#### get_analysis_summary()
```python
def get_analysis_summary(self) -> Dict[str, Any]
```

Get analysis quality metrics and recommendations.

**Example:**
```python
from getsitedna.core.analyzer import SiteAnalyzer

analyzer = SiteAnalyzer(
    output_directory=Path("./results"),
    use_dynamic_crawler=True,
    download_assets=True
)

site = await analyzer.analyze_site("https://example.com")
summary = analyzer.get_analysis_summary()
```

## Data Models

### Site

Main site model containing all analysis results.

```python
class Site(BaseModel):
    base_url: HttpUrl
    domain: str
    pages: Dict[str, Page]
    global_color_palette: List[ColorInfo]
    global_typography: List[FontInfo]
    component_specifications: List[ComponentSpec]
    # ... additional fields
```

**Key Properties:**
- `crawled_pages`: Iterator over successfully crawled pages
- `failed_pages`: Iterator over pages that failed to crawl
- `page_count`: Total number of discovered pages

**Methods:**
- `add_page(page: Page)`: Add a page to the site
- `get_page(url: str) -> Optional[Page]`: Get page by URL
- `has_page(url: str) -> bool`: Check if page exists
- `get_site_summary() -> Dict`: Get site statistics

### Page

Individual page model with analysis results.

```python
class Page(BaseModel):
    url: HttpUrl
    title: Optional[str]
    status: CrawlStatus
    content: PageContent
    design: DesignAnalysis
    structure: StructureAnalysis
    # ... additional fields
```

**Key Properties:**
- `html_content`: Raw HTML content
- `rendered_html`: JavaScript-rendered HTML (if dynamic)
- `assets`: List of page assets
- `internal_links`: Links to other site pages
- `external_links`: Links to external sites

### Configuration Models

#### CrawlConfig
```python
class CrawlConfig(BaseModel):
    max_depth: int = 2
    max_pages: int = 50
    rate_limit_delay: float = 1.0
    timeout: int = 30
    respect_robots_txt: bool = True
    max_concurrent_requests: int = 5
```

#### AnalysisMetadata
```python
class AnalysisMetadata(BaseModel):
    analysis_philosophy: AnalysisPhilosophy
    target_framework: TargetFramework
    accessibility_level: AccessibilityLevel
    include_content_analysis: bool = True
    include_design_analysis: bool = True
    # ... additional fields
```

### Content Models

#### ColorInfo
```python
class ColorInfo(BaseModel):
    hex: str
    rgb: Tuple[int, int, int]
    hsl: Tuple[int, int, int]
    name: Optional[str]
    usage_context: List[str]
    frequency: int
    accessibility_score: Optional[float]
```

#### FontInfo
```python
class FontInfo(BaseModel):
    family: str
    weight: Union[int, str]
    size: Optional[str]
    line_height: Optional[str]
    usage_context: List[str]
    frequency: int
```

#### ComponentSpec
```python
class ComponentSpec(BaseModel):
    component_name: str
    component_type: ComponentType
    description: str
    props: Dict[str, Any]
    styling: Dict[str, Any]
    implementation_notes: str
    framework_specific: Dict[str, Any]
```

## Analyzers

### ContentExtractor

Extract and analyze text content from pages.

```python
class ContentExtractor:
    async def extract_content(self, page: Page) -> Page
    def extract_key_phrases(self, text: str, max_phrases: int = 10) -> List[str]
    def analyze_content_sentiment(self, text: str) -> str
```

**Example:**
```python
from getsitedna.extractors.content import ContentExtractor

extractor = ContentExtractor()
page = await extractor.extract_content(page)

# Access extracted content
headings = page.content.text_content[ContentType.HEADING]
navigation = page.content.text_content[ContentType.NAVIGATION]
```

### DesignExtractor

Extract design system elements from pages.

```python
class DesignExtractor:
    async def extract_design(self, page: Page) -> Page
    async def analyze_global_design_system(self, site: Site) -> Site
    def _extract_css_colors(self, css_url: str, colors: Dict) -> None
```

**Example:**
```python
from getsitedna.extractors.design import DesignExtractor

extractor = DesignExtractor()
page = await extractor.extract_design(page)

# Access design elements
colors = page.design.color_palette
fonts = page.design.typography
```

### StructureExtractor

Analyze page structure and layout patterns.

```python
class StructureExtractor:
    async def extract_structure(self, page: Page) -> Page
    def _identify_components(self, soup: BeautifulSoup) -> List[ComponentSpec]
    def _analyze_layout(self, soup: BeautifulSoup) -> str
```

## Crawlers

### StaticCrawler

BeautifulSoup-based crawler for traditional websites.

```python
class StaticCrawler:
    def __init__(self, site: Site)
    async def crawl_site(self) -> Site
    async def _crawl_page(self, page: Page) -> None
```

**Example:**
```python
from getsitedna.crawlers.static_crawler import StaticCrawler

crawler = StaticCrawler(site)
site = await crawler.crawl_site()
```

### DynamicCrawler

Playwright-based crawler for JavaScript-heavy sites.

```python
class DynamicCrawler:
    def __init__(self, site: Site)
    async def crawl_site(self) -> Site
    async def _detect_frameworks(self, page: PlaywrightPage) -> List[str]
```

**Example:**
```python
from getsitedna.crawlers.dynamic_crawler import DynamicCrawler

crawler = DynamicCrawler(site)
site = await crawler.crawl_site()
```

## Outputs

### JSONWriter

Generate JSON specifications and data files.

```python
class JSONWriter:
    def __init__(self, output_directory: Path)
    def write_site_analysis(self, site: Site) -> Dict[str, Path]
    def write_page_analysis(self, page: Page) -> Path
```

**Generated Files:**
- `specification.json`: Complete site specification
- `site_data.json`: Site metadata and statistics
- `pages_data.json`: Individual page analyses
- `validation_report.json`: Quality validation results

### MarkdownWriter

Generate human-readable documentation.

```python
class MarkdownWriter:
    def __init__(self, output_directory: Path)
    def write_documentation(self, site: Site) -> Dict[str, Path]
```

**Generated Files:**
- `README.md`: Executive summary
- `TECHNICAL_SPECIFICATION.md`: Technical details
- `COMPONENTS.md`: Component library
- `DESIGN_SYSTEM.md`: Design system specs
- `IMPLEMENTATION.md`: Implementation guide

## Utilities

### Caching

#### CacheManager
```python
class CacheManager:
    def __init__(
        self, 
        cache_dir: str = ".getsitedna_cache",
        default_ttl: int = 3600,
        max_size: int = 100 * 1024 * 1024
    )
    
    async def get(self, key: str, default: Any = None) -> Any
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool
    async def delete(self, key: str) -> bool
    async def clear(self) -> bool
```

#### @cached Decorator
```python
@cached(ttl=3600, use_memory=True)
async def expensive_operation(data: str) -> str:
    # Expensive computation
    return result
```

### Performance

#### ConcurrentProcessor
```python
class ConcurrentProcessor:
    def __init__(self, max_workers: int = None, use_process_pool: bool = False)
    
    async def process_batch(
        self, 
        items: List[Any], 
        process_func: Callable,
        batch_size: Optional[int] = None
    ) -> List[Any]
```

#### PerformanceMonitor
```python
class PerformanceMonitor:
    def start_monitoring(self) -> None
    def stop_monitoring(self, concurrent_tasks: int = 1) -> PerformanceMetrics
    def get_average_metrics(self) -> Optional[PerformanceMetrics]
```

### Error Handling

#### ErrorHandler
```python
class ErrorHandler:
    def __init__(self, logger_name: str = "getsitedna")
    
    def handle_error(
        self, 
        error: Exception, 
        context: Optional[Dict[str, Any]] = None
    ) -> AnalysisError
    
    def get_error_summary(self) -> Dict[str, Any]
    def should_continue(self, error: AnalysisError) -> bool
```

#### @retry_on_error Decorator
```python
@retry_on_error(
    config=RetryConfig(max_attempts=3, base_delay=2.0),
    exceptions=(NetworkError, TimeoutError)
)
async def unreliable_operation() -> str:
    # Operation that might fail
    return result
```

## CLI Interface

### Interactive Mode

```python
from getsitedna.cli.interactive import run_interactive_mode

config = run_interactive_mode("https://example.com", Path("./output"))
if config:
    site = await analyze_website(config["url"], config=config)
```

### Command Line Usage

```bash
# Basic analysis
getsitedna analyze https://example.com

# Advanced options
getsitedna analyze https://example.com \
  --depth 3 \
  --max-pages 100 \
  --interactive \
  --browser firefox \
  --output ./analysis

# Performance management
getsitedna performance status
getsitedna performance configure --workers 8
getsitedna performance clear-cache

# Validation
getsitedna validate-analysis ./analysis
```

## Configuration

### Environment Variables

```bash
# Cache settings
GETSITEDNA_CACHE_ENABLED=true
GETSITEDNA_CACHE_TTL=3600
GETSITEDNA_CACHE_MAX_SIZE=104857600

# Performance settings
GETSITEDNA_MAX_WORKERS=4
GETSITEDNA_BATCH_SIZE=5

# Feature flags
GETSITEDNA_ENABLE_CACHING=true
GETSITEDNA_DEBUG_MODE=false
```

### Configuration Files

Default location: `~/.getsitedna/config.json`

```json
{
  "cache": {
    "enabled": true,
    "default_ttl": 3600,
    "max_size": 104857600
  },
  "performance": {
    "max_concurrent_requests": 4,
    "batch_size": 5,
    "enable_monitoring": true
  },
  "enable_caching": true,
  "enable_concurrent_processing": true
}
```

## Error Handling

### Exception Hierarchy

```
AnalysisError (base)
├── NetworkError
├── ParsingError
├── BrowserError
├── ValidationError
└── RateLimitError
```

### Error Context

All errors include contextual information:

```python
try:
    site = await analyze_website("https://example.com")
except AnalysisError as e:
    print(f"Error: {e.message}")
    print(f"Category: {e.category}")
    print(f"Severity: {e.severity}")
    print(f"Context: {e.context}")
```

## Best Practices

### Performance Optimization

1. **Use Caching**: Enable caching for repeated analyses
2. **Batch Processing**: Process multiple items concurrently
3. **Resource Monitoring**: Monitor memory and CPU usage
4. **Adaptive Configuration**: Adjust settings based on site size

### Error Recovery

1. **Safe Execution**: Use SafeExecutor for critical operations
2. **Retry Logic**: Implement retry with exponential backoff
3. **Circuit Breaker**: Prevent cascade failures
4. **Graceful Degradation**: Continue analysis with partial failures

### Memory Management

1. **Streaming**: Process large sites in batches
2. **Cleanup**: Clear caches and temporary data
3. **Monitoring**: Track memory usage during analysis
4. **Limits**: Set appropriate page and depth limits

## Examples

See the `examples/` directory for comprehensive usage examples:

- `basic_usage.py`: Simple API usage patterns
- `api_examples.py`: Advanced API features
- `cli_examples.md`: Command-line usage examples

## Type Hints

GetSiteDNA uses comprehensive type hints throughout the codebase:

```python
from typing import Dict, List, Optional, Union, AsyncIterator
from pathlib import Path
from pydantic import HttpUrl

async def analyze_website(
    url: str, 
    config: Optional[Dict[str, Any]] = None,
    output_dir: Optional[Path] = None
) -> Site:
    ...
```

This enables excellent IDE support and static type checking with mypy.