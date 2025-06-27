"""Tests for output generation."""

import pytest
import json
from pathlib import Path
from unittest.mock import Mock, patch

from src.getsitedna.outputs.json_writer import JSONWriter
from src.getsitedna.outputs.markdown_writer import MarkdownWriter


class TestJSONWriter:
    """Test JSON output generation."""
    
    def test_json_writer_initialization(self, temp_directory):
        """Test JSONWriter initialization."""
        writer = JSONWriter(temp_directory)
        
        assert writer.output_directory == temp_directory
        assert temp_directory.exists()
    
    def test_write_site_analysis(self, populated_site, temp_directory):
        """Test complete site analysis JSON output."""
        writer = JSONWriter(temp_directory)
        
        output_files = writer.write_site_analysis(populated_site)
        
        # Check all expected files were created
        expected_files = ["specification", "site_data", "pages_data", "validation_report", "summary"]
        for file_key in expected_files:
            assert file_key in output_files
            assert output_files[file_key].exists()
            assert output_files[file_key].suffix == ".json"
    
    def test_specification_json_structure(self, populated_site, temp_directory):
        """Test specification.json structure."""
        writer = JSONWriter(temp_directory)
        output_files = writer.write_site_analysis(populated_site)
        
        spec_file = output_files["specification"]
        
        with open(spec_file, 'r', encoding='utf-8') as f:
            spec_data = json.load(f)
        
        # Check required top-level sections
        required_sections = [
            "metadata", "design_intent", "experience_patterns",
            "component_specifications", "technical_modernization", "design_system"
        ]
        
        for section in required_sections:
            assert section in spec_data
        
        # Check metadata structure
        metadata = spec_data["metadata"]
        assert "analysis_philosophy" in metadata
        assert "target_framework" in metadata
        assert "base_url" in metadata
    
    def test_site_data_json_structure(self, populated_site, temp_directory):
        """Test site_data.json structure."""
        writer = JSONWriter(temp_directory)
        output_files = writer.write_site_analysis(populated_site)
        
        site_file = output_files["site_data"]
        
        with open(site_file, 'r', encoding='utf-8') as f:
            site_data = json.load(f)
        
        # Check required fields
        required_fields = ["base_url", "domain", "analysis_metadata", "statistics"]
        for field in required_fields:
            assert field in site_data
        
        # Check nested structures
        assert "global_design_system" in site_data
        assert "color_palette" in site_data["global_design_system"]
        assert "typography" in site_data["global_design_system"]
    
    def test_pages_data_json_structure(self, populated_site, temp_directory):
        """Test pages_data.json structure."""
        writer = JSONWriter(temp_directory)
        output_files = writer.write_site_analysis(populated_site)
        
        pages_file = output_files["pages_data"]
        
        with open(pages_file, 'r', encoding='utf-8') as f:
            pages_data = json.load(f)
        
        # Check structure
        assert "total_pages" in pages_data
        assert "pages" in pages_data
        assert isinstance(pages_data["pages"], dict)
        
        # Check page entries
        if pages_data["pages"]:
            first_page = next(iter(pages_data["pages"].values()))
            assert "summary" in first_page
            assert "basic_info" in first_page
            assert "seo" in first_page
    
    def test_write_page_analysis(self, sample_page, temp_directory):
        """Test individual page analysis output."""
        writer = JSONWriter(temp_directory)
        
        output_file = writer.write_page_analysis(sample_page)
        
        assert output_file.exists()
        assert output_file.name == "index.json"  # Default for root page
        
        with open(output_file, 'r', encoding='utf-8') as f:
            page_data = json.load(f)
        
        # Check page data structure
        required_sections = ["url", "basic_info", "content", "structure", "design"]
        for section in required_sections:
            assert section in page_data
    
    def test_filename_sanitization(self, temp_directory):
        """Test filename sanitization."""
        writer = JSONWriter(temp_directory)
        
        # Test with problematic characters
        sanitized = writer._sanitize_filename("page/with:bad<chars>")
        assert sanitized == "page_with_bad_chars_"
        
        # Test empty filename
        sanitized = writer._sanitize_filename("")
        assert sanitized == "page"
        
        # Test normal filename
        sanitized = writer._sanitize_filename("normal-page")
        assert sanitized == "normal-page"
    
    def test_json_serialization(self, populated_site, temp_directory):
        """Test JSON serialization of complex objects."""
        writer = JSONWriter(temp_directory)
        
        # Should not raise any serialization errors
        output_files = writer.write_site_analysis(populated_site)
        
        # Verify all files contain valid JSON
        for file_path in output_files.values():
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)  # Should not raise JSONDecodeError
                assert isinstance(data, dict)


