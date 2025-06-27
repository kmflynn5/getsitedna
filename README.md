# GetSiteDNA

**Comprehensive website analysis tool for AI-assisted reconstruction and modernization**

GetSiteDNA is a powerful Python tool that analyzes existing websites and generates detailed specifications for AI-assisted reconstruction. It extracts design systems, content structures, UX patterns, and technical requirements to enable seamless website modernization with modern frameworks.

## ✨ Features

- 🕷️ **Intelligent Crawling**: Static and dynamic content extraction with JavaScript rendering
- 🎨 **Design Analysis**: Automatic color palette, typography, and component identification
- 📝 **Content Extraction**: Smart content categorization and structure analysis
- 🧩 **Pattern Recognition**: UX component and layout pattern detection
- 🚀 **Performance Optimized**: Concurrent processing with intelligent caching
- 📊 **Multiple Outputs**: JSON specifications and human-readable Markdown documentation
- 🔧 **Interactive Mode**: Guided analysis with customizable preferences
- ✅ **Validation**: Built-in output validation and quality assurance

## 🚀 Quick Start

### Installation

```bash
# Install from PyPI (when available)
pip install getsitedna

# Or install from source
git clone https://github.com/yourusername/getsitedna.git
cd getsitedna
pip install -e .
```

### Basic Usage

```bash
# Analyze a website with default settings
getsitedna analyze https://example.com

# Customize analysis depth and output
getsitedna analyze https://example.com --depth 3 --max-pages 100 --output ./my-analysis

# Interactive mode with guided prompts
getsitedna analyze https://example.com --interactive

# Use specific browser engine
getsitedna analyze https://example.com --browser firefox
```

### Performance Management

```bash
# Check performance settings and cache status
getsitedna performance status

# Configure performance settings
getsitedna performance configure --workers 8 --batch-size 10

# Clear cache
getsitedna performance clear-cache

# Run benchmark
getsitedna performance benchmark
```

## 📖 Documentation

### Command Reference

#### analyze
Analyze a website and generate comprehensive specifications.

```bash
getsitedna analyze [URL] [OPTIONS]
```

**Options:**
- `--output, -o`: Output directory (default: ./analysis)
- `--depth, -d`: Maximum crawling depth (default: 2)
- `--max-pages, -p`: Maximum pages to analyze (default: 50)
- `--include-assets/--no-assets`: Include asset extraction (default: True)
- `--interactive, -i`: Interactive mode with prompts
- `--browser`: Browser engine (chromium/firefox/webkit)

#### performance
Manage performance settings and cache.

```bash
getsitedna performance [COMMAND]
```

**Commands:**
- `status`: Show current settings and cache statistics
- `configure`: Update performance settings
- `cache-config`: Configure cache settings
- `clear-cache`: Clear all cached data
- `reset`: Reset to default settings
- `benchmark`: Run performance benchmark

#### validate-analysis
Validate analysis output structure and completeness.

```bash
getsitedna validate-analysis [ANALYSIS_DIR]
```

### Configuration

GetSiteDNA supports configuration through:
- Configuration files (`~/.getsitedna/config.json`)
- Environment variables
- CLI options

#### Environment Variables

```bash
# Cache settings
export GETSITEDNA_CACHE_ENABLED=true
export GETSITEDNA_CACHE_TTL=3600
export GETSITEDNA_CACHE_MAX_SIZE=104857600  # 100MB

# Performance settings
export GETSITEDNA_MAX_WORKERS=4
export GETSITEDNA_BATCH_SIZE=5

# Feature flags
export GETSITEDNA_ENABLE_CACHING=true
export GETSITEDNA_DEBUG_MODE=false
```

## 🔧 Advanced Usage

### Python API

```python
from getsitedna.core.analyzer import analyze_website
from getsitedna.models.schemas import CrawlConfig, AnalysisMetadata
from pathlib import Path

# Basic analysis
site = await analyze_website("https://example.com")

# Advanced configuration
config = {
    "crawl_config": CrawlConfig(
        max_depth=3,
        max_pages=100,
        respect_robots_txt=True
    ),
    "metadata": AnalysisMetadata(
        analysis_philosophy="comprehensive",
        target_framework="next_js_tailwind"
    ),
    "use_dynamic_crawler": True,
    "download_assets": True
}

site = await analyze_website(
    "https://example.com",
    config=config,
    output_dir=Path("./analysis")
)

# Access results
print(f"Analyzed {len(site.pages)} pages")
print(f"Found {len(site.global_color_palette)} colors")
print(f"Identified {len(site.component_specifications)} components")
```

### Interactive Analysis

```python
from getsitedna.cli.interactive import run_interactive_mode
from pathlib import Path

# Run interactive analysis
config = run_interactive_mode("https://example.com", Path("./output"))
if config:
    site = await analyze_website(config["url"], config=config)
```

