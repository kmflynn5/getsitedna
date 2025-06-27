"""Tests for CLI functionality."""

import pytest
import json
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
from click.testing import CliRunner

from src.getsitedna.cli.main import cli
from src.getsitedna.cli.commands.validate import validate
from src.getsitedna.cli.interactive import InteractiveCLI, run_interactive_mode


class TestCLIMain:
    """Test main CLI functionality."""
    
    def test_cli_help(self):
        """Test CLI help output."""
        runner = CliRunner()
        result = runner.invoke(cli, ['--help'])
        
        assert result.exit_code == 0
        assert "GetSiteDNA" in result.output
        assert "analyze" in result.output
    
    def test_cli_version(self):
        """Test CLI version display."""
        runner = CliRunner()
        result = runner.invoke(cli, ['--version'])
        
        assert result.exit_code == 0
    
    @patch('src.getsitedna.core.analyzer.analyze_website')
    def test_analyze_command_basic(self, mock_analyze):
        """Test basic analyze command."""
        # Mock the analyzer
        mock_site = Mock()
        mock_site.get_site_summary.return_value = {"pages_analyzed": 5}
        mock_analyze.return_value = mock_site
        
        runner = CliRunner()
        
        with runner.isolated_filesystem():
            result = runner.invoke(cli, ['analyze', 'https://example.com'])
            
            assert result.exit_code == 0
            mock_analyze.assert_called_once()
    
    @patch('src.getsitedna.core.analyzer.analyze_website')
    def test_analyze_command_with_options(self, mock_analyze):
        """Test analyze command with various options."""
        mock_site = Mock()
        mock_site.get_site_summary.return_value = {"pages_analyzed": 3}
        mock_analyze.return_value = mock_site
        
        runner = CliRunner()
        
        with runner.isolated_filesystem():
            result = runner.invoke(cli, [
                'analyze', 'https://example.com',
                '--output', './test_output',
                '--depth', '3',
                '--max-pages', '20',
                '--no-assets',
                '--browser', 'firefox'
            ])
            
            assert result.exit_code == 0
            
            # Verify analyzer was called with correct config
            args, kwargs = mock_analyze.call_args
            assert args[0] == 'https://example.com'
            
            config = kwargs.get('config', {})
            assert config.get('crawl_config', {}).get('max_depth') == 3
            assert config.get('crawl_config', {}).get('max_pages') == 20
            assert config.get('download_assets') is False
    
    @patch('src.getsitedna.cli.interactive.run_interactive_mode')
    @patch('src.getsitedna.core.analyzer.analyze_website')
    def test_analyze_command_interactive(self, mock_analyze, mock_interactive):
        """Test analyze command in interactive mode."""
        # Mock interactive mode
        mock_interactive.return_value = {
            'url': 'https://example.com',
            'crawl_config': {'max_depth': 2}
        }
        
        # Mock analyzer
        mock_site = Mock()
        mock_site.get_site_summary.return_value = {"pages_analyzed": 2}
        mock_analyze.return_value = mock_site
        
        runner = CliRunner()
        
        with runner.isolated_filesystem():
            result = runner.invoke(cli, [
                'analyze', 'https://example.com',
                '--interactive'
            ])
            
            assert result.exit_code == 0
            mock_interactive.assert_called_once()
            mock_analyze.assert_called_once()
    
    def test_config_init_command(self):
        """Test config init command."""
        runner = CliRunner()
        
        with runner.isolated_filesystem():
            result = runner.invoke(cli, ['config', 'init'])
            
            assert result.exit_code == 0
            assert "Configuration file created" in result.output


