"""CLI commands for performance management and optimization."""

import click
import json
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from ...utils.config import config_manager, OptimizationSettings, CacheConfig, PerformanceConfig
from ...utils.cache import file_cache, memory_cache
from ...utils.performance import global_processor, global_optimizer


console = Console()


@click.group()
def performance():
    """Performance optimization and cache management commands."""
    pass


@performance.command()
def status():
    """Show current performance settings and cache status."""
    config = config_manager.load_config()
    
    # Performance settings table
    perf_table = Table(title="Performance Settings")
    perf_table.add_column("Setting", style="cyan")
    perf_table.add_column("Value", style="magenta")
    
    perf_table.add_row("Caching Enabled", str(config.enable_caching))
    perf_table.add_row("Concurrent Processing", str(config.enable_concurrent_processing))
    perf_table.add_row("Performance Monitoring", str(config.enable_performance_monitoring))
    perf_table.add_row("Max Concurrent Requests", str(config.performance.max_concurrent_requests))
    perf_table.add_row("Batch Size", str(config.performance.batch_size))
    perf_table.add_row("Memory Threshold", f"{config.performance.memory_threshold}%")
    perf_table.add_row("CPU Threshold", f"{config.performance.cpu_threshold}%")
    
    console.print(perf_table)
    console.print()
    
    # Cache settings table
    cache_table = Table(title="Cache Settings")
    cache_table.add_column("Setting", style="cyan")
    cache_table.add_column("Value", style="magenta")
    
    cache_table.add_row("Cache Enabled", str(config.cache.enabled))
    cache_table.add_row("Cache Directory", config.cache.cache_dir)
    cache_table.add_row("Default TTL", f"{config.cache.default_ttl} seconds")
    cache_table.add_row("Max Size", f"{config.cache.max_size // (1024*1024)} MB")
    cache_table.add_row("Memory Cache Enabled", str(config.cache.memory_cache_enabled))
    cache_table.add_row("Memory Cache Max Size", str(config.cache.memory_cache_max_size))
    
    console.print(cache_table)
    console.print()
    
    # Cache statistics
    try:
        cache_stats = file_cache.get_stats()
        
        stats_table = Table(title="Cache Statistics")
        stats_table.add_column("Metric", style="cyan")
        stats_table.add_column("Value", style="magenta")
        
        stats_table.add_row("Cache Hits", str(cache_stats["hits"]))
        stats_table.add_row("Cache Misses", str(cache_stats["misses"]))
        stats_table.add_row("Hit Rate", f"{cache_stats['hit_rate']:.2%}")
        stats_table.add_row("Cache Size", f"{cache_stats['cache_size'] // 1024} KB")
        stats_table.add_row("Cache Files", str(cache_stats["cache_files"]))
        
        console.print(stats_table)
        
    except Exception as e:
        console.print(f"[red]Could not retrieve cache statistics: {e}[/red]")
    
    # Resource information
    try:
        resource_info = global_optimizer.get_resource_info()
        
        resource_table = Table(title="System Resources")
        resource_table.add_column("Resource", style="cyan")
        resource_table.add_column("Value", style="magenta")
        
        resource_table.add_row("Memory Used", f"{resource_info['memory']['used']:.1f} GB")
        resource_table.add_row("Memory Available", f"{resource_info['memory']['available']:.1f} GB")
        resource_table.add_row("Memory Usage", f"{resource_info['memory']['percent']:.1f}%")
        resource_table.add_row("CPU Usage", f"{resource_info['cpu']['percent']:.1f}%")
        resource_table.add_row("CPU Cores", str(resource_info['cpu']['count']))
        
        console.print()
        console.print(resource_table)
        
    except Exception as e:
        console.print(f"[red]Could not retrieve resource information: {e}[/red]")