## 📊 Output Structure

GetSiteDNA generates comprehensive analysis results:

```
analysis/
├── specification.json          # Complete site specification
├── site_data.json             # Site metadata and statistics
├── pages_data.json            # Individual page analyses
├── validation_report.json     # Quality validation results
├── summary.json               # Analysis summary
├── README.md                  # Human-readable overview
├── TECHNICAL_SPECIFICATION.md # Technical implementation guide
├── COMPONENTS.md              # Component library documentation
├── DESIGN_SYSTEM.md          # Design system specification
├── IMPLEMENTATION.md         # Step-by-step implementation guide
└── pages/                    # Individual page analyses
    ├── index.md
    ├── about.md
    └── ...
```

### Key Output Files

#### specification.json
Complete technical specification including:
- Design intent and philosophy
- Component specifications
- Design system (colors, typography, spacing)
- Technical modernization requirements
- Experience patterns and UX guidelines

#### README.md
Executive summary with:
- Site overview and statistics
- Key findings and recommendations
- Quick start implementation guide
- Technology stack recommendations

#### TECHNICAL_SPECIFICATION.md
Detailed technical documentation:
- Framework-specific implementation details
- Performance requirements
- Accessibility guidelines
- SEO recommendations

## 🎯 Use Cases

### Website Modernization
- Analyze legacy websites for modern framework migration
- Extract design systems for consistent UI implementation
- Identify performance optimization opportunities

### Competitive Analysis
- Study competitor website structures and patterns
- Extract design trends and UX patterns
- Analyze content strategies and site architectures

### Design System Creation
- Generate design tokens from existing websites
- Document component libraries and patterns
- Create style guides and design specifications

### AI-Assisted Development
- Provide detailed specifications for AI code generation
- Enable accurate website reconstruction with modern tools
- Generate implementation roadmaps and technical requirements

## 🔍 Analysis Capabilities

### Content Analysis
- **Text Content**: Headings, paragraphs, navigation, CTAs
- **Structure**: Layout patterns, content hierarchy
- **SEO Elements**: Meta tags, structured data, accessibility
- **Forms**: Field analysis, validation patterns

### Design Analysis
- **Color Extraction**: Dominant colors, usage patterns, accessibility
- **Typography**: Font families, sizes, weights, line heights
- **Spacing**: Margins, padding, layout grids
- **Components**: Buttons, cards, modals, navigation patterns

### Technical Analysis
- **Framework Detection**: JavaScript libraries and frameworks
- **Performance Metrics**: Load times, resource sizes
- **API Discovery**: Endpoint identification and analysis
- **Asset Inventory**: Images, stylesheets, scripts

### UX Pattern Recognition
- **Layout Patterns**: Header/footer, sidebar, grid layouts
- **Navigation Patterns**: Mega menus, breadcrumbs, pagination
- **Content Patterns**: Card layouts, list views, galleries
- **Interaction Patterns**: Modals, tooltips, accordions

## ⚡ Performance Features

### Intelligent Caching
- **File-based Cache**: Persistent storage with TTL support
- **Memory Cache**: Fast in-memory caching for frequent data
- **Cache Management**: CLI tools for cache monitoring and cleanup

### Concurrent Processing
- **Batch Processing**: Optimized batch operations with resource management
- **Adaptive Throttling**: Automatic resource usage optimization
- **Progress Tracking**: Real-time analysis progress monitoring

### Resource Optimization
- **Memory Management**: Intelligent garbage collection and memory monitoring
- **CPU Optimization**: Adaptive processing based on system resources
- **Configurable Limits**: Customizable concurrency and resource thresholds

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/getsitedna

# Run specific test categories
pytest tests/test_crawlers.py
pytest tests/test_extractors.py
pytest tests/test_performance.py
```

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Setup

```bash
# Clone repository
git clone https://github.com/yourusername/getsitedna.git
cd getsitedna

# Install development dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install

# Run tests
pytest
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with [Playwright](https://playwright.dev/) for dynamic content extraction
- Uses [BeautifulSoup](https://www.crummy.com/software/BeautifulSoup/) for HTML parsing
- Powered by [Pydantic](https://pydantic.dev/) for data validation
- CLI built with [Click](https://click.palletsprojects.com/) and [Rich](https://rich.readthedocs.io/)

## 📞 Support

- 📖 [Documentation](https://getsitedna.readthedocs.io/)
- 🐛 [Issue Tracker](https://github.com/yourusername/getsitedna/issues)
- 💬 [Discussions](https://github.com/yourusername/getsitedna/discussions)

---

**GetSiteDNA** - Transforming website analysis for the AI era 🚀
