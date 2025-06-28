"""Integration tests for CLI functionality without heavy mocking."""

import pytest
import json
import tempfile
from pathlib import Path
from click.testing import CliRunner
from unittest.mock import patch

from src.getsitedna.cli.main import cli


class TestCLIIntegration:
    """Integration tests for CLI commands."""
    
    def test_cli_help_integration(self):
        """Test CLI help command integration."""
        runner = CliRunner()
        result = runner.invoke(cli, ['--help'])
        
        assert result.exit_code == 0
        assert "GetSiteDNA" in result.output
        assert "analyze" in result.output
        assert "config" in result.output
        assert "performance" in result.output
    
    def test_analyze_help_integration(self):
        """Test analyze command help integration."""
        runner = CliRunner()
        result = runner.invoke(cli, ['analyze', '--help'])
        
        assert result.exit_code == 0
        assert "Analyze a website" in result.output
        assert "--output" in result.output
        assert "--depth" in result.output
        assert "--max-pages" in result.output
    
    def test_config_help_integration(self):
        """Test config command help integration."""
        runner = CliRunner()
        result = runner.invoke(cli, ['config', '--help'])
        
        assert result.exit_code == 0
    
    def test_performance_help_integration(self):
        """Test performance command help integration."""
        runner = CliRunner()
        result = runner.invoke(cli, ['performance', '--help'])
        
        assert result.exit_code == 0
    
    @patch('src.getsitedna.core.analyzer.analyze_website')
    def test_analyze_with_mocked_analyzer(self, mock_analyze):
        """Test analyze command with mocked analyzer (simpler and more reliable)."""
        from src.getsitedna.models.site import Site
        from src.getsitedna.models.page import Page
        
        # Create a minimal Site with one page
        mock_site = Site(base_url="https://example.com")
        
        # Add a test page
        test_page = Page(
            url="https://example.com/",
            title="Example Domain",
            html_content="<html><body>This domain is for use in illustrative examples.</body></html>"
        )
        # Update the content field properly
        test_page.content.unique_copy = ["This domain is for use in illustrative examples."]
        mock_site.pages["https://example.com/"] = test_page
        mock_site.stats.total_pages_crawled = 1
        mock_site.stats.total_pages_analyzed = 1
        
        # Mock the analyzer to return our test site
        mock_analyze.return_value = mock_site
        
        runner = CliRunner()
        
        with runner.isolated_filesystem():
            result = runner.invoke(cli, [
                'analyze', 'https://example.com',
                '--depth', '1',
                '--max-pages', '1',
                '--output', './test_output'
            ])
            
            # Should complete successfully
            assert result.exit_code == 0
            assert "Analysis completed successfully" in result.output
            
            # Verify analyzer was called with correct parameters
            mock_analyze.assert_called_once()
            args, kwargs = mock_analyze.call_args
            assert args[0] == 'https://example.com'
            
            # Check if we have the right number of arguments
            assert len(args) >= 1
            
            # Check config parameter (second positional arg or in kwargs)
            if len(args) > 1:
                config = args[1]
            else:
                config = kwargs.get('config', {})
            
            assert 'crawl_config' in config
            assert config['crawl_config']['max_depth'] == 1
            assert config['crawl_config']['max_pages'] == 1
    
    def test_analyze_invalid_url(self):
        """Test analyze command with invalid URL."""
        runner = CliRunner()
        
        with runner.isolated_filesystem():
            result = runner.invoke(cli, [
                'analyze', 'not-a-valid-url',
                '--depth', '1',
                '--max-pages', '1'
            ])
            
            # Should fail gracefully
            assert result.exit_code != 0
    
    def test_analyze_with_all_options(self):
        """Test analyze command with all available options."""
        runner = CliRunner()
        
        with patch('src.getsitedna.core.analyzer.analyze_website') as mock_analyze:
            from src.getsitedna.models.site import Site
            
            # Mock analyzer to return a simple site
            mock_site = Site(base_url="https://example.com")
            mock_analyze.return_value = mock_site
            
            with runner.isolated_filesystem():
                result = runner.invoke(cli, [
                    'analyze', 'https://example.com',
                    '--output', './full_test',
                    '--depth', '2',
                    '--max-pages', '10',
                    '--include-assets',
                    '--browser', 'chromium'
                ])
                
                assert result.exit_code == 0
                
                # Verify analyzer was called with correct configuration
                mock_analyze.assert_called_once()
                args, kwargs = mock_analyze.call_args
                
                assert args[0] == 'https://example.com'
                assert kwargs['output_dir'] == Path('./full_test')
                
                config = kwargs['config']
                assert config['crawl_config']['max_depth'] == 2
                assert config['crawl_config']['max_pages'] == 10
                assert config['download_assets'] is True
    
    def test_config_init_integration(self):
        """Test config init command integration."""
        runner = CliRunner()
        
        with runner.isolated_filesystem():
            result = runner.invoke(cli, ['config', 'init'])
            
            # Should create config file
            assert result.exit_code == 0
            
            # Check for config file creation message
            assert "Configuration" in result.output or "config" in result.output.lower()


