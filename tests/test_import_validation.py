"""Tests for import validation and syntax checking."""

import pytest
import importlib
import sys
from pathlib import Path


class TestImportValidation:
    """Test that all modules can be imported without syntax errors."""
    
    def test_cli_main_imports(self):
        """Test that CLI main module imports successfully."""
        try:
            import src.getsitedna.cli.main
            assert True
        except (ImportError, SyntaxError) as e:
            pytest.fail(f"Failed to import CLI main: {e}")
    
    def test_core_analyzer_imports(self):
        """Test that core analyzer imports successfully."""
        try:
            import src.getsitedna.core.analyzer
            assert True
        except (ImportError, SyntaxError) as e:
            pytest.fail(f"Failed to import core analyzer: {e}")
    
    def test_crawlers_import(self):
        """Test that all crawlers import successfully."""
        crawlers = [
            'src.getsitedna.crawlers.static_crawler',
            'src.getsitedna.crawlers.dynamic_crawler'
        ]
        
        for crawler_module in crawlers:
            try:
                importlib.import_module(crawler_module)
            except (ImportError, SyntaxError) as e:
                pytest.fail(f"Failed to import {crawler_module}: {e}")
    
    def test_extractors_import(self):
        """Test that all extractors import successfully."""
        extractors = [
            'src.getsitedna.extractors.content',
            'src.getsitedna.extractors.design',
            'src.getsitedna.extractors.structure',
            'src.getsitedna.extractors.assets',
            'src.getsitedna.extractors.api_discovery'
        ]
        
        for extractor_module in extractors:
            try:
                importlib.import_module(extractor_module)
            except (ImportError, SyntaxError) as e:
                pytest.fail(f"Failed to import {extractor_module}: {e}")
    
    def test_models_import(self):
        """Test that all models import successfully."""
        models = [
            'src.getsitedna.models.schemas',
            'src.getsitedna.models.site',
            'src.getsitedna.models.page'
        ]
        
        for model_module in models:
            try:
                importlib.import_module(model_module)
            except (ImportError, SyntaxError) as e:
                pytest.fail(f"Failed to import {model_module}: {e}")
    
    def test_outputs_import(self):
        """Test that output modules import successfully."""
        outputs = [
            'src.getsitedna.outputs.json_writer',
            'src.getsitedna.outputs.markdown_writer'
        ]
        
        for output_module in outputs:
            try:
                importlib.import_module(output_module)
            except (ImportError, SyntaxError) as e:
                pytest.fail(f"Failed to import {output_module}: {e}")
    
    def test_utils_import(self):
        """Test that utility modules import successfully."""
        utils = [
            'src.getsitedna.utils.error_handling',
            'src.getsitedna.utils.performance',
            'src.getsitedna.utils.cache',
            'src.getsitedna.utils.validation'
        ]
        
        for util_module in utils:
            try:
                importlib.import_module(util_module)
            except (ImportError, SyntaxError) as e:
                pytest.fail(f"Failed to import {util_module}: {e}")
    
    def test_processors_import(self):
        """Test that processor modules import successfully."""
        processors = [
            'src.getsitedna.processors.html_parser',
            'src.getsitedna.processors.pattern_recognition'
        ]
        
        for processor_module in processors:
            try:
                importlib.import_module(processor_module)
            except (ImportError, SyntaxError) as e:
                pytest.fail(f"Failed to import {processor_module}: {e}")


class TestSmokeTests:
    """Basic smoke tests for critical functionality."""
    
    def test_cli_help_command(self):
        """Test that CLI help command works without errors."""
        from click.testing import CliRunner
        from src.getsitedna.cli.main import cli
        
        runner = CliRunner()
        result = runner.invoke(cli, ['--help'])
        
        assert result.exit_code == 0
        assert "GetSiteDNA" in result.output
        assert "analyze" in result.output
    
    def test_analyze_help_command(self):
        """Test that analyze help command works without errors."""
        from click.testing import CliRunner
        from src.getsitedna.cli.main import cli
        
        runner = CliRunner()
        result = runner.invoke(cli, ['analyze', '--help'])
        
        assert result.exit_code == 0
        assert "Analyze a website" in result.output
    
    def test_validation_report_creation(self):
        """Test that ValidationReport can be created with defaults."""
        from src.getsitedna.models.schemas import ValidationReport
        
        # Should not raise any validation errors
        report = ValidationReport()
        assert report.completeness_score == 0.0
        assert isinstance(report.quality_metrics, dict)
        assert isinstance(report.missing_elements, list)
    
    def test_site_model_creation(self):
        """Test that Site model can be created properly."""
        from src.getsitedna.models.site import Site
        
        # Should not raise any validation errors
        site = Site(base_url="https://example.com")
        assert site.domain == "example.com"
        assert str(site.base_url).startswith("https://example.com")
    
    def test_crawl_config_creation(self):
        """Test that CrawlConfig can be created with defaults."""
        from src.getsitedna.models.site import CrawlConfig
        
        # Should not raise any validation errors
        config = CrawlConfig()
        assert config.max_depth >= 1
        assert config.max_pages >= 1
    
    def test_analyzer_instantiation(self):
        """Test that SiteAnalyzer can be instantiated."""
        from src.getsitedna.core.analyzer import SiteAnalyzer
        from pathlib import Path
        
        # Should not raise any errors during instantiation
        analyzer = SiteAnalyzer(output_directory=Path("./test"))
        assert analyzer.output_directory == Path("./test")
        assert analyzer.error_handler is not None


class TestCriticalPaths:
    """Test critical code paths that must work."""
    
    def test_analyze_website_function_exists(self):
        """Test that analyze_website function exists and is callable."""
        from src.getsitedna.core.analyzer import analyze_website
        import inspect
        
        assert callable(analyze_website)
        assert inspect.iscoroutinefunction(analyze_website)
    
    def test_error_handling_imports(self):
        """Test that error handling components import correctly."""
        from src.getsitedna.utils.error_handling import (
            ErrorHandler, SafeExecutor, AnalysisError, 
            ErrorSeverity, ErrorCategory
        )
        
        # Test that error handler can be instantiated
        handler = ErrorHandler()
        assert handler is not None
        
        # Test that SafeExecutor can be instantiated
        executor = SafeExecutor()
        assert executor is not None
    
    def test_key_schemas_have_required_fields(self):
        """Test that key schemas have all required fields."""
        from src.getsitedna.models.schemas import (
            ValidationReport, CrawlConfig, AnalysisMetadata
        )
        
        # ValidationReport should have completeness_score with default
        report = ValidationReport()
        assert hasattr(report, 'completeness_score')
        
        # CrawlConfig should have core crawling parameters
        from src.getsitedna.models.site import CrawlConfig
        config = CrawlConfig()
        assert hasattr(config, 'max_depth')
        assert hasattr(config, 'max_pages')
        
        # AnalysisMetadata should be creatable
        metadata = AnalysisMetadata()
        assert metadata is not None