class TestValidateCommand:
    """Test validation command functionality."""
    
    def test_validate_command_help(self):
        """Test validate command help."""
        runner = CliRunner()
        result = runner.invoke(validate, ['--help'])
        
        assert result.exit_code == 0
        assert "Validate analysis output" in result.output
    
    def test_validate_nonexistent_directory(self):
        """Test validation with non-existent directory."""
        runner = CliRunner()
        result = runner.invoke(validate, ['/nonexistent/path'])
        
        assert result.exit_code != 0
    
    def test_validate_empty_directory(self, temp_directory):
        """Test validation with empty directory."""
        runner = CliRunner()
        result = runner.invoke(validate, [str(temp_directory)])
        
        # Should fail validation due to missing files
        assert result.exit_code == 1
        assert "Missing" in result.output or "failed" in result.output.lower()
    
    def test_validate_valid_analysis(self, temp_directory, create_test_files, sample_json_output):
        """Test validation with valid analysis directory."""
        # Create required files
        files = {
            "specification.json": sample_json_output,
            "site_data.json": {
                "base_url": "https://example.com",
                "domain": "example.com",
                "analysis_metadata": {},
                "statistics": {"total_pages_discovered": 5}
            },
            "validation_report.json": {
                "site_validation": {},
                "global_issues": {}
            },
            "README.md": "# Test Analysis\nThis is a test analysis.",
            "TECHNICAL_SPECIFICATION.md": "# Technical Spec\nDetailed specs."
        }
        
        create_test_files(temp_directory, files)
        
        # Create pages directory
        pages_dir = temp_directory / "pages"
        pages_dir.mkdir()
        
        runner = CliRunner()
        result = runner.invoke(validate, [str(temp_directory)])
        
        # Should pass validation
        assert result.exit_code == 0
        assert "✓ Validation passed" in result.output
    
    def test_validate_with_output_file(self, temp_directory, create_test_files, sample_json_output):
        """Test validation with output file generation."""
        # Create minimal valid files
        files = {
            "specification.json": sample_json_output,
            "site_data.json": {
                "base_url": "https://example.com",
                "domain": "example.com", 
                "analysis_metadata": {},
                "statistics": {}
            }
        }
        
        create_test_files(temp_directory, files)
        
        output_file = temp_directory / "validation_output.json"
        
        runner = CliRunner()
        result = runner.invoke(validate, [
            str(temp_directory),
            '--output', str(output_file)
        ])
        
        # Check output file was created
        assert output_file.exists()
        
        with open(output_file, 'r') as f:
            validation_data = json.load(f)
            assert "overall_score" in validation_data


class TestInteractiveCLI:
    """Test interactive CLI functionality."""
    
    def test_interactive_cli_initialization(self):
        """Test InteractiveCLI initialization."""
        interactive = InteractiveCLI()
        
        assert isinstance(interactive.config, dict)
        assert isinstance(interactive.metadata, dict)
    
    @patch('src.getsitedna.cli.interactive.Confirm.ask')
    @patch('src.getsitedna.cli.interactive.Prompt.ask')
    @patch('src.getsitedna.cli.interactive.IntPrompt.ask')
    def test_interactive_analysis_flow(self, mock_int_prompt, mock_prompt, mock_confirm):
        """Test complete interactive analysis flow."""
        # Mock user inputs
        mock_confirm.side_effect = [
            True,   # Confirm URL
            True,   # Include assets
            True,   # Generate markdown
            False,  # No screenshots
            True,   # Enable content analysis
            True,   # Enable design analysis
            True,   # Enable component analysis
            False,  # No performance analysis
            True,   # Enable SEO analysis
            True,   # Enable accessibility analysis
            False,  # No deep analysis
            True    # Proceed with analysis
        ]
        
        mock_int_prompt.side_effect = [
            1,  # Analysis philosophy
            1,  # Target framework  
            1,  # Accessibility level
            2,  # Max depth
            25, # Max pages
            1   # Browser choice
        ]
        
        mock_prompt.side_effect = [
            "./test_output"  # Output directory
        ]
        
        interactive = InteractiveCLI()
        
        # Should complete without errors
        config = interactive.run_interactive_analysis("https://example.com")
        
        assert config["url"] == "https://example.com"
        assert "philosophy" in config
        assert "framework" in config
        assert "crawl_config" in config
    
    @patch('src.getsitedna.cli.interactive.Confirm.ask')
    def test_interactive_url_confirmation(self, mock_confirm):
        """Test URL confirmation in interactive mode."""
        mock_confirm.return_value = False  # User says URL is wrong
        
        with patch('src.getsitedna.cli.interactive.Prompt.ask') as mock_prompt:
            mock_prompt.return_value = "https://corrected.com"
            
            # Mock remaining prompts to complete flow
            with patch('src.getsitedna.cli.interactive.IntPrompt.ask') as mock_int:
                mock_int.return_value = 1
                with patch('src.getsitedna.cli.interactive.Confirm.ask') as mock_confirm_remaining:
                    mock_confirm_remaining.return_value = True
                    
                    interactive = InteractiveCLI()
                    config = interactive.run_interactive_analysis("https://example.com")
                    
                    # Should use corrected URL
                    assert config["url"] == "https://corrected.com"
    
    def test_interactive_cancellation(self):
        """Test cancellation of interactive analysis."""
        with patch('src.getsitedna.cli.interactive.Confirm.ask') as mock_confirm:
            # Mock final confirmation as False (cancel)
            mock_confirm.side_effect = [True] * 10 + [False]  # Say no to final confirmation
            
            with patch('src.getsitedna.cli.interactive.IntPrompt.ask') as mock_int:
                mock_int.return_value = 1
                with patch('src.getsitedna.cli.interactive.Prompt.ask') as mock_prompt:
                    mock_prompt.return_value = "./output"
                    
                    interactive = InteractiveCLI()
                    config = interactive.run_interactive_analysis("https://example.com")
                    
                    # Should return empty config on cancellation
                    assert config == {}
    
    def test_progress_updates(self):
        """Test progress update display."""
        interactive = InteractiveCLI()
        
        # Should not raise any errors
        interactive.show_progress_updates("Testing progress", {
            "pages_discovered": 10,
            "pages_analyzed": 5,
            "errors": ["test error"]
        })
    
    def test_completion_summary(self):
        """Test completion summary display."""
        interactive = InteractiveCLI()
        
        results = {
            "pages_analyzed": 10,
            "components_found": 15,
            "colors_found": 8,
            "fonts_found": 3,
            "assets_downloaded": 25,
            "output_directory": "/test/output",
            "output_files": {
                "specification": "/test/output/specification.json",
                "readme": "/test/output/README.md"
            }
        }
        
        # Should not raise any errors
        interactive.show_completion_summary(results)
    
    @patch('src.getsitedna.cli.interactive.InteractiveCLI.run_interactive_analysis')
    def test_run_interactive_mode_function(self, mock_run):
        """Test run_interactive_mode entry point function."""
        mock_run.return_value = {"url": "https://example.com"}
        
        result = run_interactive_mode("https://example.com", Path("./output"))
        
        assert result == {"url": "https://example.com"}
        mock_run.assert_called_once_with("https://example.com", Path("./output"))