@performance.command()
@click.option('--workers', type=int, help='Maximum number of concurrent workers')
@click.option('--batch-size', type=int, help='Batch size for processing')
@click.option('--memory-threshold', type=int, help='Memory usage threshold (percentage)')
@click.option('--cpu-threshold', type=int, help='CPU usage threshold (percentage)')
@click.option('--enable-caching/--disable-caching', default=None, help='Enable or disable caching')
@click.option('--enable-monitoring/--disable-monitoring', default=None, help='Enable or disable monitoring')
def configure(workers, batch_size, memory_threshold, cpu_threshold, enable_caching, enable_monitoring):
    """Configure performance settings."""
    config = config_manager.load_config()
    
    # Update performance settings
    if workers is not None:
        config.performance.max_concurrent_requests = workers
        console.print(f"[green]Set max concurrent workers to {workers}[/green]")
    
    if batch_size is not None:
        config.performance.batch_size = batch_size
        console.print(f"[green]Set batch size to {batch_size}[/green]")
    
    if memory_threshold is not None:
        config.performance.memory_threshold = memory_threshold
        console.print(f"[green]Set memory threshold to {memory_threshold}%[/green]")
    
    if cpu_threshold is not None:
        config.performance.cpu_threshold = cpu_threshold
        console.print(f"[green]Set CPU threshold to {cpu_threshold}%[/green]")
    
    if enable_caching is not None:
        config.enable_caching = enable_caching
        status = "enabled" if enable_caching else "disabled"
        console.print(f"[green]Caching {status}[/green]")
    
    if enable_monitoring is not None:
        config.enable_performance_monitoring = enable_monitoring
        status = "enabled" if enable_monitoring else "disabled"
        console.print(f"[green]Performance monitoring {status}[/green]")
    
    # Save configuration
    config_manager.save_config(config)
    console.print("[bold green]Configuration saved successfully![/bold green]")


@performance.command()
@click.option('--cache-dir', help='Cache directory path')
@click.option('--ttl', type=int, help='Default cache TTL in seconds')
@click.option('--max-size', type=int, help='Maximum cache size in MB')
@click.option('--memory-cache-size', type=int, help='Memory cache maximum entries')
def cache_config(cache_dir, ttl, max_size, memory_cache_size):
    """Configure cache settings."""
    config = config_manager.load_config()
    
    if cache_dir is not None:
        config.cache.cache_dir = cache_dir
        console.print(f"[green]Set cache directory to {cache_dir}[/green]")
    
    if ttl is not None:
        config.cache.default_ttl = ttl
        console.print(f"[green]Set default TTL to {ttl} seconds[/green]")
    
    if max_size is not None:
        config.cache.max_size = max_size * 1024 * 1024  # Convert MB to bytes
        console.print(f"[green]Set max cache size to {max_size} MB[/green]")
    
    if memory_cache_size is not None:
        config.cache.memory_cache_max_size = memory_cache_size
        console.print(f"[green]Set memory cache max size to {memory_cache_size} entries[/green]")
    
    # Save configuration
    config_manager.save_config(config)
    console.print("[bold green]Cache configuration saved successfully![/bold green]")


@performance.command()
@click.confirmation_option(prompt='Are you sure you want to clear all caches?')
def clear_cache():
    """Clear all cached data."""
    try:
        # Clear file cache
        file_cache_cleared = False
        try:
            import asyncio
            asyncio.run(file_cache.clear())
            file_cache_cleared = True
        except Exception as e:
            console.print(f"[yellow]Warning: Could not clear file cache: {e}[/yellow]")
        
        # Clear memory cache
        memory_cache.clear()
        
        if file_cache_cleared:
            console.print("[green]All caches cleared successfully![/green]")
        else:
            console.print("[yellow]Memory cache cleared, but file cache could not be cleared[/yellow]")
        
    except Exception as e:
        console.print(f"[red]Error clearing caches: {e}[/red]")


@performance.command()
def reset():
    """Reset performance settings to defaults."""
    config_manager.reset_to_defaults()
    console.print("[green]Performance settings reset to defaults![/green]")


