# Contributing to GetSiteDNA

Thank you for your interest in contributing to GetSiteDNA! This guide will help you understand how to contribute to this project.

## 🚀 Getting Started

### Prerequisites

- Python 3.8 or higher
- Git
- Basic understanding of web technologies (HTML, CSS, JavaScript)
- Familiarity with async/await Python patterns

### Development Setup

1. **Fork and clone the repository**
   ```bash
   git clone https://github.com/yourusername/getsitedna.git
   cd getsitedna
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install development dependencies**
   ```bash
   pip install -e ".[dev]"
   ```

4. **Install Playwright browsers** (for dynamic crawling)
   ```bash
   playwright install
   ```

5. **Install pre-commit hooks**
   ```bash
   pre-commit install
   ```

6. **Run tests to verify setup**
   ```bash
   pytest
   ```

## 🏗️ Project Structure

```
src/getsitedna/
├── cli/                    # Command-line interface
│   ├── commands/          # Individual CLI commands
│   ├── interactive.py     # Interactive mode
│   └── main.py           # Main CLI entry point
├── core/                  # Core analysis logic
│   └── analyzer.py       # Main analysis orchestrator
├── crawlers/             # Website crawling modules
│   ├── static_crawler.py # BeautifulSoup-based crawler
│   └── dynamic_crawler.py# Playwright-based crawler
├── extractors/           # Content and design extractors
│   ├── content.py        # Text content extraction
│   ├── design.py         # Design system extraction
│   ├── structure.py      # Layout structure analysis
│   └── assets.py         # Asset extraction
├── models/               # Data models and schemas
│   ├── schemas.py        # Pydantic schemas
│   ├── site.py          # Site model
│   └── page.py          # Page model
├── outputs/              # Output generation
│   ├── json_writer.py    # JSON output
│   └── markdown_writer.py# Markdown documentation
├── processors/           # Data processing modules
│   ├── html_parser.py    # HTML parsing utilities
│   └── pattern_recognition.py # UX pattern recognition
└── utils/                # Utility modules
    ├── cache.py          # Caching system
    ├── performance.py    # Performance optimization
    ├── error_handling.py # Error handling and retry logic
    ├── http.py          # HTTP utilities
    ├── validation.py     # URL and data validation
    └── config.py         # Configuration management
```

## 🤝 How to Contribute

### Types of Contributions

1. **Bug Reports**: Found a bug? Please report it!
2. **Feature Requests**: Have an idea for improvement?
3. **Code Contributions**: Fix bugs or implement new features
4. **Documentation**: Improve docs, examples, or guides
5. **Testing**: Add test cases or improve test coverage

### Bug Reports

Before submitting a bug report:
- Check if the issue already exists in the issue tracker
- Test with the latest version
- Collect relevant information (error messages, logs, environment)

When submitting a bug report, include:
- Clear description of the problem
- Steps to reproduce
- Expected vs actual behavior
- Error messages/logs
- Environment details (Python version, OS, etc.)

### Feature Requests

When suggesting new features:
- Explain the use case and motivation
- Describe the proposed solution
- Consider backwards compatibility
- Be open to discussion and alternative approaches

### Code Contributions

#### Before You Start

1. **Check existing issues** - Look for related issues or discussions
2. **Create an issue** - For significant changes, create an issue first
3. **Fork the repository** - Work on your own fork
4. **Create a branch** - Use descriptive branch names

#### Development Workflow

1. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   # or
   git checkout -b bugfix/issue-description
   ```

2. **Make your changes**
   - Follow the coding standards (see below)
   - Add tests for new functionality
   - Update documentation if needed

3. **Test your changes**
   ```bash
   # Run all tests
   pytest
   
   # Run with coverage
   pytest --cov=src/getsitedna
   
   # Run specific tests
   pytest tests/test_your_module.py
   ```

4. **Commit your changes**
   ```bash
   git add .
   git commit -m "feat: add new feature description"
   ```

5. **Push and create a pull request**
   ```bash
   git push origin feature/your-feature-name
   ```

## 📋 Coding Standards

### Python Style