class TestMarkdownWriter:
    """Test Markdown documentation generation."""
    
    def test_markdown_writer_initialization(self, temp_directory):
        """Test MarkdownWriter initialization."""
        writer = MarkdownWriter(temp_directory)
        
        assert writer.output_directory == temp_directory
        assert temp_directory.exists()
    
    def test_write_documentation(self, populated_site, temp_directory):
        """Test complete documentation generation."""
        writer = MarkdownWriter(temp_directory)
        
        output_files = writer.write_documentation(populated_site)
        
        # Check all expected files were created
        expected_files = [
            "readme", "technical_spec", "components", 
            "design_system", "implementation"
        ]
        
        for file_key in expected_files:
            assert file_key in output_files
            assert output_files[file_key].exists()
            assert output_files[file_key].suffix == ".md"
    
    def test_main_readme_content(self, populated_site, temp_directory):
        """Test main README.md content."""
        writer = MarkdownWriter(temp_directory)
        output_files = writer.write_documentation(populated_site)
        
        readme_file = output_files["readme"]
        
        with open(readme_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for required sections
        assert "# Website Analysis Report" in content
        assert "## Site Overview" in content
        assert "## Executive Summary" in content
        assert "## Quick Start" in content
        
        # Check for site-specific information
        assert str(populated_site.base_url) in content
        assert populated_site.domain in content
    
    def test_technical_specification_content(self, populated_site, temp_directory):
        """Test technical specification content."""
        writer = MarkdownWriter(temp_directory)
        output_files = writer.write_documentation(populated_site)
        
        tech_spec_file = output_files["technical_spec"]
        
        with open(tech_spec_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for required sections
        assert "# Technical Specification" in content
        assert "## Technology Stack" in content
        assert "## Performance Requirements" in content
        assert "## Accessibility Requirements" in content
        
        # Check for framework-specific content
        framework = populated_site.metadata.target_framework.value.replace('_', ' ').title()
        assert framework in content
    
    def test_component_library_content(self, populated_site, temp_directory):
        """Test component library documentation."""
        writer = MarkdownWriter(temp_directory)
        output_files = writer.write_documentation(populated_site)
        
        components_file = output_files["components"]
        
        with open(components_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for component documentation
        assert "# Component Library" in content
        assert "## Component Overview" in content
        
        # Should include components from populated site
        if populated_site.component_specifications:
            component = populated_site.component_specifications[0]
            assert component.component_name in content
    
    def test_design_system_content(self, populated_site, temp_directory):
        """Test design system documentation."""
        writer = MarkdownWriter(temp_directory)
        output_files = writer.write_documentation(populated_site)
        
        design_file = output_files["design_system"]
        
        with open(design_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for design system sections
        assert "# Design System" in content
        assert "## Color Palette" in content
        assert "## Typography" in content
        
        # Should include colors from populated site
        if populated_site.global_color_palette:
            color = populated_site.global_color_palette[0]
            assert color.hex in content
    
    def test_implementation_guide_content(self, populated_site, temp_directory):
        """Test implementation guide content."""
        writer = MarkdownWriter(temp_directory)
        output_files = writer.write_documentation(populated_site)
        
        impl_file = output_files["implementation"]
        
        with open(impl_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for implementation phases
        assert "# Implementation Guide" in content
        assert "## Phase 1: Project Setup" in content
        assert "## Phase 2: Design System Implementation" in content
        assert "## Phase 3: Component Development" in content
        
        # Should include framework-specific setup
        framework = populated_site.metadata.target_framework.value
        if "react" in framework:
            assert "create-next-app" in content or "React" in content
    
    def test_page_analysis_content(self, sample_page, temp_directory):
        """Test individual page analysis documentation."""
        writer = MarkdownWriter(temp_directory)
        
        pages_dir = temp_directory / "pages"
        output_file = writer._write_page_analysis(sample_page, pages_dir)
        
        assert output_file.exists()
        
        with open(output_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check page analysis content
        assert f"# Page Analysis: {sample_page.title}" in content
        assert str(sample_page.url) in content
        assert "## Content Analysis" in content
        assert "## Technical Details" in content
    
    def test_markdown_formatting(self, populated_site, temp_directory):
        """Test proper Markdown formatting."""
        writer = MarkdownWriter(temp_directory)
        output_files = writer.write_documentation(populated_site)
        
        # Check README for proper Markdown
        readme_file = output_files["readme"]
        with open(readme_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for proper heading levels
        assert content.count("# ") >= 1  # At least one H1
        assert content.count("## ") >= 3  # Multiple H2s
        
        # Check for proper list formatting
        assert "- " in content or "* " in content
        
        # Check for proper link formatting
        assert "](" in content  # Markdown link format
    
    def test_site_map_generation(self, populated_site):
        """Test site map generation."""
        writer = MarkdownWriter(Path("."))
        
        sitemap = writer._generate_site_map(populated_site)
        
        assert populated_site.domain in sitemap
        assert "├──" in sitemap or sitemap.strip() == f"{populated_site.domain}/"
    
    def test_filename_sanitization_markdown(self):
        """Test filename sanitization for Markdown files."""
        writer = MarkdownWriter(Path("."))
        
        # Test with problematic characters
        sanitized = writer._sanitize_filename("page/with:bad<chars>")
        assert sanitized == "page_with_bad_chars_"
        
        # Test normal filename
        sanitized = writer._sanitize_filename("about-us")
        assert sanitized == "about-us"
    
    def test_content_formatting_helpers(self, populated_site):
        """Test content formatting helper methods."""
        writer = MarkdownWriter(Path("."))
        
        # Test design intent formatting
        design_intent = writer._format_design_intent(populated_site)
        assert isinstance(design_intent, str)
        
        # Test component summary formatting
        component_summary = writer._format_component_summary(populated_site)
        assert isinstance(component_summary, str)
        
        # Test validation summary formatting
        validation_summary = writer._format_validation_summary(populated_site)
        assert isinstance(validation_summary, str)