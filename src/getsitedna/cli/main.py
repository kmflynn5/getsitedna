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
            _display_console_summary(site_data, summary_data, validation_data, analysis_dir)
        elif format == "json":
            summary_result = _generate_json_summary(site_data, summary_data, validation_data, analysis_dir)
            if output:
                with open(output, 'w', encoding='utf-8') as f:
                    json.dump(summary_result, f, indent=2)
                console.print(f"[green]Summary saved to: {output}[/green]")
            else:
                console.print_json(data=summary_result)
        elif format == "markdown":
            markdown_content = _generate_markdown_summary(site_data, summary_data, validation_data, analysis_dir)
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


def _display_console_summary(site_data: dict, summary_data: dict, validation_data: dict, analysis_dir: Path):
    """Display summary in console format."""
    from rich.table import Table
    from rich.panel import Panel
    from rich.tree import Tree
    
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
    
    # Site map with intent mapping
    _display_site_map(site_data, analysis_dir)
    
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


def _display_site_map(site_data: dict, analysis_dir: Path):
    """Display site map with intent mapping."""
    from rich.tree import Tree
    from rich.panel import Panel
    
    # Load pages data to get the full site structure
    pages_data_file = analysis_dir / "pages_data.json"
    if not pages_data_file.exists():
        console.print("\n🗺️  [yellow]Site map unavailable - pages data not found[/yellow]")
        return
    
    try:
        with open(pages_data_file, 'r', encoding='utf-8') as f:
            pages_data = json.load(f)
    except Exception as e:
        console.print(f"\n🗺️  [yellow]Site map unavailable - error loading pages data: {e}[/yellow]")
        return
    
    # Initialize intent detector
    from ..utils.intent_detection import IntentDetector
    detector = IntentDetector()
    
    # Build site map tree
    tree = Tree("🗺️  [bold blue]Site Map & Features[/bold blue]")
    
    # Group pages by hierarchy
    pages = pages_data.get("pages", {})
    root_pages = []
    child_pages = {}
    
    # Analyze each page for intent
    page_intents = {}
    all_features = set()
    
    for url, page_data in pages.items():
        # Create a simplified page object for intent detection
        from types import SimpleNamespace
        page_mock = SimpleNamespace()
        page_mock.url = url
        page_mock.title = page_data.get("basic_info", {}).get("title", "")
        page_mock.content = SimpleNamespace()
        page_mock.content.text_content = {}
        page_mock.structure = SimpleNamespace()
        page_mock.structure.components = []
        page_mock.technical = SimpleNamespace()
        page_mock.technical.forms = []
        
        # Analyze intent
        intent_data = detector.analyze_page(page_mock)
        page_intents[url] = intent_data
        all_features.update(intent_data.get("business_features", []))
        
        # Organize by hierarchy
        depth = page_data.get("basic_info", {}).get("depth", 0)
        parent_url = page_data.get("links", {}).get("parent_url")
        
        if depth == 0 or not parent_url:
            root_pages.append(url)
        else:
            if parent_url not in child_pages:
                child_pages[parent_url] = []
            child_pages[parent_url].append(url)
    
    # Add pages to tree
    added_pages = set()
    
    def add_page_to_tree(parent_node, url, depth=0):
        if url in added_pages or depth > 3:  # Prevent infinite loops and excessive depth
            return
        added_pages.add(url)
        
        page_data = pages.get(url, {})
        intent_info = page_intents.get(url, {})
        
        # Get page info
        title = page_data.get("basic_info", {}).get("title", "Untitled")
        components_count = page_data.get("summary", {}).get("components_count", 0)
        icon = intent_info.get("icon", "📄")
        description = intent_info.get("description", "")
        priority = intent_info.get("priority", "Low")
        
        # Format URL for display
        from urllib.parse import urlparse
        parsed = urlparse(url)
        display_path = parsed.path or "/"
        
        # Create node label with intent info
        priority_color = "red" if priority == "High" else "yellow" if priority == "Medium" else "green"
        node_label = f"{icon} [bold]{title}[/bold] [dim]({display_path})[/dim] [blue]\\[{components_count} components][/blue]"
        if description:
            node_label += f"\n    [dim]{description}[/dim]"
        
        page_node = parent_node.add(node_label)
        
        # Add children
        children = child_pages.get(url, [])
        for child_url in children:
            add_page_to_tree(page_node, child_url, depth + 1)
    
    # Add root pages first
    for url in sorted(root_pages):
        add_page_to_tree(tree, url)
    
    # Add any orphaned pages
    for url in pages.keys():
        if url not in added_pages:
            add_page_to_tree(tree, url)
    
    console.print()
    console.print(tree)
    
    # Show reconstruction requirements
    if all_features:
        requirements_tree = Tree("🎯 [bold green]Reconstruction Requirements[/bold green]")
        
        # Group features by category
        auth_features = [f for f in all_features if "user" in f or "login" in f or "registration" in f]
        ecommerce_features = [f for f in all_features if "payment" in f or "cart" in f or "product" in f]
        content_features = [f for f in all_features if "blog" in f or "content" in f or "search" in f]
        other_features = [f for f in all_features if f not in auth_features + ecommerce_features + content_features]
        
        if auth_features:
            auth_node = requirements_tree.add("🔐 [bold]User Management[/bold]")
            for feature in auth_features:
                auth_node.add(f"• {feature.replace('_', ' ').title()}")
        
        if ecommerce_features:
            ecomm_node = requirements_tree.add("🛒 [bold]E-commerce[/bold]")
            for feature in ecommerce_features:
                ecomm_node.add(f"• {feature.replace('_', ' ').title()}")
        
        if content_features:
            content_node = requirements_tree.add("📝 [bold]Content & Search[/bold]")
            for feature in content_features:
                content_node.add(f"• {feature.replace('_', ' ').title()}")
        
        if other_features:
            other_node = requirements_tree.add("⚙️ [bold]Other Features[/bold]")
            for feature in other_features:
                other_node.add(f"• {feature.replace('_', ' ').title()}")
        
        console.print()
        console.print(requirements_tree)