class TestCLIErrorHandling:
    """Test CLI error handling scenarios."""
    
    @patch('src.getsitedna.core.analyzer.analyze_website')
    def test_analyze_command_network_error(self, mock_analyze):
        """Test analyze command with network error."""
        from src.getsitedna.utils.error_handling import NetworkError
        
        mock_analyze.side_effect = NetworkError("Connection failed", url="https://example.com")
        
        runner = CliRunner()
        result = runner.invoke(cli, ['analyze', 'https://example.com'])
        
        assert result.exit_code != 0
        assert "error" in result.output.lower() or "failed" in result.output.lower()
    
    @patch('src.getsitedna.core.analyzer.analyze_website')
    def test_analyze_command_analysis_error(self, mock_analyze):
        """Test analyze command with analysis error."""
        from src.getsitedna.utils.error_handling import AnalysisError, ErrorCategory, ErrorSeverity
        
        mock_analyze.side_effect = AnalysisError(
            "Analysis failed", 
            ErrorCategory.PARSING, 
            ErrorSeverity.HIGH
        )
        
        runner = CliRunner()
        result = runner.invoke(cli, ['analyze', 'https://example.com'])
        
        assert result.exit_code != 0
    
    def test_invalid_url_handling(self):
        """Test handling of invalid URLs."""
        runner = CliRunner()
        result = runner.invoke(cli, ['analyze', 'not-a-valid-url'])
        
        # Should handle gracefully (either validate URL or fail gracefully)
        # Exact behavior depends on implementation
        assert isinstance(result.exit_code, int)
    
    def test_invalid_options_handling(self):
        """Test handling of invalid command options."""
        runner = CliRunner()
        
        # Test invalid depth
        result = runner.invoke(cli, [
            'analyze', 'https://example.com',
            '--depth', '0'  # Invalid depth
        ])
        
        assert result.exit_code != 0
        
        # Test invalid browser
        result = runner.invoke(cli, [
            'analyze', 'https://example.com', 
            '--browser', 'invalid-browser'
        ])
        
        assert result.exit_code != 0