@performance.command()
@click.option('--output', '-o', type=click.Path(), help='Output file for configuration')
def export_config(output):
    """Export current configuration to a file."""
    config = config_manager.load_config()
    
    config_data = {
        'cache': {
            'enabled': config.cache.enabled,
            'cache_dir': config.cache.cache_dir,
            'default_ttl': config.cache.default_ttl,
            'max_size': config.cache.max_size,
            'cleanup_interval': config.cache.cleanup_interval,
            'memory_cache_enabled': config.cache.memory_cache_enabled,
            'memory_cache_max_size': config.cache.memory_cache_max_size,
            'memory_cache_ttl': config.cache.memory_cache_ttl
        },
        'performance': {
            'max_concurrent_requests': config.performance.max_concurrent_requests,
            'max_concurrent_extractions': config.performance.max_concurrent_extractions,
            'use_process_pool': config.performance.use_process_pool,
            'enable_monitoring': config.performance.enable_monitoring,
            'memory_threshold': config.performance.memory_threshold,
            'cpu_threshold': config.performance.cpu_threshold,
            'batch_size': config.performance.batch_size,
            'adaptive_batching': config.performance.adaptive_batching,
            'enable_gc_optimization': config.performance.enable_gc_optimization,
            'enable_adaptive_delays': config.performance.enable_adaptive_delays
        },
        'enable_caching': config.enable_caching,
        'enable_concurrent_processing': config.enable_concurrent_processing,
        'enable_performance_monitoring': config.enable_performance_monitoring,
        'debug_mode': config.debug_mode,
        'log_performance_metrics': config.log_performance_metrics
    }
    
    output_path = Path(output) if output else Path('getsitedna-config.json')
    
    with open(output_path, 'w') as f:
        json.dump(config_data, f, indent=2)
    
    console.print(f"[green]Configuration exported to {output_path}[/green]")


@performance.command()
@click.argument('config_file', type=click.Path(exists=True))
def import_config(config_file):
    """Import configuration from a file."""
    try:
        with open(config_file, 'r') as f:
            config_data = json.load(f)
        
        # Create new configuration
        cache_config = CacheConfig(**config_data.get('cache', {}))
        perf_config = PerformanceConfig(**config_data.get('performance', {}))
        
        settings = OptimizationSettings(
            cache=cache_config,
            performance=perf_config,
            enable_caching=config_data.get('enable_caching', True),
            enable_concurrent_processing=config_data.get('enable_concurrent_processing', True),
            enable_performance_monitoring=config_data.get('enable_performance_monitoring', True),
            debug_mode=config_data.get('debug_mode', False),
            log_performance_metrics=config_data.get('log_performance_metrics', False)
        )
        
        config_manager.save_config(settings)
        console.print(f"[green]Configuration imported from {config_file}[/green]")
        
    except Exception as e:
        console.print(f"[red]Error importing configuration: {e}[/red]")


@performance.command()
def benchmark():
    """Run a simple performance benchmark."""
    import time
    import asyncio
    from ...utils.performance import performance_context
    
    console.print("[blue]Running performance benchmark...[/blue]")
    
    async def test_operation():
        """Simple test operation for benchmarking."""
        await asyncio.sleep(0.01)  # Simulate work
        return "test"
    
    async def run_benchmark():
        async with performance_context() as ctx:
            start_time = time.time()
            
            # Run test operations
            tasks = [test_operation() for _ in range(100)]
            results = await asyncio.gather(*tasks)
            
            end_time = time.time()
            
            console.print(f"[green]Benchmark completed in {end_time - start_time:.2f} seconds[/green]")
            console.print(f"[green]Processed {len(results)} operations[/green]")
            
            if ctx['monitor']:
                metrics = ctx['monitor'].stop_monitoring()
                console.print(f"[cyan]Memory usage: {metrics.memory_usage:.2f} MB[/cyan]")
                console.print(f"[cyan]CPU usage: {metrics.cpu_usage:.1f}%[/cyan]")
    
    asyncio.run(run_benchmark())