def _generate_json_summary(site_data: dict, summary_data: dict, validation_data: dict, analysis_dir: Path = None) -> dict:
    """Generate summary in JSON format."""
    result = {
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
    
    # Add site map if available
    if analysis_dir:
        site_map_data = _generate_site_map_data(analysis_dir)
        if site_map_data:
            result["site_map"] = site_map_data
    
    return result


def _generate_site_map_data(analysis_dir: Path) -> dict:
    """Generate site map data for JSON/Markdown output."""
    pages_data_file = analysis_dir / "pages_data.json"
    if not pages_data_file.exists():
        return None
    
    try:
        with open(pages_data_file, 'r', encoding='utf-8') as f:
            pages_data = json.load(f)
    except Exception:
        return None
    
    # Initialize intent detector
    from ..utils.intent_detection import IntentDetector
    detector = IntentDetector()
    
    pages = pages_data.get("pages", {})
    site_map = {
        "pages": {},
        "hierarchy": {},
        "features_required": set(),
        "reconstruction_requirements": []
    }
    
    # Analyze each page for intent
    for url, page_data in pages.items():
        # Create a simplified page object for intent detection
        from types import SimpleNamespace
        page_mock = SimpleNamespace()
        page_mock.url = url
        page_mock.title = page_data.get("basic_info", {}).get("title", "")
        page_mock.content = SimpleNamespace()
        page_mock.content.text_content = {}
        page_mock.structure = SimpleNamespace()
        page_mock.structure.components = []
        page_mock.technical = SimpleNamespace()
        page_mock.technical.forms = []
        
        # Analyze intent
        intent_data = detector.analyze_page(page_mock)
        
        # Add to site map
        site_map["pages"][url] = {
            "title": page_data.get("basic_info", {}).get("title", "Untitled"),
            "depth": page_data.get("basic_info", {}).get("depth", 0),
            "components_count": page_data.get("summary", {}).get("components_count", 0),
            "intent": intent_data.get("primary_intent"),
            "description": intent_data.get("description"),
            "priority": intent_data.get("priority"),
            "icon": intent_data.get("icon"),
            "business_features": intent_data.get("business_features", []),
            "reconstruction_requirements": intent_data.get("reconstruction_requirements", []),
            "parent_url": page_data.get("links", {}).get("parent_url"),
            "children": page_data.get("links", {}).get("children", []),
            "internal_links": page_data.get("links", {}).get("internal_links", [])
        }
        
        # Collect all features
        site_map["features_required"].update(intent_data.get("business_features", []))
    
    # Convert set to list for JSON serialization
    site_map["features_required"] = list(site_map["features_required"])
    
    # Group features by category for reconstruction requirements
    all_features = site_map["features_required"]
    auth_features = [f for f in all_features if "user" in f or "login" in f or "registration" in f]
    ecommerce_features = [f for f in all_features if "payment" in f or "cart" in f or "product" in f]
    content_features = [f for f in all_features if "blog" in f or "content" in f or "search" in f]
    
    site_map["reconstruction_requirements"] = []
    if auth_features:
        site_map["reconstruction_requirements"].append({
            "category": "User Management",
            "features": auth_features,
            "priority": "High"
        })
    if ecommerce_features:
        site_map["reconstruction_requirements"].append({
            "category": "E-commerce",
            "features": ecommerce_features,
            "priority": "High"
        })
    if content_features:
        site_map["reconstruction_requirements"].append({
            "category": "Content & Search",
            "features": content_features,
            "priority": "Medium"
        })
    
    return site_map


def _generate_site_map_markdown(analysis_dir: Path) -> str:
    """Generate site map in Markdown format."""
    site_map_data = _generate_site_map_data(analysis_dir)
    if not site_map_data:
        return ""
    
    markdown = "## 🗺️ Site Map & Features\n\n"
    
    # Build hierarchical structure
    pages = site_map_data["pages"]
    root_pages = [url for url, data in pages.items() if data["depth"] == 0 or not data["parent_url"]]
    
    def add_page_to_markdown(url, depth=0):
        if url not in pages:
            return ""
        
        page = pages[url]
        indent = "  " * depth
        icon = page.get("icon", "📄")
        title = page.get("title", "Untitled")
        description = page.get("description", "")
        components = page.get("components_count", 0)
        
        from urllib.parse import urlparse
        parsed = urlparse(url)
        display_path = parsed.path or "/"
        
        result = f"{indent}- {icon} **{title}** (`{display_path}`) - {components} components\n"
        if description:
            result += f"{indent}  *{description}*\n"
        
        # Add children
        children = page.get("children", [])
        for child_url in sorted(children):
            result += add_page_to_markdown(child_url, depth + 1)
        
        return result
    
    # Add root pages
    for url in sorted(root_pages):
        markdown += add_page_to_markdown(url)
    
    # Add reconstruction requirements
    if site_map_data.get("reconstruction_requirements"):
        markdown += "\n## 🎯 Reconstruction Requirements\n\n"
        
        for req_category in site_map_data["reconstruction_requirements"]:
            category = req_category["category"]
            features = req_category["features"]
            priority = req_category["priority"]
            
            priority_emoji = "🔴" if priority == "High" else "🟡" if priority == "Medium" else "🟢"
            markdown += f"### {priority_emoji} {category} ({priority} Priority)\n\n"
            
            for feature in features:
                feature_name = feature.replace("_", " ").title()
                markdown += f"- {feature_name}\n"
            
            markdown += "\n"
        
        # Add implementation suggestions
        markdown += "### 💡 Implementation Suggestions\n\n"
        all_features = site_map_data["features_required"]
        
        if any("payment" in f for f in all_features):
            markdown += "- **Payment Processing**: Consider Stripe or PayPal integration\n"
        if any("user" in f for f in all_features):
            markdown += "- **User Management**: Implement JWT-based authentication\n"
        if any("cart" in f for f in all_features):
            markdown += "- **Shopping Cart**: Use local storage or session management\n"
        if any("search" in f for f in all_features):
            markdown += "- **Search**: Consider Elasticsearch or Algolia integration\n"
        if any("blog" in f for f in all_features):
            markdown += "- **Content Management**: Headless CMS like Strapi or Contentful\n"
        
        markdown += "\n"
    
    return markdown


def _generate_markdown_summary(site_data: dict, summary_data: dict, validation_data: dict, analysis_dir: Path = None) -> str:
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

"""
    
    # Add site map if available
    if analysis_dir:
        site_map_markdown = _generate_site_map_markdown(analysis_dir)
        if site_map_markdown:
            markdown += site_map_markdown
    
    markdown += f"""## 🎨 Design Analysis
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
cli.add_command(validate_cmd, name="validate")


if __name__ == "__main__":
    cli()