#!/usr/bin/env python3
"""Basic usage examples for GetSiteDNA."""

import asyncio
from pathlib import Path

from getsitedna.core.analyzer import analyze_website
from getsitedna.models.schemas import CrawlConfig, AnalysisMetadata


async def basic_analysis():
    """Simple website analysis with default settings."""
    print("🔍 Basic Analysis Example")
    print("=" * 50)
    
    # Analyze a website with default settings
    site = await analyze_website("https://example.com")
    
    # Print basic statistics
    print(f"✅ Analysis complete!")
    print(f"📊 Pages analyzed: {len(site.pages)}")
    print(f"🎨 Colors found: {len(site.global_color_palette)}")
    print(f"🔤 Fonts found: {len(site.global_typography)}")
    print(f"🧩 Components found: {len(site.component_specifications)}")
    
    return site


async def advanced_analysis():
    """Advanced analysis with custom configuration."""
    print("\n🚀 Advanced Analysis Example")
    print("=" * 50)
    
    # Create custom configuration
    config = {
        "crawl_config": CrawlConfig(
            max_depth=3,
            max_pages=25,
            respect_robots_txt=True,
            rate_limit_delay=1.0,
            timeout=30
        ),
        "metadata": AnalysisMetadata(
            analysis_philosophy="comprehensive",
            target_framework="next_js_tailwind",
            accessibility_level="AA"
        ),
        "use_dynamic_crawler": True,
        "download_assets": True,
        "generate_markdown": True
    }
    
    # Run analysis with custom config
    site = await analyze_website(
        "https://example.com",
        config=config,
        output_dir=Path("./example_analysis")
    )
    
    # Print detailed results
    print(f"✅ Advanced analysis complete!")
    print(f"📂 Output directory: ./example_analysis")
    print(f"🌐 Base URL: {site.base_url}")
    print(f"📊 Statistics:")
    print(f"   • Pages: {len(site.pages)}")
    print(f"   • Errors: {len(site.errors)}")
    print(f"   • Warnings: {len(site.warnings)}")
    
    # Show color palette
    if site.global_color_palette:
        print(f"\n🎨 Color Palette:")
        for color in site.global_color_palette[:5]:  # Show first 5 colors
            print(f"   • {color.hex} ({color.usage_context})")
    
    # Show typography
    if site.global_typography:
        print(f"\n🔤 Typography:")
        for font in site.global_typography[:3]:  # Show first 3 fonts
            print(f"   • {font.family} - {font.weight}")
    
    return site


async def analyze_specific_aspects():
    """Focus on specific analysis aspects."""
    print("\n🎯 Focused Analysis Example")
    print("=" * 50)
    
    # Configuration focused on design analysis
    config = {
        "crawl_config": CrawlConfig(
            max_depth=2,
            max_pages=10
        ),
        "metadata": AnalysisMetadata(
            analysis_philosophy="design_focused",
            target_framework="react_styled_components"
        ),
        "use_dynamic_crawler": False,  # Faster for design analysis
        "download_assets": False
    }
    
    site = await analyze_website("https://example.com", config=config)
    
    # Analyze design system
    print("🎨 Design System Analysis:")
    
    # Color analysis
    primary_colors = [c for c in site.global_color_palette if "primary" in c.usage_context]
    if primary_colors:
        print(f"   Primary colors: {[c.hex for c in primary_colors]}")
    
    # Typography analysis
    headings = [f for f in site.global_typography if "heading" in f.usage_context]
    if headings:
        print(f"   Heading fonts: {[f.family for f in headings]}")
    
    # Component analysis
    buttons = [c for c in site.component_specifications if c.component_type.value == "button"]
    print(f"   Button components: {len(buttons)}")
    
    return site


async def batch_analysis():
    """Analyze multiple websites in batch."""
    print("\n📦 Batch Analysis Example")
    print("=" * 50)
    
    urls = [
        "https://example.com",
        "https://httpbin.org",
        # Add more URLs as needed
    ]
    
    results = []
    
    for i, url in enumerate(urls, 1):
        print(f"🔍 Analyzing {i}/{len(urls)}: {url}")
        
        try:
            config = {
                "crawl_config": CrawlConfig(max_depth=1, max_pages=5),
                "use_dynamic_crawler": False  # Faster for batch analysis
            }
            
            site = await analyze_website(url, config=config)
            results.append({
                "url": url,
                "pages": len(site.pages),
                "colors": len(site.global_color_palette),
                "components": len(site.component_specifications),
                "success": True
            })
            
        except Exception as e:
            print(f"❌ Failed to analyze {url}: {e}")
            results.append({
                "url": url,
                "success": False,
                "error": str(e)
            })
    
    # Print batch results
    print(f"\n📊 Batch Analysis Results:")
    for result in results:
        if result["success"]:
            print(f"✅ {result['url']}: {result['pages']} pages, {result['colors']} colors")
        else:
            print(f"❌ {result['url']}: {result['error']}")
    
    return results


async def main():
    """Run all examples."""
    print("🚀 GetSiteDNA Usage Examples")
    print("=" * 60)
    
    try:
        # Run basic analysis
        await basic_analysis()
        
        # Run advanced analysis
        await advanced_analysis()
        
        # Run focused analysis
        await analyze_specific_aspects()
        
        # Run batch analysis
        await batch_analysis()
        
        print("\n✨ All examples completed successfully!")
        
    except Exception as e:
        print(f"❌ Example failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Run the examples
    asyncio.run(main())