"""Main CLI entry point for GetSiteDNA."""

import click
import json
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()


@click.group()
@click.version_option()
def cli():
    """GetSiteDNA - Comprehensive website analysis tool for AI-assisted reconstruction."""
    pass


@cli.command()
@click.argument("url")
@click.option(
    "--output", "-o",
    type=click.Path(path_type=Path),
    default="./analysis",
    help="Output directory for analysis results"
)
@click.option(
    "--depth", "-d",
    type=int,
    default=2,
    help="Maximum crawling depth"
)
@click.option(
    "--max-pages", "-p",
    type=int,
    default=50,
    help="Maximum number of pages to analyze"
)
@click.option(
    "--include-assets/--no-assets",
    default=True,
    help="Include asset extraction (images, CSS, etc.)"
)
@click.option(
    "--interactive", "-i",
    is_flag=True,
    help="Run in interactive mode with guided prompts"
)
@click.option(
    "--browser",
    type=click.Choice(["chromium", "firefox", "webkit"]),
    default="chromium",
    help="Browser engine for dynamic content"
)
def analyze(
    url: str,
    output: Path,
    depth: int,
    max_pages: int,
    include_assets: bool,
    interactive: bool,
    browser: str
):
    """Analyze a website and generate comprehensive specifications."""
    console.print(f"[bold blue]Analyzing website:[/bold blue] {url}")
    console.print(f"[dim]Output directory:[/dim] {output}")
    console.print(f"[dim]Max depth:[/dim] {depth}, [dim]Max pages:[/dim] {max_pages}")
    
    if interactive:
        console.print("[yellow]Interactive mode enabled - you'll be prompted for preferences[/yellow]")
    
    # Run the actual analysis
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Initializing analysis...", total=None)
            
            # Import and run the analyzer
            from ..core.analyzer import analyze_website
            from ..models.site import CrawlConfig
            
            # Build configuration
            config = {
                "crawl_config": {
                    "max_depth": depth,
                    "max_pages": max_pages,
                },
                "use_dynamic_crawler": True,
                "generate_markdown": True,
                "download_assets": include_assets
            }
            
            progress.update(task, description="Running analysis...")
            
            # Run the analysis
            import asyncio
            site = asyncio.run(analyze_website(url, config, output))
            
            progress.update(task, description="Analysis complete!")
    except Exception as e:
        console.print(f"[bold red]✗[/bold red] Analysis failed: {str(e)}")
        raise click.Abort()
    
    console.print("[bold green]✓[/bold green] Analysis completed successfully!")
    console.print(f"[dim]Results saved to:[/dim] {output}")


@cli.command()
@click.argument("analysis_dir", type=click.Path(exists=True, path_type=Path))
@click.option("--detailed", "-d", is_flag=True, help="Show detailed validation results")
@click.option("--output", "-o", type=click.Path(path_type=Path), help="Save validation report to file")
def validate(analysis_dir: Path, detailed: bool, output: Optional[Path]):
    """Validate analysis output structure and completeness."""
    from .commands.validate import AnalysisValidator
    
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
            raise click.ClickException("Validation failed")
        else:
            console.print("\n[green]✓ Validation passed[/green]")
    
    except Exception as e:
        if not isinstance(e, click.ClickException):
            console.print(f"[red]Validation failed with error: {e}[/red]")
            raise click.ClickException(f"Validation error: {e}")
        raise


