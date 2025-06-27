#!/usr/bin/env python3
"""Advanced API usage examples for GetSiteDNA."""

import asyncio
import json
from pathlib import Path
from typing import List, Dict, Any

from getsitedna.core.analyzer import SiteAnalyzer, analyze_website
from getsitedna.models.schemas import (
    CrawlConfig, AnalysisMetadata, AnalysisPhilosophy, 
    TargetFramework, AccessibilityLevel
)
from getsitedna.models.site import Site
from getsitedna.cli.interactive import InteractiveCLI
from getsitedna.utils.cache import file_cache, memory_cache
from getsitedna.utils.performance import ConcurrentProcessor, performance_context


class AdvancedAnalysisExamples:
    """Advanced examples for GetSiteDNA API usage."""
    
    def __init__(self):
        self.analyzer = SiteAnalyzer(
            use_dynamic_crawler=True,
            generate_markdown=True,
            download_assets=False
        )
    
    async def custom_analyzer_example(self):
        """Example using custom SiteAnalyzer configuration."""
        print("🔧 Custom Analyzer Example")
        print("-" * 30)
        
        # Create analyzer with custom settings
        analyzer = SiteAnalyzer(
            output_directory=Path("./custom_analysis"),
            use_dynamic_crawler=True,
            generate_markdown=True,
            download_assets=True
        )
        
        # Create comprehensive configuration
        config = CrawlConfig(
            max_depth=3,
            max_pages=50,
            rate_limit_delay=1.0,
            timeout=30,
            respect_robots_txt=True,
            max_concurrent_requests=4
        )
        
        metadata = AnalysisMetadata(
            analysis_philosophy=AnalysisPhilosophy.COMPREHENSIVE,
            target_framework=TargetFramework.NEXT_JS_TAILWIND,
            accessibility_level=AccessibilityLevel.AA,
            include_content_analysis=True,
            include_design_analysis=True,
            include_structure_analysis=True,
            include_seo_analysis=True,
            include_performance_analysis=True,
            include_accessibility_analysis=True
        )
        
        # Perform analysis
        site = await analyzer.analyze_site(
            url="https://example.com",
            config=config,
            metadata=metadata
        )
        
        # Get analysis summary
        summary = analyzer.get_analysis_summary()
        
        print(f"✅ Analysis completed!")
        print(f"📊 Pages analyzed: {len(site.pages)}")
        print(f"🎯 Quality score: {summary['analysis_quality']:.2%}")
        print(f"⚠️  Total errors: {summary['error_statistics']['total_errors']}")
        
        return site, summary
    
    async def batch_processing_example(self):
        """Example of processing multiple sites efficiently."""
        print("\n📦 Batch Processing Example")
        print("-" * 30)
        
        urls = [
            "https://example.com",
            "https://httpbin.org",
            "https://jsonplaceholder.typicode.com"
        ]
        
        # Create concurrent processor
        processor = ConcurrentProcessor(max_workers=3)
        
        async def analyze_single_site(url: str) -> Dict[str, Any]:
            """Analyze a single site and return summary."""
            try:
                config = {
                    "crawl_config": CrawlConfig(max_depth=1, max_pages=5),
                    "use_dynamic_crawler": False  # Faster for batch
                }
                
                site = await analyze_website(url, config=config)
                
                return {
                    "url": url,
                    "success": True,
                    "pages": len(site.pages),
                    "colors": len(site.global_color_palette),
                    "components": len(site.component_specifications),
                    "errors": len(site.errors)
                }
                
            except Exception as e:
                return {
                    "url": url,
                    "success": False,
                    "error": str(e)
                }
        
        # Process all URLs concurrently
        results = await processor.process_batch(
            urls,
            analyze_single_site,
            batch_size=2
        )
        
        # Print results
        for result in results:
            if result and result["success"]:
                print(f"✅ {result['url']}: {result['pages']} pages, {result['colors']} colors")
            elif result:
                print(f"❌ {result['url']}: {result['error']}")
        
        return results
    
    async def caching_example(self):
        """Example demonstrating caching functionality."""
        print("\n💾 Caching Example")
        print("-" * 30)
        
        # Clear cache to start fresh
        await file_cache.clear()
        memory_cache.clear()
        
        url = "https://httpbin.org"
        
        # First analysis (cache miss)
        print("🔍 First analysis (should cache results)...")
        start_time = asyncio.get_event_loop().time()
        
        site1 = await analyze_website(url, config={
            "crawl_config": CrawlConfig(max_depth=1, max_pages=3)
        })
        
        first_duration = asyncio.get_event_loop().time() - start_time
        
        # Second analysis (cache hit)
        print("🔍 Second analysis (should use cache)...")
        start_time = asyncio.get_event_loop().time()
        
        site2 = await analyze_website(url, config={
            "crawl_config": CrawlConfig(max_depth=1, max_pages=3)
        })
        
        second_duration = asyncio.get_event_loop().time() - start_time
        
        # Show cache statistics
        cache_stats = file_cache.get_stats()
        
        print(f"⏱️  First analysis: {first_duration:.2f}s")
        print(f"⏱️  Second analysis: {second_duration:.2f}s")
        print(f"📈 Cache hit rate: {cache_stats['hit_rate']:.1%}")
        print(f"💾 Cache size: {cache_stats['cache_size'] // 1024}KB")
        
        return site1, site2, cache_stats
    
    async def performance_monitoring_example(self):
        """Example with performance monitoring."""
        print("\n📊 Performance Monitoring Example")
        print("-" * 30)
        
        async with performance_context(enable_monitoring=True) as ctx:
            # Perform analysis within performance context
            site = await analyze_website("https://example.com", config={
                "crawl_config": CrawlConfig(max_depth=2, max_pages=10)
            })
            
            # Access performance metrics
            if ctx['monitor']:
                metrics = ctx['monitor'].stop_monitoring()
                print(f"⏱️  Execution time: {metrics.execution_time:.2f}s")
                print(f"💾 Memory usage: {metrics.memory_usage:.2f}MB")
                print(f"🖥️  CPU usage: {metrics.cpu_usage:.1f}%")
                print(f"🔄 Concurrent tasks: {metrics.concurrent_tasks}")
        
        return site
    
    async def interactive_api_example(self):
        """Example using interactive CLI programmatically."""
        print("\n🤖 Interactive API Example")
        print("-" * 30)
        
        # Create interactive CLI instance
        interactive = InteractiveCLI()
        
        # You would typically call run_interactive_analysis for full interaction
        # Here we'll demonstrate programmatic configuration
        
        config = {
            "url": "https://example.com",
            "philosophy": AnalysisPhilosophy.DESIGN_FOCUSED,
            "framework": TargetFramework.REACT_STYLED_COMPONENTS,
            "accessibility_level": AccessibilityLevel.AAA,
            "crawl_config": CrawlConfig(
                max_depth=2,
                max_pages=15
            ),
            "include_assets": False,
            "generate_markdown": True,
            "analysis_features": {
                "content_analysis": True,
                "design_analysis": True,
                "structure_analysis": True,
                "seo_analysis": False,
                "performance_analysis": False,
                "accessibility_analysis": True
            }
        }
        
        # Show configuration summary
        interactive.show_progress_updates("Configuration created", {
            "url": config["url"],
            "philosophy": config["philosophy"].value,
            "framework": config["framework"].value
        })
        
        return config
    
    async def custom_output_example(self):
        """Example of custom output processing."""
        print("\n📄 Custom Output Example")
        print("-" * 30)
        
        # Perform analysis
        site = await analyze_website("https://example.com", config={
            "crawl_config": CrawlConfig(max_depth=1, max_pages=5)
        })
        
        # Create custom output data
        custom_data = {
            "analysis_summary": {
                "url": str(site.base_url),
                "domain": site.domain,
                "total_pages": len(site.pages),
                "analysis_date": site.analysis_metadata.analysis_date.isoformat(),
                "target_framework": site.metadata.target_framework.value
            },
            "design_tokens": {
                "colors": [
                    {
                        "hex": color.hex,
                        "name": color.name or f"color-{i}",
                        "usage": color.usage_context
                    }
                    for i, color in enumerate(site.global_color_palette[:10])
                ],
                "typography": [
                    {
                        "family": font.family,
                        "weight": font.weight,
                        "size": font.size,
                        "usage": font.usage_context
                    }
                    for font in site.global_typography[:5]
                ]
            },
            "components": [
                {
                    "name": comp.component_name,
                    "type": comp.component_type.value,
                    "props": comp.props,
                    "implementation": comp.implementation_notes
                }
                for comp in site.component_specifications[:5]
            ],
            "recommendations": [
                f"Consider using {site.metadata.target_framework.value} for implementation",
                f"Implement {len(site.component_specifications)} reusable components",
                f"Use the extracted {len(site.global_color_palette)} color palette"
            ]
        }
        
        # Save custom output
        output_path = Path("./custom_output.json")
        with open(output_path, 'w') as f:
            json.dump(custom_data, f, indent=2, default=str)
        
        print(f"💾 Custom output saved to: {output_path}")
        print(f"🎨 Extracted {len(custom_data['design_tokens']['colors'])} colors")
        print(f"🔤 Found {len(custom_data['design_tokens']['typography'])} fonts")
        print(f"🧩 Identified {len(custom_data['components'])} components")
        
        return custom_data
    
    async def error_handling_example(self):
        """Example demonstrating error handling."""
        print("\n🚨 Error Handling Example")
        print("-" * 30)
        
        from getsitedna.utils.error_handling import (
            ErrorHandler, SafeExecutor, AnalysisError
        )
        
        # Create error handler
        error_handler = ErrorHandler("ExampleAnalysis")
        safe_executor = SafeExecutor(error_handler)
        
        async def risky_analysis(url: str) -> Site:
            """Analysis that might fail."""
            if "invalid" in url:
                raise AnalysisError("Invalid URL provided")
            
            return await analyze_website(url, config={
                "crawl_config": CrawlConfig(max_depth=1, max_pages=2)
            })
        
        # Test with valid URL
        site = await safe_executor.safe_execute(
            risky_analysis,
            "https://httpbin.org",
            error_context={"operation": "valid_analysis"},
            default_return=None
        )
        
        if site:
            print(f"✅ Successful analysis: {len(site.pages)} pages")
        
        # Test with invalid URL
        failed_site = await safe_executor.safe_execute(
            risky_analysis,
            "https://invalid.example.com",
            error_context={"operation": "invalid_analysis"},
            default_return=None
        )
        
        print(f"❌ Failed analysis returned: {failed_site}")
        
        # Get error statistics
        error_stats = error_handler.get_error_summary()
        print(f"📊 Total errors encountered: {error_stats['total_errors']}")
        
        return error_stats


async def run_all_examples():
    """Run all advanced API examples."""
    print("🚀 GetSiteDNA Advanced API Examples")
    print("=" * 50)
    
    examples = AdvancedAnalysisExamples()
    
    try:
        # Run all examples
        await examples.custom_analyzer_example()
        await examples.batch_processing_example()
        await examples.caching_example()
        await examples.performance_monitoring_example()
        await examples.interactive_api_example()
        await examples.custom_output_example()
        await examples.error_handling_example()
        
        print("\n✨ All advanced examples completed successfully!")
        
    except Exception as e:
        print(f"❌ Example failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Run all advanced examples
    asyncio.run(run_all_examples())