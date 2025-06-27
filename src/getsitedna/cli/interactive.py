"""Interactive CLI mode with guided prompts."""

from pathlib import Path
from typing import Optional, Dict, Any, List

import click
from rich.console import Console
from rich.prompt import Prompt, Confirm, IntPrompt
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

from ..models.schemas import AnalysisPhilosophy, TargetFramework, AccessibilityLevel
from ..models.site import CrawlConfig, Site
from ..models.schemas import AnalysisMetadata


console = Console()


class InteractiveCLI:
    """Interactive CLI for guided website analysis."""
    
    def __init__(self):
        self.config = {}
        self.metadata = {}
        
    def run_interactive_analysis(self, url: str, output_dir: Optional[Path] = None) -> Dict[str, Any]:
        """Run interactive analysis with user prompts."""
        console.print(Panel.fit(
            "[bold blue]GetSiteDNA Interactive Analysis[/bold blue]\n"
            "Let's configure your website analysis with guided prompts.",
            border_style="blue"
        ))
        
        # Welcome and URL confirmation
        console.print(f"\n[bold]Target URL:[/bold] {url}")
        if not Confirm.ask("Is this the correct URL to analyze?", default=True):
            new_url = Prompt.ask("Please enter the correct URL")
            url = new_url
        
        # Get analysis philosophy
        philosophy = self._get_analysis_philosophy()
        
        # Get target framework
        framework = self._get_target_framework()
        
        # Get accessibility level
        accessibility = self._get_accessibility_level()
        
        # Get crawl configuration
        crawl_config = self._get_crawl_configuration()
        
        # Get output preferences
        output_config = self._get_output_preferences(output_dir)
        
        # Get analysis scope
        analysis_scope = self._get_analysis_scope()
        
        # Summary and confirmation
        if self._show_configuration_summary(url, philosophy, framework, accessibility, crawl_config, output_config, analysis_scope):
            return {
                'url': url,
                'philosophy': philosophy,
                'framework': framework,
                'accessibility': accessibility,
                'crawl_config': crawl_config,
                'output_config': output_config,
                'analysis_scope': analysis_scope
            }
        else:
            console.print("[yellow]Analysis cancelled by user.[/yellow]")
            return {}
    
    def _get_analysis_philosophy(self) -> AnalysisPhilosophy:
        """Get the user's preferred analysis philosophy."""
        console.print("\n[bold cyan]Step 1: Analysis Philosophy[/bold cyan]")
        console.print("How would you like GetSiteDNA to approach the analysis?")
        
        philosophies = [
            ("Modern Interpretation", "Focus on modern web patterns and best practices", AnalysisPhilosophy.MODERN_INTERPRETATION),
            ("Pixel Perfect", "Maintain exact visual fidelity to the original", AnalysisPhilosophy.PIXEL_PERFECT),
            ("Component Focused", "Emphasize reusable component architecture", AnalysisPhilosophy.COMPONENT_FOCUSED)
        ]
        
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Option", style="cyan", width=20)
        table.add_column("Description", style="white")
        
        for i, (name, desc, _) in enumerate(philosophies, 1):
            table.add_row(f"{i}. {name}", desc)
        
        console.print(table)
        
        choice = IntPrompt.ask(
            "Choose your analysis philosophy",
            choices=[str(i) for i in range(1, len(philosophies) + 1)],
            default="1"
        )
        
        return philosophies[choice - 1][2]
    
    def _get_target_framework(self) -> TargetFramework:
        """Get the user's target framework."""
        console.print("\n[bold cyan]Step 2: Target Framework[/bold cyan]")
        console.print("What modern framework should the analysis target?")
        
        frameworks = [
            ("React + Next.js", "Modern React with Next.js for SSR/SSG", TargetFramework.REACT_NEXTJS),
            ("Vue + Nuxt", "Vue.js with Nuxt for SSR/SSG", TargetFramework.VUE_NUXT),
            ("Svelte + SvelteKit", "Svelte with SvelteKit", TargetFramework.SVELTE_SVELTEKIT),
            ("Vanilla JS", "Pure JavaScript without frameworks", TargetFramework.VANILLA_JS)
        ]
        
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Option", style="cyan", width=20)
        table.add_column("Description", style="white")
        
        for i, (name, desc, _) in enumerate(frameworks, 1):
            table.add_row(f"{i}. {name}", desc)
        
        console.print(table)
        
        choice = IntPrompt.ask(
            "Choose your target framework",
            choices=[str(i) for i in range(1, len(frameworks) + 1)],
            default="1"
        )
        
        return frameworks[choice - 1][2]
    
    def _get_accessibility_level(self) -> AccessibilityLevel:
        """Get the desired accessibility compliance level."""
        console.print("\n[bold cyan]Step 3: Accessibility Level[/bold cyan]")
        console.print("What accessibility compliance level should we target?")
        
        levels = [
            ("WCAG 2.1 AA", "Recommended standard for most websites", AccessibilityLevel.WCAG_AA),
            ("WCAG 2.1 A", "Basic accessibility compliance", AccessibilityLevel.WCAG_A),
            ("WCAG 2.1 AAA", "Highest accessibility standard", AccessibilityLevel.WCAG_AAA)
        ]
        
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Option", style="cyan", width=15)
        table.add_column("Description", style="white")
        
        for i, (name, desc, _) in enumerate(levels, 1):
            table.add_row(f"{i}. {name}", desc)
        
        console.print(table)
        
        choice = IntPrompt.ask(
            "Choose accessibility level",
            choices=[str(i) for i in range(1, len(levels) + 1)],
            default="1"
        )
        
        return levels[choice - 1][2]
    
    def _get_crawl_configuration(self) -> Dict[str, Any]:
        """Get crawl configuration preferences."""
        console.print("\n[bold cyan]Step 4: Crawl Configuration[/bold cyan]")
        
        max_depth = IntPrompt.ask(
            "Maximum crawl depth (how many clicks deep)",
            default=2,
            choices=[str(i) for i in range(1, 6)]
        )
        
        max_pages = IntPrompt.ask(
            "Maximum pages to analyze",
            default=50
        )
        
        include_assets = Confirm.ask(
            "Download and analyze assets (images, CSS, JS)?",
            default=True
        )
        
        browser_engines = ["chromium", "firefox", "webkit"]
        console.print("\nBrowser engines:")
        for i, engine in enumerate(browser_engines, 1):
            console.print(f"  {i}. {engine.title()}")
        
        browser_choice = IntPrompt.ask(
            "Choose browser engine for dynamic content",
            choices=[str(i) for i in range(1, len(browser_engines) + 1)],
            default="1"
        )
        
        browser = browser_engines[browser_choice - 1]
        
        return {
            'max_depth': max_depth,
            'max_pages': max_pages,
            'include_assets': include_assets,
            'browser_engine': browser,
            'respect_robots_txt': True,
            'rate_limit_delay': 1.0,
            'concurrent_requests': 5,
            'timeout': 30
        }
    
    def _get_output_preferences(self, output_dir: Optional[Path]) -> Dict[str, Any]:
        """Get output configuration preferences."""
        console.print("\n[bold cyan]Step 5: Output Configuration[/bold cyan]")
        
        if output_dir:
            console.print(f"Default output directory: {output_dir}")
            use_default = Confirm.ask("Use this output directory?", default=True)
            if not use_default:
                output_dir = Path(Prompt.ask("Enter output directory path"))
        else:
            output_dir = Path(Prompt.ask("Enter output directory path", default="./analysis"))
        
        generate_markdown = Confirm.ask(
            "Generate human-readable Markdown documentation?",
            default=True
        )
        
        include_screenshots = Confirm.ask(
            "Include page screenshots in analysis?",
            default=False
        )
        
        return {
            'output_directory': output_dir,
            'generate_markdown': generate_markdown,
            'include_screenshots': include_screenshots
        }
    
    def _get_analysis_scope(self) -> Dict[str, Any]:
        """Get analysis scope preferences."""
        console.print("\n[bold cyan]Step 6: Analysis Scope[/bold cyan]")
        console.print("Which analysis modules would you like to enable?")
        
        modules = [
            ("Content Analysis", "Extract and analyze text content and structure", "content"),
            ("Design Analysis", "Analyze colors, typography, and visual design", "design"),
            ("Component Analysis", "Identify and specify UI components", "components"),
            ("Performance Analysis", "Analyze loading performance and metrics", "performance"),
            ("SEO Analysis", "Analyze SEO metadata and structure", "seo"),
            ("Accessibility Analysis", "Check accessibility compliance", "accessibility")
        ]
        
        enabled_modules = []
        
        for name, description, key in modules:
            console.print(f"\n[bold]{name}[/bold]: {description}")
            if Confirm.ask(f"Enable {name}?", default=True):
                enabled_modules.append(key)
        
        return {
            'enabled_modules': enabled_modules,
            'deep_analysis': Confirm.ask(
                "\nEnable deep analysis (slower but more comprehensive)?",
                default=False
            )
        }
    
    def _show_configuration_summary(self, url: str, philosophy: AnalysisPhilosophy, 
                                   framework: TargetFramework, accessibility: AccessibilityLevel,
                                   crawl_config: Dict, output_config: Dict, 
                                   analysis_scope: Dict) -> bool:
        """Show configuration summary and get final confirmation."""
        console.print("\n" + "="*60)
        console.print("[bold cyan]Configuration Summary[/bold cyan]")
        console.print("="*60)
        
        # Create summary table
        table = Table(show_header=False, box=None, padding=(0, 2))
        table.add_column("Setting", style="bold cyan", width=25)
        table.add_column("Value", style="white")
        
        table.add_row("Target URL", url)
        table.add_row("Analysis Philosophy", philosophy.value.replace('_', ' ').title())
        table.add_row("Target Framework", framework.value.replace('_', ' ').title())
        table.add_row("Accessibility Level", accessibility.value.upper())
        table.add_row("", "")
        table.add_row("Max Crawl Depth", str(crawl_config['max_depth']))
        table.add_row("Max Pages", str(crawl_config['max_pages']))
        table.add_row("Include Assets", "Yes" if crawl_config['include_assets'] else "No")
        table.add_row("Browser Engine", crawl_config['browser_engine'].title())
        table.add_row("", "")
        table.add_row("Output Directory", str(output_config['output_directory']))
        table.add_row("Generate Markdown", "Yes" if output_config['generate_markdown'] else "No")
        table.add_row("Include Screenshots", "Yes" if output_config['include_screenshots'] else "No")
        table.add_row("", "")
        table.add_row("Analysis Modules", ", ".join(analysis_scope['enabled_modules']))
        table.add_row("Deep Analysis", "Yes" if analysis_scope['deep_analysis'] else "No")
        
        console.print(table)
        
        console.print("\n[yellow]Review the configuration above.[/yellow]")
        return Confirm.ask("\nProceed with analysis?", default=True)
    
    def show_progress_updates(self, current_step: str, progress: Dict[str, Any]):
        """Show progress updates during analysis."""
        console.print(f"\n[bold blue]Current Step:[/bold blue] {current_step}")
        
        if 'pages_discovered' in progress:
            console.print(f"[dim]Pages discovered: {progress['pages_discovered']}[/dim]")
        
        if 'pages_analyzed' in progress:
            console.print(f"[dim]Pages analyzed: {progress['pages_analyzed']}[/dim]")
        
        if 'errors' in progress and progress['errors']:
            console.print(f"[yellow]Warnings/Errors: {len(progress['errors'])}[/yellow]")
    
    def show_completion_summary(self, results: Dict[str, Any]):
        """Show analysis completion summary."""
        console.print("\n" + "="*60)
        console.print("[bold green]Analysis Complete![/bold green]")
        console.print("="*60)
        
        # Results summary
        table = Table(show_header=True, header_style="bold green")
        table.add_column("Metric", style="cyan")
        table.add_column("Count", style="white", justify="right")
        
        table.add_row("Pages Analyzed", str(results.get('pages_analyzed', 0)))
        table.add_row("Components Found", str(results.get('components_found', 0)))
        table.add_row("Colors Extracted", str(results.get('colors_found', 0)))
        table.add_row("Fonts Identified", str(results.get('fonts_found', 0)))
        table.add_row("Assets Downloaded", str(results.get('assets_downloaded', 0)))
        
        console.print(table)
        
        if 'output_files' in results:
            console.print(f"\n[bold]Output files created:[/bold]")
            for file_type, file_path in results['output_files'].items():
                console.print(f"  [cyan]{file_type}:[/cyan] {file_path}")
        
        console.print(f"\n[green]Analysis results saved to: {results.get('output_directory', 'unknown')}[/green]")


def run_interactive_mode(url: str, output_dir: Optional[Path] = None) -> Dict[str, Any]:
    """Entry point for interactive CLI mode."""
    interactive = InteractiveCLI()
    return interactive.run_interactive_analysis(url, output_dir)