@cli.command()
@click.argument("analysis_dir", type=click.Path(exists=True, path_type=Path))
@click.option("--format", "-f", type=click.Choice(["console", "json", "markdown"]), default="console", help="Output format")
@click.option("--output", "-o", type=click.Path(path_type=Path), help="Save summary to file")
def summary(analysis_dir: Path, format: str, output: Optional[Path]):
    """Generate human-readable summary of analysis results."""
    from rich.table import Table
    from rich.panel import Panel
    
    try:
        # Load analysis data
        site_data_file = analysis_dir / "site_data.json"
        summary_file = analysis_dir / "analysis_summary.json"
        validation_file = analysis_dir / "validation_report.json"
        
        if not site_data_file.exists():
            raise click.ClickException(f"Analysis data not found: {site_data_file}")
        
        with open(site_data_file, 'r', encoding='utf-8') as f:
            site_data = json.load(f)
        
        summary_data = {}
        if summary_file.exists():
            with open(summary_file, 'r', encoding='utf-8') as f:
                summary_data = json.load(f)
        
        validation_data = {}
        if validation_file.exists():
            with open(validation_file, 'r', encoding='utf-8') as f:
                validation_data = json.load(f)
        
        if format == "console":
            _display_console_summary(site_data, summary_data, validation_data)
        elif format == "json":
            summary_result = _generate_json_summary(site_data, summary_data, validation_data)
            if output:
                with open(output, 'w', encoding='utf-8') as f:
                    json.dump(summary_result, f, indent=2)
                console.print(f"[green]Summary saved to: {output}[/green]")
            else:
                console.print_json(data=summary_result)
        elif format == "markdown":
            markdown_content = _generate_markdown_summary(site_data, summary_data, validation_data)
            if output:
                with open(output, 'w', encoding='utf-8') as f:
                    f.write(markdown_content)
                console.print(f"[green]Summary saved to: {output}[/green]")
            else:
                console.print(markdown_content)
        
        console.print("\n[green]✓ Summary generated successfully![/green]")
        
    except Exception as e:
        console.print(f"[red]Summary generation failed: {e}[/red]")
        raise click.ClickException(f"Summary error: {e}")


@cli.group()
def config():
    """Configuration management commands."""
    pass


@config.command("init")
@click.option(
    "--output", "-o",
    type=click.Path(path_type=Path),
    default="./getsitedna.config.json",
    help="Config file location"
)
@click.option("--overwrite", is_flag=True, help="Overwrite existing config file")
def config_init(output: Path, overwrite: bool):
    """Create a default configuration file."""
    if output.exists() and not overwrite:
        console.print(f"[yellow]Config file already exists: {output}[/yellow]")
        console.print("[dim]Use --overwrite to replace it[/dim]")
        return
    
    # Create default configuration
    default_config = {
        "crawl_config": {
            "max_depth": 2,
            "max_pages": 50,
            "include_assets": True,
            "respect_robots_txt": True,
            "rate_limit_delay": 1.0,
            "concurrent_requests": 5,
            "browser_engine": "chromium",
            "timeout": 30
        },
        "metadata": {
            "analysis_philosophy": "modern_interpretation",
            "target_framework": "react_nextjs",
            "design_era": "2025_modern_web",
            "accessibility_level": "wcag_aa",
            "performance_targets": [
                "core_web_vitals_optimized"
            ]
        },
        "output_config": {
            "generate_markdown": True,
            "download_assets": False,
            "use_dynamic_crawler": True
        }
    }
    
    try:
        with open(output, 'w', encoding='utf-8') as f:
            json.dump(default_config, f, indent=2)
        
        console.print(f"[bold green]✓[/bold green] Configuration file created: {output}")
        console.print("\n[dim]You can now customize the configuration and use it with:[/dim]")
        console.print(f"[dim]  getsitedna analyze <url> --config {output}[/dim]")
        
    except Exception as e:
        console.print(f"[red]Failed to create config file: {e}[/red]")
        raise click.ClickException(f"Config creation error: {e}")


