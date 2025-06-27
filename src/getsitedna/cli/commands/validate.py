"""Validation command for verifying analysis output quality."""

import json
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from ...models.site import Site
from ...models.page import Page
from ...outputs.json_writer import JSONWriter
from ...utils.error_handling import ErrorHandler, AnalysisError, ErrorSeverity


console = Console()


class AnalysisValidator:
    """Validate analysis results for completeness and quality."""
    
    def __init__(self):
        self.error_handler = ErrorHandler("getsitedna.validator")
        self.validation_rules = self._setup_validation_rules()
    
    def _setup_validation_rules(self) -> Dict[str, Dict]:
        """Set up validation rules for different aspects of analysis."""
        return {
            "site_structure": {
                "required_fields": ["base_url", "domain", "pages"],
                "min_pages": 1,
                "max_error_rate": 0.3
            },
            "page_content": {
                "required_fields": ["url", "title", "content"],
                "min_content_length": 10,
                "required_seo_fields": ["title", "description"]
            },
            "design_analysis": {
                "min_colors": 1,
                "min_fonts": 1,
                "required_design_elements": ["color_palette", "typography"]
            },
            "component_analysis": {
                "min_components": 1,
                "required_component_fields": ["component_name", "component_type", "design_intent"]
            },
            "output_files": {
                "required_json_files": ["specification.json", "site_data.json", "validation_report.json"],
                "required_markdown_files": ["README.md", "TECHNICAL_SPECIFICATION.md"]
            }
        }
    
    def validate_analysis_directory(self, analysis_dir: Path) -> Dict[str, Any]:
        """Validate an entire analysis directory."""
        console.print(f"[bold blue]Validating analysis directory:[/bold blue] {analysis_dir}")
        
        validation_results = {
            "overall_score": 0.0,
            "passed_checks": 0,
            "total_checks": 0,
            "issues": [],
            "recommendations": [],
            "file_validation": {},
            "content_validation": {},
            "completeness_score": 0.0
        }
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            
            # Check directory structure
            task = progress.add_task("Validating directory structure...", total=None)
            structure_results = self._validate_directory_structure(analysis_dir)
            validation_results["file_validation"] = structure_results
            progress.advance(task)
            
            # Load and validate site data
            progress.update(task, description="Loading site data...")
            site_data = self._load_site_data(analysis_dir)
            if site_data:
                content_results = self._validate_site_content(site_data)
                validation_results["content_validation"] = content_results
            progress.advance(task)
            
            # Validate JSON schema compliance
            progress.update(task, description="Validating JSON schemas...")
            schema_results = self._validate_json_schemas(analysis_dir)
            validation_results["schema_validation"] = schema_results
            progress.advance(task)
            
            # Calculate overall scores
            progress.update(task, description="Calculating scores...")
            self._calculate_validation_scores(validation_results)
            progress.complete_task(task)
        
        return validation_results
    
    def _validate_directory_structure(self, analysis_dir: Path) -> Dict[str, Any]:
        """Validate the directory structure and required files."""
        results = {
            "required_files_present": [],
            "missing_files": [],
            "unexpected_files": [],
            "file_sizes": {},
            "directory_score": 0.0
        }
        
        if not analysis_dir.exists():
            results["missing_files"].append("Analysis directory does not exist")
            return results
        
        # Check required JSON files
        required_json = self.validation_rules["output_files"]["required_json_files"]
        for filename in required_json:
            file_path = analysis_dir / filename
            if file_path.exists():
                results["required_files_present"].append(filename)
                results["file_sizes"][filename] = file_path.stat().st_size
            else:
                results["missing_files"].append(filename)
        
        # Check required Markdown files
        required_md = self.validation_rules["output_files"]["required_markdown_files"]
        for filename in required_md:
            file_path = analysis_dir / filename
            if file_path.exists():
                results["required_files_present"].append(filename)
                results["file_sizes"][filename] = file_path.stat().st_size
            else:
                results["missing_files"].append(filename)
        
        # Check for pages directory
        pages_dir = analysis_dir / "pages"
        if pages_dir.exists() and pages_dir.is_dir():
            results["required_files_present"].append("pages/")
            page_files = list(pages_dir.glob("*.json"))
            results["file_sizes"]["pages/"] = len(page_files)
        else:
            results["missing_files"].append("pages/")
        
        # Calculate directory score
        total_required = len(required_json) + len(required_md) + 1  # +1 for pages dir
        present_count = len(results["required_files_present"])
        results["directory_score"] = present_count / total_required
        
        return results
    
    def _load_site_data(self, analysis_dir: Path) -> Optional[Dict]:
        """Load site data from JSON files."""
        try:
            site_data_file = analysis_dir / "site_data.json"
            if site_data_file.exists():
                with open(site_data_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            self.error_handler.handle_error(e, {"file": "site_data.json"})
        
        return None
    
    def _validate_site_content(self, site_data: Dict) -> Dict[str, Any]:
        """Validate site content quality and completeness."""
        results = {
            "site_validation": {},
            "pages_validation": {},
            "design_validation": {},
            "components_validation": {},
            "content_score": 0.0
        }
        
        # Validate site structure
        site_rules = self.validation_rules["site_structure"]
        site_validation = self._validate_required_fields(site_data, site_rules["required_fields"])
        results["site_validation"] = site_validation
        
        # Validate design analysis
        design_data = site_data.get("global_design_system", {})
        design_validation = self._validate_design_analysis(design_data)
        results["design_validation"] = design_validation
        
        # Load and validate pages
        if "statistics" in site_data:
            stats = site_data["statistics"]
            pages_validation = self._validate_pages_statistics(stats)
            results["pages_validation"] = pages_validation
        
        # Calculate content score
        scores = [
            site_validation.get("completeness", 0.0),
            design_validation.get("completeness", 0.0),
            pages_validation.get("completeness", 0.0)
        ]
        results["content_score"] = sum(scores) / len(scores)
        
        return results
    
    def _validate_design_analysis(self, design_data: Dict) -> Dict[str, Any]:
        """Validate design analysis completeness."""
        results = {
            "colors_found": 0,
            "fonts_found": 0,
            "tokens_found": 0,
            "completeness": 0.0,
            "issues": []
        }
        
        # Check color palette
        colors = design_data.get("color_palette", [])
        results["colors_found"] = len(colors)
        
        if len(colors) < self.validation_rules["design_analysis"]["min_colors"]:
            results["issues"].append("Insufficient color analysis - very few colors detected")
        
        # Check typography
        fonts = design_data.get("typography", [])
        results["fonts_found"] = len(fonts)
        
        if len(fonts) < self.validation_rules["design_analysis"]["min_fonts"]:
            results["issues"].append("Insufficient typography analysis - very few fonts detected")
        
        # Check design tokens
        tokens = design_data.get("design_tokens", [])
        results["tokens_found"] = len(tokens)
        
        # Calculate completeness
        color_score = min(len(colors) / 5, 1.0)  # Expect at least 5 colors
        font_score = min(len(fonts) / 3, 1.0)    # Expect at least 3 fonts
        token_score = min(len(tokens) / 10, 1.0) # Expect at least 10 tokens
        
        results["completeness"] = (color_score + font_score + token_score) / 3
        
        return results
    
    def _validate_pages_statistics(self, stats: Dict) -> Dict[str, Any]:
        """Validate page analysis statistics."""
        results = {
            "total_pages": stats.get("total_pages_discovered", 0),
            "crawled_pages": stats.get("total_pages_crawled", 0),
            "analyzed_pages": stats.get("total_pages_analyzed", 0),
            "success_rate": 0.0,
            "analysis_rate": 0.0,
            "completeness": 0.0,
            "issues": []
        }
        
        total = results["total_pages"]
        crawled = results["crawled_pages"]
        analyzed = results["analyzed_pages"]
        
        if total > 0:
            results["success_rate"] = crawled / total
            results["analysis_rate"] = analyzed / total
            
            if results["success_rate"] < 0.7:
                results["issues"].append("Low crawl success rate - many pages failed to load")
            
            if results["analysis_rate"] < 0.8:
                results["issues"].append("Low analysis completion rate - many pages not fully analyzed")
            
            # Completeness is average of success and analysis rates
            results["completeness"] = (results["success_rate"] + results["analysis_rate"]) / 2
        
        return results
    
    def _validate_json_schemas(self, analysis_dir: Path) -> Dict[str, Any]:
        """Validate JSON files against expected schemas."""
        results = {
            "valid_files": [],
            "invalid_files": [],
            "schema_errors": {},
            "schema_score": 0.0
        }
        
        json_files = [
            "specification.json",
            "site_data.json",
            "pages_data.json",
            "validation_report.json",
            "analysis_summary.json"
        ]
        
        for filename in json_files:
            file_path = analysis_dir / filename
            if file_path.exists():
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    # Basic validation - check if it's valid JSON and has expected structure
                    if self._validate_json_structure(filename, data):
                        results["valid_files"].append(filename)
                    else:
                        results["invalid_files"].append(filename)
                        
                except json.JSONDecodeError as e:
                    results["invalid_files"].append(filename)
                    results["schema_errors"][filename] = f"JSON parsing error: {e}"
                
                except Exception as e:
                    results["invalid_files"].append(filename)
                    results["schema_errors"][filename] = f"Validation error: {e}"
        
        # Calculate schema score
        total_files = len([f for f in json_files if (analysis_dir / f).exists()])
        valid_files = len(results["valid_files"])
        results["schema_score"] = valid_files / total_files if total_files > 0 else 0.0
        
        return results
    
    def _validate_json_structure(self, filename: str, data: Dict) -> bool:
        """Validate JSON structure for specific files."""
        if filename == "specification.json":
            required_sections = ["metadata", "design_intent", "component_specifications"]
            return all(section in data for section in required_sections)
        
        elif filename == "site_data.json":
            required_fields = ["base_url", "domain", "analysis_metadata"]
            return all(field in data for field in required_fields)
        
        elif filename == "pages_data.json":
            required_fields = ["total_pages", "pages"]
            return all(field in data for field in required_fields)
        
        elif filename == "validation_report.json":
            required_fields = ["site_validation", "global_issues"]
            return all(field in data for field in required_fields)
        
        return True  # Default to valid for unknown files
    
    def _validate_required_fields(self, data: Dict, required_fields: List[str]) -> Dict[str, Any]:
        """Validate that required fields are present in data."""
        results = {
            "present_fields": [],
            "missing_fields": [],
            "completeness": 0.0
        }
        
        for field in required_fields:
            if field in data and data[field] is not None:
                results["present_fields"].append(field)
            else:
                results["missing_fields"].append(field)
        
        results["completeness"] = len(results["present_fields"]) / len(required_fields)
        
        return results
    
    def _calculate_validation_scores(self, validation_results: Dict[str, Any]):
        """Calculate overall validation scores."""
        scores = []
        
        # Directory structure score
        if "file_validation" in validation_results:
            scores.append(validation_results["file_validation"].get("directory_score", 0.0))
        
        # Content quality score
        if "content_validation" in validation_results:
            scores.append(validation_results["content_validation"].get("content_score", 0.0))
        
        # Schema compliance score
        if "schema_validation" in validation_results:
            scores.append(validation_results["schema_validation"].get("schema_score", 0.0))
        
        # Calculate overall score
        if scores:
            validation_results["overall_score"] = sum(scores) / len(scores)
            validation_results["completeness_score"] = validation_results["overall_score"]
        
        # Generate recommendations
        validation_results["recommendations"] = self._generate_recommendations(validation_results)
    
    def _generate_recommendations(self, validation_results: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on validation results."""
        recommendations = []
        
        # File structure recommendations
        file_validation = validation_results.get("file_validation", {})
        missing_files = file_validation.get("missing_files", [])
        
        if missing_files:
            recommendations.append(
                f"Missing {len(missing_files)} required files. "
                f"Re-run analysis to generate: {', '.join(missing_files[:3])}"
            )
        
        # Content quality recommendations
        content_validation = validation_results.get("content_validation", {})
        design_validation = content_validation.get("design_validation", {})
        
        if design_validation.get("colors_found", 0) < 3:
            recommendations.append(
                "Very few colors detected in design analysis. "
                "Check if CSS files are accessible or site uses external stylesheets."
            )
        
        if design_validation.get("fonts_found", 0) < 2:
            recommendations.append(
                "Limited typography analysis. "
                "Verify that font information is accessible in the site's CSS."
            )
        
        # Pages analysis recommendations
        pages_validation = content_validation.get("pages_validation", {})
        success_rate = pages_validation.get("success_rate", 1.0)
        
        if success_rate < 0.7:
            recommendations.append(
                "Low page crawl success rate. "
                "Consider increasing timeout values or using static crawler mode."
            )
        
        # Overall quality recommendations
        overall_score = validation_results.get("overall_score", 0.0)
        
        if overall_score < 0.6:
            recommendations.append(
                "Analysis quality is below acceptable threshold. "
                "Consider re-running analysis with adjusted parameters."
            )
        
        return recommendations
    
    def display_validation_results(self, results: Dict[str, Any]):
        """Display validation results in a formatted way."""
        # Overall score panel
        score = results.get("overall_score", 0.0)
        score_color = "green" if score >= 0.8 else "yellow" if score >= 0.6 else "red"
        
        console.print(Panel.fit(
            f"[bold {score_color}]Overall Validation Score: {score:.1%}[/bold {score_color}]",
            border_style=score_color
        ))
        
        # File validation table
        if "file_validation" in results:
            self._display_file_validation(results["file_validation"])
        
        # Content validation table
        if "content_validation" in results:
            self._display_content_validation(results["content_validation"])
        
        # Recommendations
        recommendations = results.get("recommendations", [])
        if recommendations:
            console.print("\n[bold yellow]Recommendations:[/bold yellow]")
            for i, rec in enumerate(recommendations, 1):
                console.print(f"{i}. {rec}")
    
    def _display_file_validation(self, file_results: Dict[str, Any]):
        """Display file validation results."""
        console.print("\n[bold cyan]File Structure Validation[/bold cyan]")
        
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Category", style="cyan")
        table.add_column("Status", style="white")
        table.add_column("Details", style="dim")
        
        present = file_results.get("required_files_present", [])
        missing = file_results.get("missing_files", [])
        
        table.add_row("Required Files Present", f"{len(present)}", ", ".join(present[:5]))
        table.add_row("Missing Files", f"{len(missing)}", ", ".join(missing) if missing else "None")
        table.add_row("Directory Score", f"{file_results.get('directory_score', 0):.1%}", "")
        
        console.print(table)
    
    def _display_content_validation(self, content_results: Dict[str, Any]):
        """Display content validation results."""
        console.print("\n[bold cyan]Content Quality Validation[/bold cyan]")
        
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Aspect", style="cyan")
        table.add_column("Score", style="white")
        table.add_column("Details", style="dim")
        
        # Design validation
        design = content_results.get("design_validation", {})
        table.add_row(
            "Design Analysis", 
            f"{design.get('completeness', 0):.1%}",
            f"Colors: {design.get('colors_found', 0)}, Fonts: {design.get('fonts_found', 0)}"
        )
        
        # Pages validation
        pages = content_results.get("pages_validation", {})
        table.add_row(
            "Page Analysis",
            f"{pages.get('completeness', 0):.1%}",
            f"Success Rate: {pages.get('success_rate', 0):.1%}"
        )
        
        # Overall content score
        table.add_row(
            "Overall Content",
            f"{content_results.get('content_score', 0):.1%}",
            ""
        )
        
        console.print(table)


@click.command()
@click.argument("analysis_dir", type=click.Path(exists=True, path_type=Path))
@click.option("--detailed", "-d", is_flag=True, help="Show detailed validation results")
@click.option("--output", "-o", type=click.Path(path_type=Path), help="Save validation report to file")
def validate(analysis_dir: Path, detailed: bool, output: Optional[Path]):
    """Validate analysis output structure and completeness."""
    validator = AnalysisValidator()
    
    try:
        results = validator.validate_analysis_directory(analysis_dir)
        
        # Display results
        validator.display_validation_results(results)
        
        # Save detailed report if requested
        if output:
            with open(output, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, default=str)
            console.print(f"\n[green]Detailed validation report saved to: {output}[/green]")
        
        # Exit with appropriate code
        if results.get("overall_score", 0.0) < 0.6:
            console.print("\n[red]Validation failed - analysis quality below threshold[/red]")
            exit(1)
        else:
            console.print("\n[green]✓ Validation passed[/green]")
    
    except Exception as e:
        console.print(f"[red]Validation failed with error: {e}[/red]")
        exit(1)