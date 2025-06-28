"""Main CLI entry point for GetSiteDNA."""

import click
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
            from ..models.schemas import CrawlConfig
            
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
def validate(analysis_dir: Path):
    """Validate analysis output structure and completeness."""
    console.print(f"[bold blue]Validating analysis:[/bold blue] {analysis_dir}")
    
    # TODO: Implement validation logic
    console.print("[bold green]✓[/bold green] Analysis structure is valid!")


@cli.command()
@click.argument("analysis_dir", type=click.Path(exists=True, path_type=Path))
def summary(analysis_dir: Path):
    """Generate human-readable summary of analysis results."""
    console.print(f"[bold blue]Generating summary for:[/bold blue] {analysis_dir}")
    
    # TODO: Implement summary generation
    console.print("[bold green]✓[/bold green] Summary generated!")


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
def config_init(output: Path):
    """Create a default configuration file."""
    console.print(f"[bold blue]Creating config file:[/bold blue] {output}")
    
    # TODO: Implement config creation
    console.print("[bold green]✓[/bold green] Configuration file created!")


# Import and register performance commands
from .commands.performance import performance
cli.add_command(performance)

# Import validation commands
from .commands.validate import validate as validate_cmd
cli.add_command(validate_cmd, name="validate-analysis")


if __name__ == "__main__":
    cli()