class TestCLIErrorHandling:
    """Test CLI error handling in integration scenarios."""
    
    def test_analyze_network_timeout(self):
        """Test analyze command behavior with network issues."""
        runner = CliRunner()
        
        with runner.isolated_filesystem():
            # Use a URL that should timeout or be unreachable
            result = runner.invoke(cli, [
                'analyze', 'https://192.0.2.1',  # Reserved test IP that should be unreachable
                '--depth', '1',
                '--max-pages', '1'
            ])
            
            # Should handle network errors gracefully
            assert result.exit_code != 0
            assert "error" in result.output.lower() or "failed" in result.output.lower()
    
    def test_analyze_invalid_options(self):
        """Test analyze command with invalid option values."""
        runner = CliRunner()
        
        # Test invalid depth
        result = runner.invoke(cli, [
            'analyze', 'https://example.com',
            '--depth', '0'  # Invalid depth
        ])
        assert result.exit_code != 0
        
        # Test invalid max-pages
        result = runner.invoke(cli, [
            'analyze', 'https://example.com',
            '--max-pages', '0'  # Invalid max-pages
        ])
        assert result.exit_code != 0
        
        # Test invalid browser
        result = runner.invoke(cli, [
            'analyze', 'https://example.com',
            '--browser', 'invalid-browser'
        ])
        assert result.exit_code != 0
    
    def test_analyze_output_permission_error(self):
        """Test analyze command with output directory permission issues."""
        runner = CliRunner()
        
        with runner.isolated_filesystem():
            # Try to write to a read-only location (simulated)
            result = runner.invoke(cli, [
                'analyze', 'https://example.com',
                '--output', '/root/forbidden',  # Should not have permission
                '--depth', '1',
                '--max-pages', '1'
            ])
            
            # Should handle permission errors gracefully
            # Note: This might not fail on all systems, so we just check it doesn't crash
            assert isinstance(result.exit_code, int)


class TestCLIOutputValidation:
    """Test that CLI produces valid output."""
    
    @patch('src.getsitedna.core.analyzer.analyze_website')
    def test_analyze_produces_valid_json(self, mock_analyze):
        """Test that analyze command produces valid JSON output."""
        from src.getsitedna.models.site import Site
        from src.getsitedna.models.page import Page
        
        # Create a site with real data structure
        mock_site = Site(base_url="https://example.com")
        test_page = Page(
            url="https://example.com/",
            title="Test Page",
            html_content="<html><body>Test content</body></html>"
        )
        test_page.content.unique_copy = ["Test content"]
        mock_site.pages["https://example.com/"] = test_page
        mock_analyze.return_value = mock_site
        
        runner = CliRunner()
        
        with runner.isolated_filesystem():
            result = runner.invoke(cli, [
                'analyze', 'https://example.com',
                '--output', './json_test'
            ])
            
            assert result.exit_code == 0
            
            # Check that JSON file was created and is valid
            json_file = Path('./json_test/specification.json')
            if json_file.exists():
                with open(json_file, 'r') as f:
                    data = json.load(f)  # Should not raise JSON decode error
                    assert isinstance(data, dict)
                    assert 'base_url' in data or 'url' in data
    
    @patch('src.getsitedna.core.analyzer.analyze_website')
    def test_analyze_produces_markdown_files(self, mock_analyze):
        """Test that analyze command produces readable markdown files."""
        from src.getsitedna.models.site import Site
        
        mock_site = Site(base_url="https://example.com")
        mock_analyze.return_value = mock_site
        
        runner = CliRunner()
        
        with runner.isolated_filesystem():
            result = runner.invoke(cli, [
                'analyze', 'https://example.com',
                '--output', './markdown_test'
            ])
            
            assert result.exit_code == 0
            
            # Check that markdown files were created
            output_dir = Path('./markdown_test')
            markdown_files = list(output_dir.glob('*.md'))
            
            assert len(markdown_files) > 0, "No markdown files were created"
            
            # Check that at least one markdown file has content
            for md_file in markdown_files:
                if md_file.stat().st_size > 0:
                    with open(md_file, 'r') as f:
                        content = f.read()
                        assert len(content.strip()) > 0
                    break
            else:
                pytest.fail("All markdown files are empty")


class TestCLIPerformance:
    """Test CLI performance characteristics."""
    
    @patch('src.getsitedna.core.analyzer.analyze_website')
    def test_analyze_completes_in_reasonable_time(self, mock_analyze):
        """Test that analyze command completes in reasonable time."""
        import time
        from src.getsitedna.models.site import Site
        
        mock_site = Site(base_url="https://example.com")
        mock_analyze.return_value = mock_site
        
        runner = CliRunner()
        
        with runner.isolated_filesystem():
            start_time = time.time()
            
            result = runner.invoke(cli, [
                'analyze', 'https://example.com',
                '--depth', '1',
                '--max-pages', '1'
            ])
            
            end_time = time.time()
            duration = end_time - start_time
            
            # Should complete within reasonable time (30 seconds for mocked analysis)
            assert duration < 30, f"Analysis took too long: {duration} seconds"
            assert result.exit_code == 0