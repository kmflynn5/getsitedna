# GetSiteDNA - AI Assistant Context

This document provides context for AI assistants working on the GetSiteDNA project.

## Project Overview

GetSiteDNA is a comprehensive website analysis tool that crawls websites and generates modern implementation specifications for AI-assisted reconstruction. The tool analyzes design systems, content structure, UX patterns, and technical architecture to produce actionable specifications for rebuilding sites with modern frameworks.

## Project Status

**Current Phase: PRODUCTION READY**
- All core functionality implemented and tested
- Complete CLI interface with all commands functional
- Comprehensive validation scoring and error handling
- All analysis features working correctly
- Only remaining task: Package for PyPI distribution

## Development Notes

### Development Workflow Tips
- Use venv to test commands during development 

## Architecture Overview

### Core Components

1. **Data Models** (`src/getsitedna/models/`)
   - `schemas.py`: Pydantic models for all data structures
   - `site.py`: Main Site model orchestrating analysis

2. **Crawlers** (`src/getsitedna/crawlers/`)
   - `static_crawler.py`: BeautifulSoup-based for traditional sites
   - `dynamic_crawler.py`: Playwright-based for JavaScript-heavy sites

3. **Extractors** (`src/getsitedna/extractors/`)
   - `content.py`: Text content and structure analysis
   - `design.py`: Color, typography, and design system extraction
   - `structure.py`: Layout patterns and component identification
   - `assets.py`: Media files and resource management

4. **Core Logic** (`src/getsitedna/core/`)
   - `analyzer.py`: Main analysis orchestration
   - `api_discovery.py`: REST API endpoint detection

5. **CLI Interface** (`src/getsitedna/cli/`)
   - `main.py`: Click-based command interface
   - `interactive.py`: Guided analysis mode

6. **Output Generation** (`src/getsitedna/outputs/`)
   - `json_writer.py`: Technical specifications
   - `markdown_writer.py`: Human-readable documentation

7. **Utilities** (`src/getsitedna/utils/`)
   - `error_handling.py`: Comprehensive error management
   - `cache.py`: File and memory caching system
   - `performance.py`: Optimization and monitoring

## Key Features Implemented

### Analysis Capabilities
- ✅ Static HTML crawling with sitemap/robots.txt support
- ✅ Dynamic JavaScript rendering with Playwright
- ✅ Design system extraction (colors, fonts, spacing)
- ✅ Content categorization and structure analysis
- ✅ Component identification and specification
- ✅ API endpoint discovery
- ✅ SEO and accessibility analysis
- ✅ Performance metrics collection

### Output Formats
- ✅ JSON specifications for technical implementation
- ✅ Markdown documentation for human consumption
- ✅ Design system specifications
- ✅ Component library documentation
- ✅ Implementation guides for modern frameworks

### Performance & Reliability
- ✅ Multi-level caching (file + memory)
- ✅ Concurrent processing with batching
- ✅ Comprehensive error handling with retry logic
- ✅ Circuit breaker patterns for resilience
- ✅ Resource monitoring and adaptive throttling

### CLI Features
- ✅ Interactive mode with guided prompts
- ✅ Performance management commands
- ✅ Validation and quality assurance with scoring
- ✅ Summary generation in multiple formats
- ✅ Configuration file creation and management
- ✅ Extensive configuration options

## Technology Stack

### Core Dependencies
- **Python 3.8+** with full async/await support
- **Click** for CLI interface
- **Pydantic** for data validation and serialization
- **BeautifulSoup4** for HTML parsing
- **Playwright** for JavaScript rendering
- **aiohttp** for async HTTP requests
- **Rich** for console interface

### Development Tools
- **pytest** with async support for testing
- **mypy** for static type checking
- **Coverage** for test coverage analysis

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
GETSITEDNA_DEBUG_MODE=false
```

### Default Configuration Location
- `~/.getsitedna/config.json`

## Common Commands

### Basic Analysis
```bash
# Simple website analysis
getsitedna analyze https://example.com

# With custom configuration
getsitedna analyze https://example.com --depth 3 --max-pages 50 --interactive
```

### Performance Management
```bash
# Check performance status
getsitedna performance status

# Configure workers and caching
getsitedna performance configure --workers 4 --enable-caching

# Clear cache
getsitedna performance clear-cache
```

### Validation and Summary
```bash
# Validate analysis results
getsitedna validate ./analysis --detailed --output validation-report.json

# Generate summaries
getsitedna summary ./analysis --format console
getsitedna summary ./analysis --format json --output summary.json
getsitedna summary ./analysis --format markdown --output summary.md
```

### Configuration Management
```bash
# Create configuration file
getsitedna config init --output my-config.json

