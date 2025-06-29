"""JSON output writer for analysis results."""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List

from ..models.site import Site
from ..models.page import Page


class JSONWriter:
    """Write analysis results to JSON files."""
    
    def __init__(self, output_directory: Path):
        self.output_directory = Path(output_directory)
        self.output_directory.mkdir(parents=True, exist_ok=True)
    
    def write_site_analysis(self, site: Site) -> Dict[str, Path]:
        """Write complete site analysis to JSON files."""
        output_files = {}
        
        # Main specification file (following PRD format)
        spec_file = self.output_directory / "specification.json"
        specification = site.get_json_specification()
        self._write_json_file(spec_file, specification)
        output_files["specification"] = spec_file
        
        # Detailed site data
        site_file = self.output_directory / "site_data.json"
        site_data = self._prepare_site_data(site)
        self._write_json_file(site_file, site_data)
        output_files["site_data"] = site_file
        
        # Pages data
        pages_file = self.output_directory / "pages_data.json"
        pages_data = self._prepare_pages_data(site)
        self._write_json_file(pages_file, pages_data)
        output_files["pages_data"] = pages_file
        
        # Validation report
        validation_file = self.output_directory / "validation_report.json"
        validation_data = self._prepare_validation_report(site)
        self._write_json_file(validation_file, validation_data)
        output_files["validation_report"] = validation_file
        
        # Summary statistics
        summary_file = self.output_directory / "analysis_summary.json"
        summary_data = site.get_site_summary()
        self._write_json_file(summary_file, summary_data)
        output_files["summary"] = summary_file
        
        return output_files
    
    def write_page_analysis(self, page: Page, filename: Optional[str] = None) -> Path:
        """Write individual page analysis to JSON."""
        if not filename:
            # Create safe filename from URL
            url_path = page.url.path.strip('/') or 'index'
            safe_filename = self._sanitize_filename(url_path) + '.json'
            filename = safe_filename
        
        page_file = self.output_directory / "pages" / filename
        page_file.parent.mkdir(parents=True, exist_ok=True)
        
        page_data = self._prepare_page_data(page)
        self._write_json_file(page_file, page_data)
        
        return page_file
    
    def _prepare_site_data(self, site: Site) -> Dict[str, Any]:
        """Prepare complete site data for JSON output."""
        return {
            "base_url": str(site.base_url),
            "domain": site.domain,
            "analysis_metadata": {
                "analysis_philosophy": site.metadata.analysis_philosophy.value,
                "target_framework": site.metadata.target_framework.value,
                "design_era": site.metadata.design_era,
                "accessibility_level": site.metadata.accessibility_level.value,
                "performance_targets": site.metadata.performance_targets,
                "analysis_date": site.metadata.analysis_date.isoformat(),
                "tool_version": site.metadata.tool_version,
                "analysis_started_at": site.analysis_started_at.isoformat(),
                "analysis_completed_at": site.analysis_completed_at.isoformat() if site.analysis_completed_at else None,
            },
            "crawl_config": {
                "max_depth": site.config.max_depth,
                "max_pages": site.config.max_pages,
                "include_assets": site.config.include_assets,
                "respect_robots_txt": site.config.respect_robots_txt,
                "rate_limit_delay": site.config.rate_limit_delay,
                "concurrent_requests": site.config.concurrent_requests,
                "browser_engine": site.config.browser_engine,
                "timeout": site.config.timeout,
            },
            "stats": site.stats.dict(),
            "sitemap_urls": [str(url) for url in site.sitemap_urls],
            "robots_txt_content": site.robots_txt_content,
            "global_design_system": {
                "color_palette": [
                    {
                        "hex": color.hex,
                        "rgb": list(color.rgb),
                        "usage_context": color.usage_context,
                        "frequency": color.frequency,
                    }
                    for color in site.global_color_palette
                ],
                "typography": [
                    {
                        "family": font.family,
                        "weights": font.weights,
                        "sizes": font.sizes,
                        "usage_context": font.usage_context,
                    }
                    for font in site.global_typography
                ],
                "design_tokens": [
                    {
                        "name": token.name,
                        "value": token.value,
                        "category": token.category,
                        "usage": token.usage,
                    }
                    for token in site.global_design_tokens
                ],
            },
            "errors": site.errors,
            "warnings": site.warnings,
        }
    
    def _prepare_pages_data(self, site: Site) -> Dict[str, Any]:
        """Prepare pages data for JSON output."""
        pages_data = {
            "total_pages": len(site.pages),
            "successful_pages": len(site.crawled_pages),
            "failed_pages": len(site.failed_pages),
            "pages": {}
        }
        
        for url, page in site.pages.items():
            pages_data["pages"][url] = {
                "summary": page.get_summary(),
                "basic_info": {
                    "title": page.title,
                    "status": page.status.value,
                    "status_code": page.status_code,
                    "depth": page.depth,
                    "content_type": page.content_type,
                    "content_length": page.content_length,
                    "discovered_at": page.discovered_at.isoformat(),
                    "crawled_at": page.crawled_at.isoformat() if page.crawled_at else None,
                    "analyzed_at": page.analyzed_at.isoformat() if page.analyzed_at else None,
                },
                "seo": {
                    "title": page.seo.title,
                    "description": page.seo.description,
                    "keywords": page.seo.keywords,
                    "og_title": page.seo.og_title,
                    "og_description": page.seo.og_description,
                    "og_image": page.seo.og_image,
                    "canonical_url": str(page.seo.canonical_url) if page.seo.canonical_url else None,
                    "schema_markup": page.seo.schema_markup,
                },
                "links": {
                    "internal_count": len(page.internal_links),
                    "external_count": len(page.external_links),
                    "children_count": len(page.children),
                    "internal_links": [str(url) for url in page.internal_links],
                    "external_links": [str(url) for url in page.external_links],
                    "children": [str(url) for url in page.children],
                    "parent_url": str(page.parent_url) if page.parent_url else None,
                },
                "assets_count": len(page.assets),
                "errors": page.errors,
                "warnings": page.warnings,
            }
        
        return pages_data
    
    def _prepare_page_data(self, page: Page) -> Dict[str, Any]:
        """Prepare detailed page data for JSON output."""
        return {
            "url": str(page.url),
            "basic_info": {
                "title": page.title,
                "status": page.status.value,
                "status_code": page.status_code,
                "redirect_url": str(page.redirect_url) if page.redirect_url else None,
                "content_type": page.content_type,
                "content_length": page.content_length,
                "depth": page.depth,
                "parent_url": str(page.parent_url) if page.parent_url else None,
                "discovered_at": page.discovered_at.isoformat(),
                "crawled_at": page.crawled_at.isoformat() if page.crawled_at else None,
                "analyzed_at": page.analyzed_at.isoformat() if page.analyzed_at else None,
            },
            "seo": {
                "title": page.seo.title,
                "description": page.seo.description,
                "keywords": page.seo.keywords,
                "og_title": page.seo.og_title,
                "og_description": page.seo.og_description,
                "og_image": page.seo.og_image,
                "canonical_url": str(page.seo.canonical_url) if page.seo.canonical_url else None,
                "schema_markup": page.seo.schema_markup,
            },
            "content": {
                "text_content": {
                    content_type.value: content_list 
                    for content_type, content_list in page.content.text_content.items()
                },
                "unique_copy": page.content.unique_copy,
                "boilerplate_text": page.content.boilerplate_text,
                "content_structure": page.content.content_structure,
            },
            "structure": {
                "components": [
                    {
                        "component_name": comp.component_name,
                        "component_type": comp.component_type.value,
                        "design_intent": comp.design_intent,
                        "modern_features": comp.modern_features,
                        "accessibility_features": comp.accessibility_features,
                        "performance_considerations": comp.performance_considerations,
                    }
                    for comp in page.structure.components
                ],
                "layout_type": page.structure.layout_type,
                "grid_system": page.structure.grid_system,
                "responsive_breakpoints": page.structure.responsive_breakpoints,
                "navigation_structure": page.structure.navigation_structure,
            },
            "design": {
                "color_palette": [
                    {
                        "hex": color.hex,
                        "rgb": list(color.rgb),
                        "usage_context": color.usage_context,
                        "frequency": color.frequency,
                    }
                    for color in page.design.color_palette
                ],
                "typography": [
                    {
                        "family": font.family,
                        "weights": font.weights,
                        "sizes": font.sizes,
                        "usage_context": font.usage_context,
                    }
                    for font in page.design.typography
                ],
                "design_tokens": [
                    {
                        "name": token.name,
                        "value": token.value,
                        "category": token.category,
                        "usage": token.usage,
                    }
                    for token in page.design.design_tokens
                ],
                "spacing_system": page.design.spacing_system,
            },
            "technical": {
                "forms": [
                    {
                        "action": form.action,
                        "method": form.method,
                        "fields": [
                            {
                                "name": field.name,
                                "type": field.type,
                                "label": field.label,
                                "placeholder": field.placeholder,
                                "required": field.required,
                                "validation_pattern": field.validation_pattern,
                            }
                            for field in form.fields
                        ],
                        "submit_text": form.submit_text,
                    }
                    for form in page.technical.forms
                ],
                "api_endpoints": page.technical.api_endpoints,
                "javascript_frameworks": page.technical.javascript_frameworks,
                "performance_metrics": page.technical.performance_metrics,
            },
            "assets": [
                {
                    "url": asset.url,
                    "local_path": str(asset.local_path) if asset.local_path else None,
                    "type": asset.type,
                    "size": asset.size,
                    "alt_text": asset.alt_text,
                    "dimensions": list(asset.dimensions) if asset.dimensions else None,
                }
                for asset in page.assets
            ],
            "links": {
                "internal": [str(url) for url in page.internal_links],
                "external": [str(url) for url in page.external_links],
                "children": [str(url) for url in page.children],
            },
            "validation": {
                "completeness_score": page.validation.completeness_score,
                "quality_metrics": page.validation.quality_metrics,
                "missing_elements": page.validation.missing_elements,
                "recommendations": page.validation.recommendations,
                "analysis_warnings": page.validation.analysis_warnings,
            },
            "errors": page.errors,
            "warnings": page.warnings,
        }
    
    def _prepare_validation_report(self, site: Site) -> Dict[str, Any]:
        """Prepare validation report for JSON output."""
        return {
            "site_validation": {
                "completeness_score": site.validation.completeness_score,
                "quality_metrics": site.validation.quality_metrics,
                "missing_elements": site.validation.missing_elements,
                "recommendations": site.validation.recommendations,
                "analysis_warnings": site.validation.analysis_warnings,
            },
            "page_validations": {
                str(page.url): {
                    "completeness_score": page.validation.completeness_score,
                    "quality_metrics": page.validation.quality_metrics,
                    "error_count": len(page.errors),
                    "warning_count": len(page.warnings),
                }
                for page in site.pages.values()
                if page.is_successful
            },
            "global_issues": {
                "total_errors": len(site.errors) + sum(len(page.errors) for page in site.pages.values()),
                "total_warnings": len(site.warnings) + sum(len(page.warnings) for page in site.pages.values()),
                "failed_pages": len(site.failed_pages),
                "incomplete_analysis": len([p for p in site.pages.values() if not p.analyzed_at]),
            },
            "recommendations": self._generate_global_recommendations(site),
        }
    
    def _generate_global_recommendations(self, site: Site) -> List[str]:
        """Generate global recommendations based on analysis."""
        recommendations = []
        
        # Check crawl success rate
        if site.stats.total_pages_discovered > 0:
            success_rate = site.stats.total_pages_crawled / site.stats.total_pages_discovered
            if success_rate < 0.8:
                recommendations.append("Low crawl success rate detected. Consider adjusting crawl settings or checking for anti-bot measures.")
        
        # Check for missing key components
        all_components = []
        for page in site.crawled_pages:
            all_components.extend([comp.component_type for comp in page.structure.components])
        
        from ..models.schemas import ComponentType
        if ComponentType.HEADER not in all_components:
            recommendations.append("No header components detected. Consider adding proper site header structure.")
        
        if ComponentType.NAVIGATION not in all_components:
            recommendations.append("No navigation components detected. Ensure proper navigation structure is implemented.")
        
        # Check for SEO issues
        pages_without_titles = [p for p in site.crawled_pages if not p.title]
        if len(pages_without_titles) > len(site.crawled_pages) * 0.2:
            recommendations.append("Many pages missing titles. Implement proper title tags for SEO.")
        
        # Check for accessibility
        pages_with_forms = [p for p in site.crawled_pages if p.technical.forms]
        if pages_with_forms:
            recommendations.append("Forms detected. Ensure proper accessibility features like labels and error handling.")
        
        return recommendations
    
    def _write_json_file(self, file_path: Path, data: Dict[str, Any]):
        """Write data to JSON file with proper formatting."""
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)
    
    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize filename for safe filesystem usage."""
        import re
        # Replace invalid characters
        filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
        # Remove multiple underscores
        filename = re.sub(r'_+', '_', filename)
        # Trim and remove leading/trailing underscores
        filename = filename.strip('_')
        # Ensure not empty
        if not filename:
            filename = 'page'
        return filename