def _display_console_summary(site_data: dict, summary_data: dict, validation_data: dict):
    """Display summary in console format."""
    from rich.table import Table
    from rich.panel import Panel
    
    # Site overview
    base_url = site_data.get("base_url", "Unknown")
    domain = site_data.get("domain", "Unknown")
    
    console.print(Panel.fit(
        f"[bold blue]{base_url}[/bold blue]\n"
        f"Domain: {domain}",
        title="🌐 Site Analysis Summary",
        border_style="blue"
    ))
    
    # Statistics table
    stats = site_data.get("statistics", {})
    table = Table(title="📊 Analysis Statistics")
    table.add_column("Metric", style="cyan")
    table.add_column("Count", style="magenta")
    
    table.add_row("Pages Crawled", str(stats.get("total_pages_crawled", 0)))
    table.add_row("Pages Analyzed", str(stats.get("total_pages_analyzed", 0)))
    table.add_row("Components Found", str(stats.get("total_components_identified", 0)))
    table.add_row("Assets Downloaded", str(stats.get("total_assets_downloaded", 0)))
    table.add_row("API Endpoints", str(len(site_data.get("technical_modernization", {}).get("api_endpoints", []))))
    
    console.print(table)
    
    # Design intent
    design_intent = summary_data.get("design_intent", {})
    if design_intent.get("brand_personality"):
        console.print(f"\n🎨 [bold]Brand Personality:[/bold] {', '.join(design_intent['brand_personality'])}")
    if design_intent.get("conversion_focus"):
        console.print(f"🎯 [bold]Conversion Focus:[/bold] {design_intent['conversion_focus']}")
    
    # Validation score
    validation_score = summary_data.get("validation_score", 0)
    score_color = "green" if validation_score >= 0.8 else "yellow" if validation_score >= 0.6 else "red"
    console.print(f"\n✅ [bold {score_color}]Validation Score: {validation_score:.1%}[/bold {score_color}]")


def _generate_json_summary(site_data: dict, summary_data: dict, validation_data: dict) -> dict:
    """Generate summary in JSON format."""
    return {
        "site_info": {
            "base_url": site_data.get("base_url"),
            "domain": site_data.get("domain"),
            "analysis_date": summary_data.get("analysis_date")
        },
        "statistics": site_data.get("statistics", {}),
        "design_intent": summary_data.get("design_intent", {}),
        "validation": {
            "score": summary_data.get("validation_score", 0),
            "details": validation_data.get("site_validation", {})
        },
        "technical_summary": {
            "api_endpoints": len(site_data.get("technical_modernization", {}).get("api_endpoints", [])),
            "global_colors": summary_data.get("global_colors_count", 0),
            "global_fonts": summary_data.get("global_fonts_count", 0)
        }
    }


def _generate_markdown_summary(site_data: dict, summary_data: dict, validation_data: dict) -> str:
    """Generate summary in Markdown format."""
    base_url = site_data.get("base_url", "Unknown")
    domain = site_data.get("domain", "Unknown")
    stats = site_data.get("statistics", {})
    design_intent = summary_data.get("design_intent", {})
    
    markdown = f"""# Site Analysis Summary

## 🌐 Site Information
- **URL**: {base_url}
- **Domain**: {domain}
- **Analysis Date**: {summary_data.get('analysis_date', 'Unknown')}

## 📊 Statistics
- **Pages Crawled**: {stats.get('total_pages_crawled', 0)}
- **Pages Analyzed**: {stats.get('total_pages_analyzed', 0)}
- **Components Identified**: {stats.get('total_components_identified', 0)}
- **Assets Downloaded**: {stats.get('total_assets_downloaded', 0)}
- **Analysis Duration**: {stats.get('analysis_duration_seconds', 0):.1f}s

## 🎨 Design Analysis
"""
    
    if design_intent.get("brand_personality"):
        markdown += f"- **Brand Personality**: {', '.join(design_intent['brand_personality'])}\n"
    if design_intent.get("conversion_focus"):
        markdown += f"- **Conversion Focus**: {design_intent['conversion_focus']}\n"
    
    markdown += f"- **Global Colors**: {summary_data.get('global_colors_count', 0)}\n"
    markdown += f"- **Global Fonts**: {summary_data.get('global_fonts_count', 0)}\n"
    
    validation_score = summary_data.get("validation_score", 0)
    markdown += f"\n## ✅ Quality Assessment\n- **Validation Score**: {validation_score:.1%}\n"
    
    return markdown


# Import and register performance commands
from .commands.performance import performance
cli.add_command(performance)

# Import validation commands
from .commands.validate import validate as validate_cmd
cli.add_command(validate_cmd, name="validate-analysis")


if __name__ == "__main__":
    cli()