# Use configuration file
getsitedna analyze https://example.com --config my-config.json
```

## Testing

### Test Structure
- `tests/conftest.py`: Shared fixtures and configuration
- `tests/test_*.py`: Comprehensive test coverage for all modules
- `tests/integration/`: End-to-end integration tests

### Running Tests
```bash
# Run all tests
pytest

# With coverage
pytest --cov=src/getsitedna --cov-report=html

# Specific test file
pytest tests/test_analyzer.py -v
```

## Development Workflow

### Code Quality
- Type hints throughout codebase
- Comprehensive error handling
- Extensive logging and monitoring
- Performance optimization patterns

### Git Practices
- Structured commit messages with co-authorship
- Regular commits after major features
- Clean git history with meaningful messages

## Known Limitations & Considerations

### Current Constraints
- Playwright requires browser binaries (auto-installed)
- Memory usage scales with site size
- Rate limiting may affect large site analysis
- Some dynamic content may require specific browser configurations

### Future Enhancements (Post-PyPI)
- Plugin system for custom extractors
- Advanced AI integration for pattern recognition
- Distributed analysis for large-scale sites
- Integration with design tools and CMSs

## Troubleshooting

### Common Issues
1. **Memory Usage**: Adjust `max_workers` and `batch_size` for large sites
2. **Network Timeouts**: Increase timeout settings or reduce concurrency
3. **Playwright Issues**: Ensure browser binaries are properly installed
4. **Cache Problems**: Clear cache with `getsitedna performance clear-cache`

### Debug Mode
```bash
export GETSITEDNA_DEBUG_MODE=true
getsitedna analyze https://problematic-site.com
```

## API Usage

### Programmatic Access
```python
from getsitedna.core.analyzer import analyze_website

# Basic analysis
site = await analyze_website("https://example.com")

# Advanced configuration
from getsitedna.models.schemas import CrawlConfig
config = CrawlConfig(max_depth=3, max_pages=50)
site = await analyze_website("https://example.com", config={"crawl_config": config})
```

## Documentation Files

### Generated Documentation
- `README.md`: Project overview and quick start
- `CONTRIBUTING.md`: Development guidelines
- `CHANGELOG.md`: Version history and features
- `API_REFERENCE.md`: Comprehensive API documentation
- `examples/`: Usage examples and patterns

### Output Documentation
When analyzing a site, GetSiteDNA generates:
- `README.md`: Executive summary
- `TECHNICAL_SPECIFICATION.md`: Technical details
- `COMPONENTS.md`: Component library
- `DESIGN_SYSTEM.md`: Design tokens and specifications
- `IMPLEMENTATION.md`: Step-by-step rebuild guide

## Important File Locations

### Source Code
- Main entry point: `src/getsitedna/cli/main.py`
- Core analyzer: `src/getsitedna/core/analyzer.py`
- Data models: `src/getsitedna/models/schemas.py`

### Configuration
- Project config: `pyproject.toml`
- Default settings: `~/.getsitedna/config.json`

### Tests and Examples
- Test suite: `tests/`
- Usage examples: `examples/`
- CLI examples: `examples/cli_examples.md`

## Recent Completions

**All Critical CLI Commands Implemented (Complete)**
- ✅ `getsitedna validate` - Full analysis validation with scoring and reporting
- ✅ `getsitedna summary` - Rich summaries in console/JSON/Markdown formats  
- ✅ `getsitedna config init` - Configuration file generation and management
- ✅ Validation scoring system - Complete metrics calculation for all analysis aspects
- ✅ Design intent analysis - Brand personality and UX goals extraction
- ✅ Asset download statistics - Proper counting and reporting
- ✅ Error handling cleanup - All runtime warnings and errors resolved

**All Analysis Features Fully Functional**
- ✅ Component detection and counting (8 components detected in tests)
- ✅ Design system extraction (15 colors, typography analysis)
- ✅ API endpoint discovery (2 endpoints detected in tests)
- ✅ Validation reports with meaningful scores (75% validation score)
- ✅ Repository cleanup (removed __pycache__ files, proper .gitignore)

## Next Steps

The project is now fully complete and production-ready. The only remaining task is:

**Package for PyPI distribution**
- Set up PyPI packaging configuration  
- Create distribution workflows
- Publish to PyPI for public installation

This will make GetSiteDNA available via `pip install getsitedna` for global usage.

The tool now provides a complete, professional CLI experience with all functionality working correctly.

---

*This document should be updated when significant changes are made to the project structure or functionality.*