- Follow [PEP 8](https://pep8.org/) style guidelines
- Use [Black](https://black.readthedocs.io/) for code formatting
- Use [isort](https://pycqa.github.io/isort/) for import sorting
- Use type hints where appropriate
- Write docstrings for all public functions and classes

### Code Quality

- **Function length**: Keep functions focused and reasonably short
- **Error handling**: Use proper exception handling with informative messages
- **Async/await**: Use async patterns consistently for I/O operations
- **Logging**: Use appropriate logging levels and messages
- **Comments**: Write clear comments for complex logic

### Testing

- Write tests for all new functionality
- Aim for high test coverage (>90%)
- Use descriptive test names
- Include both positive and negative test cases
- Mock external dependencies (HTTP requests, file system, etc.)

### Example Code Style

```python
"""Module for analyzing website content."""

import asyncio
from typing import Dict, List, Optional
from pathlib import Path

from ..models.page import Page
from ..utils.error_handling import ErrorHandler


class ContentExtractor:
    """Extract and analyze content from web pages."""
    
    def __init__(self, error_handler: Optional[ErrorHandler] = None):
        """Initialize content extractor.
        
        Args:
            error_handler: Optional error handler for logging
        """
        self.error_handler = error_handler or ErrorHandler("ContentExtractor")
    
    async def extract_content(self, page: Page) -> Page:
        """Extract content from a page.
        
        Args:
            page: Page object to analyze
            
        Returns:
            Updated page object with extracted content
            
        Raises:
            ExtractionError: If content extraction fails
        """
        try:
            # Implementation here
            return page
        except Exception as e:
            self.error_handler.handle_error(e)
            raise
```

## 🧪 Testing Guidelines

### Test Structure

- Place tests in the `tests/` directory
- Mirror the source structure: `tests/test_modulename.py`
- Use pytest fixtures for common test data
- Group related tests in classes

### Writing Good Tests

```python
import pytest
from unittest.mock import Mock, patch

from src.getsitedna.extractors.content import ContentExtractor


class TestContentExtractor:
    """Test content extraction functionality."""
    
    def test_extract_content_success(self, sample_page):
        """Test successful content extraction."""
        extractor = ContentExtractor()
        result = extractor.extract_content(sample_page)
        
        assert result is not None
        assert result.content.word_count > 0
    
    def test_extract_content_empty_page(self):
        """Test extraction with empty page."""
        extractor = ContentExtractor()
        empty_page = Page(url="https://example.com")
        
        result = extractor.extract_content(empty_page)
        
        assert result.content.word_count == 0
    
    @patch('requests.get')
    def test_extract_content_network_error(self, mock_get, sample_page):
        """Test handling of network errors."""
        mock_get.side_effect = ConnectionError("Network error")
        
        extractor = ContentExtractor()
        
        with pytest.raises(ExtractionError):
            extractor.extract_content(sample_page)
```

### Test Coverage

Run coverage reports to ensure adequate testing:

```bash
# Generate coverage report
pytest --cov=src/getsitedna --cov-report=html

# View coverage in browser
open htmlcov/index.html
```

## 📝 Documentation

### Docstring Format

Use Google-style docstrings:

```python
def analyze_website(url: str, config: Optional[Dict] = None) -> Site:
    """Analyze a website and return comprehensive analysis.
    
    Args:
        url: The website URL to analyze
        config: Optional configuration dictionary
        
    Returns:
        Site object containing analysis results
        
    Raises:
        AnalysisError: If analysis fails
        ValidationError: If URL is invalid
        
    Example:
        >>> site = analyze_website("https://example.com")
        >>> print(f"Found {len(site.pages)} pages")
    """
```

### Adding Examples

When adding new features, include examples in:
- Function docstrings
- README.md usage section
- Separate example files in `examples/` directory

## 🚀 Performance Considerations

### General Guidelines

- Use async/await for I/O operations
- Implement proper caching for expensive operations
- Consider memory usage with large websites
- Use generators for processing large datasets
- Profile code for performance bottlenecks

### Caching

When adding cacheable operations:

```python
from ..utils.cache import cached

@cached(ttl=3600)  # Cache for 1 hour
async def expensive_operation(url: str) -> Dict:
    """Expensive operation that should be cached."""
    # Implementation
    return result
```

### Concurrent Processing

For batch operations, use the concurrent processor:

```python
from ..utils.performance import ConcurrentProcessor

processor = ConcurrentProcessor(max_workers=4)
results = await processor.process_batch(
    items=pages,
    process_func=analyze_page,
    batch_size=5
)
```

## 🔄 Pull Request Process

### Before Submitting

- [ ] Tests pass (`pytest`)
- [ ] Code is formatted (`black src/ tests/`)
- [ ] Imports are sorted (`isort src/ tests/`)
- [ ] Documentation is updated
- [ ] Changelog is updated (if applicable)

### Pull Request Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Tests added/updated
- [ ] All tests pass
- [ ] Manual testing completed

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] No breaking changes (or noted)
```

### Review Process

1. **Automated checks** - CI/CD pipeline runs tests
2. **Code review** - Maintainers review code
3. **Discussion** - Address feedback and comments
4. **Approval** - Once approved, PR will be merged

## 🏷️ Commit Message Guidelines

Use conventional commits format:

```
type(scope): description

[optional body]

[optional footer]
```

### Types
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

### Examples
```
feat(crawler): add support for JavaScript-heavy sites
fix(cache): resolve memory leak in file cache
docs(readme): update installation instructions
```

## 🆘 Getting Help

- **Discussions**: Use GitHub Discussions for questions
- **Issues**: Create issues for bugs and feature requests
- **Documentation**: Check existing docs and examples
- **Code Review**: Ask for feedback in pull requests

## 📜 Code of Conduct

- Be respectful and inclusive
- Provide constructive feedback
- Help others learn and contribute
- Focus on the technical aspects
- Follow the project's values and goals

## 🎯 Priority Areas

Current areas where contributions are especially welcome:

1. **Testing**: Improve test coverage
2. **Documentation**: Examples and tutorials
3. **Performance**: Optimization opportunities
4. **Accessibility**: Better accessibility analysis
5. **Internationalization**: Multi-language support
6. **Integration**: Framework-specific output generators

Thank you for contributing to GetSiteDNA! 🚀