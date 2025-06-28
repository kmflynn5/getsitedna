"""Main analyzer orchestrating the entire analysis process."""

import asyncio
import time
from pathlib import Path
from typing import Dict, List, Optional, Any

from ..models.site import Site, CrawlConfig
from ..models.page import Page
from ..models.schemas import AnalysisMetadata
from ..crawlers.static_crawler import StaticCrawler
from ..crawlers.dynamic_crawler import DynamicCrawler
from ..extractors.content import ContentExtractor
from ..extractors.structure import StructureExtractor
from ..extractors.design import DesignExtractor
from ..extractors.assets import AssetExtractor
from ..extractors.api_discovery import discover_site_apis
from ..processors.pattern_recognition import recognize_site_patterns
from ..outputs.json_writer import JSONWriter
from ..outputs.markdown_writer import MarkdownWriter
from ..utils.error_handling import (
    ErrorHandler, SafeExecutor, retry_on_error, RetryConfig,
    AnalysisError, ErrorSeverity, ErrorCategory
)
from ..utils.cache import file_cache
from ..utils.performance import ConcurrentProcessor, performance_context, PerformanceMonitor


class SiteAnalyzer:
    """Main orchestrator for complete website analysis."""
    
    def __init__(self, 
                 output_directory: Optional[Path] = None,
                 use_dynamic_crawler: bool = True,
                 generate_markdown: bool = True,
                 download_assets: bool = False):
        self.output_directory = output_directory
        self.use_dynamic_crawler = use_dynamic_crawler
        self.generate_markdown = generate_markdown
        self.download_assets = download_assets
        
        # Error handling
        self.error_handler = ErrorHandler("getsitedna.analyzer")
        self.safe_executor = SafeExecutor(self.error_handler)
        
        # Analysis modules
        self.content_extractor = ContentExtractor()
        self.structure_extractor = StructureExtractor()
        self.design_extractor = DesignExtractor()
        
        # Performance optimization
        self.processor = ConcurrentProcessor(max_workers=4)
        self.performance_monitor = PerformanceMonitor()
        
        # Retry configuration
        self.retry_config = RetryConfig(
            max_attempts=3,
            base_delay=2.0,
            max_delay=30.0
        )
    
    async def analyze_site(self, 
                          url: str, 
                          config: Optional[CrawlConfig] = None,
                          metadata: Optional[AnalysisMetadata] = None) -> Site:
        """Perform complete site analysis with performance optimization."""
        async with performance_context(enable_monitoring=True) as ctx:
            start_time = time.time()
            
            try:
                # Initialize site
                site = self._initialize_site(url, config, metadata)
                
                self.error_handler.logger.info(f"Starting analysis of {url}")
                
                # Phase 1: Crawling
                site = await self._crawl_site(site)
                
                # Phase 2: Parallel Content and Design Analysis
                site = await self._analyze_content_and_design_parallel(site)
                
                # Phase 4: Pattern Recognition
                site = await self._recognize_patterns(site)
                
                # Phase 5: Asset Processing
                if self.download_assets:
                    site = await self._process_assets(site)
                
                # Phase 6: API Discovery
                site = await self._discover_apis(site)
                
                # Finalize analysis (update statistics before output generation)
                site.mark_analysis_complete()
                
                # Calculate validation scores
                self._calculate_validation_scores(site)
                
                # Phase 7: Generate Outputs
                await self._generate_outputs(site)
                
                analysis_time = time.time() - start_time
                self.error_handler.logger.info(
                    f"Analysis completed in {analysis_time:.2f}s. "
                    f"Pages: {site.stats.total_pages_analyzed}, "
                    f"Errors: {self.error_handler.error_stats['total_errors']}"
                )
                
                return site
                
            except Exception as e:
                analysis_error = self.error_handler.handle_error(
                    e, {"url": url, "phase": "unknown"}
                )
                
                if analysis_error.severity == ErrorSeverity.CRITICAL:
                    raise analysis_error
                
                # Return partial results if possible
                if 'site' in locals():
                    site.add_error(f"Analysis incomplete due to error: {analysis_error.message}")
                    return site
                else:
                    raise analysis_error
    
    def _initialize_site(self, 
                        url: str, 
                        config: Optional[CrawlConfig],
                        metadata: Optional[AnalysisMetadata]) -> Site:
        """Initialize site object with configuration."""
        site = Site(base_url=url)
        
        if config:
            site.config = config
        
        if metadata:
            site.metadata = metadata
        
        if self.output_directory:
            site.output_directory = self.output_directory
        
        return site
    
    @retry_on_error(exceptions=(AnalysisError,))
    async def _crawl_site(self, site: Site) -> Site:
        """Crawl the website to discover and analyze pages."""
        self.error_handler.logger.info("Phase 1: Crawling website")
        
        try:
            if self.use_dynamic_crawler:
                # Use dynamic crawler for JavaScript-heavy sites
                crawler = DynamicCrawler(site)
                site = await self.safe_executor.safe_execute(
                    crawler.crawl_site,
                    error_context={"phase": "dynamic_crawling", "url": str(site.base_url)},
                    default_return=site
                )
            else:
                # Use static crawler for traditional sites
                crawler = StaticCrawler(site)
                site = await self.safe_executor.safe_execute(
                    crawler.crawl_site,
                    error_context={"phase": "static_crawling", "url": str(site.base_url)},
                    default_return=site
                )
            
            self.error_handler.logger.info(
                f"Crawling completed: {len(site.crawled_pages)} pages successfully crawled"
            )
            
            return site
            
        except Exception as e:
            raise AnalysisError(
                f"Crawling failed: {e}",
                ErrorCategory.NETWORK,
                ErrorSeverity.HIGH,
                {"url": str(site.base_url)}
            )
    
    async def _analyze_content(self, site: Site) -> Site:
        """Analyze content and structure of all crawled pages."""
        self.error_handler.logger.info("Phase 2: Analyzing content and structure")
        
        successful_analyses = 0
        
        for page in site.crawled_pages:
            try:
                # Content extraction
                page = await self.safe_executor.safe_execute(
                    self.content_extractor.extract_content,
                    page,
                    error_context={"phase": "content_extraction", "url": str(page.url)},
                    default_return=page
                )
                
                # Structure extraction
                page = await self.safe_executor.safe_execute(
                    self.structure_extractor.extract_structure,
                    page,
                    error_context={"phase": "structure_extraction", "url": str(page.url)},
                    default_return=page
                )
                
                page.mark_analyzed()
                successful_analyses += 1
                
            except Exception as e:
                page.add_error(f"Content analysis failed: {e}")
                self.error_handler.handle_error(
                    e, {"phase": "content_analysis", "url": str(page.url)}
                )
        
        self.error_handler.logger.info(
            f"Content analysis completed: {successful_analyses}/{len(site.crawled_pages)} pages"
        )
        
        return site
    
    async def _analyze_design(self, site: Site) -> Site:
        """Analyze design elements across all pages."""
        self.error_handler.logger.info("Phase 3: Analyzing design elements")
        
        for page in site.crawled_pages:
            try:
                page = await self.safe_executor.safe_execute(
                    self.design_extractor.extract_design,
                    page,
                    error_context={"phase": "design_extraction", "url": str(page.url)},
                    default_return=page
                )
                
            except Exception as e:
                page.add_warning(f"Design analysis failed: {e}")
                self.error_handler.handle_error(
                    e, {"phase": "design_analysis", "url": str(page.url)}
                )
        
        # Analyze global design system
        try:
            site = await self.safe_executor.safe_execute(
                self.design_extractor.analyze_global_design_system,
                site,
                error_context={"phase": "global_design_analysis"},
                default_return=site
            )
        except Exception as e:
            site.add_warning(f"Global design analysis failed: {e}")
        
        return site
    
    async def _recognize_patterns(self, site: Site) -> Site:
        """Recognize UX patterns and experience flows."""
        self.error_handler.logger.info("Phase 4: Recognizing UX patterns")
        
        try:
            site = await self.safe_executor.safe_execute(
                recognize_site_patterns,
                site,
                error_context={"phase": "pattern_recognition"},
                default_return=site
            )
            
            self.error_handler.logger.info(
                f"Pattern recognition completed: {len(site.experience_patterns)} patterns identified"
            )
            
        except Exception as e:
            site.add_warning(f"Pattern recognition failed: {e}")
            self.error_handler.handle_error(e, {"phase": "pattern_recognition"})
        
        return site
    
    async def _process_assets(self, site: Site) -> Site:
        """Process and analyze assets."""
        self.error_handler.logger.info("Phase 5: Processing assets")
        
        asset_extractor = AssetExtractor(site, download_assets=True)
        
        for page in site.crawled_pages:
            try:
                page = await self.safe_executor.safe_execute(
                    asset_extractor.extract_assets,
                    page,
                    error_context={"phase": "asset_processing", "url": str(page.url)},
                    default_return=page
                )
                
            except Exception as e:
                page.add_warning(f"Asset processing failed: {e}")
                self.error_handler.handle_error(
                    e, {"phase": "asset_processing", "url": str(page.url)}
                )
        
        return site
    
    async def _discover_apis(self, site: Site) -> Site:
        """Discover API endpoints and services."""
        self.error_handler.logger.info("Phase 6: Discovering APIs")
        
        try:
            site = await self.safe_executor.safe_execute(
                discover_site_apis,
                site,
                error_context={"phase": "api_discovery"},
                default_return=site
            )
            
            api_count = len(site.technical_modernization.api_endpoints or [])
            self.error_handler.logger.info(f"API discovery completed: {api_count} endpoints found")
            
        except Exception as e:
            site.add_warning(f"API discovery failed: {e}")
            self.error_handler.handle_error(e, {"phase": "api_discovery"})
        
        return site
    
    async def _generate_outputs(self, site: Site) -> Dict[str, Path]:
        """Generate all output files."""
        self.error_handler.logger.info("Phase 7: Generating outputs")
        
        output_files = {}
        
        if not site.output_directory:
            site.output_directory = Path("./analysis")
        
        # Generate JSON outputs
        try:
            json_writer = JSONWriter(site.output_directory)
            json_files = json_writer.write_site_analysis(site)
            output_files.update(json_files)
            
        except Exception as e:
            site.add_error(f"JSON output generation failed: {e}")
            self.error_handler.handle_error(e, {"phase": "json_output"})
        
        # Generate Markdown documentation
        if self.generate_markdown:
            try:
                markdown_writer = MarkdownWriter(site.output_directory)
                markdown_files = markdown_writer.write_documentation(site)
                output_files.update(markdown_files)
                
            except Exception as e:
                site.add_warning(f"Markdown output generation failed: {e}")
                self.error_handler.handle_error(e, {"phase": "markdown_output"})
        
        self.error_handler.logger.info(f"Output generation completed: {len(output_files)} files created")
        
        return output_files
    
    def get_analysis_summary(self) -> Dict[str, Any]:
        """Get summary of the analysis process."""
        error_stats = self.error_handler.get_error_summary()
        
        return {
            "error_statistics": error_stats,
            "analysis_quality": self._calculate_analysis_quality(error_stats),
            "recommendations": self._generate_analysis_recommendations(error_stats)
        }
    
    def _calculate_analysis_quality(self, error_stats: Dict) -> float:
        """Calculate overall analysis quality score."""
        total_errors = error_stats["total_errors"]
        critical_errors = error_stats["by_severity"].get("critical", 0)
        high_errors = error_stats["by_severity"].get("high", 0)
        
        # Start with perfect score
        quality = 1.0
        
        # Deduct for errors
        quality -= critical_errors * 0.3  # Critical errors are heavily penalized
        quality -= high_errors * 0.1      # High errors moderately penalized
        quality -= total_errors * 0.01    # Small penalty for any error
        
        return max(quality, 0.0)
    
    def _generate_analysis_recommendations(self, error_stats: Dict) -> List[str]:
        """Generate recommendations based on analysis errors."""
        recommendations = []
        
        if error_stats["by_category"].get("network", 0) > 5:
            recommendations.append(
                "Multiple network errors detected. Consider increasing timeout values or checking network connectivity."
            )
        
        if error_stats["by_category"].get("browser", 0) > 3:
            recommendations.append(
                "Browser automation issues detected. Try using static crawler for this site."
            )
        
        if error_stats["by_category"].get("parsing", 0) > 10:
            recommendations.append(
                "Many parsing errors detected. The site may have malformed HTML or use complex JavaScript rendering."
            )
        
        if error_stats["total_errors"] > 50:
            recommendations.append(
                "High error count detected. Consider reducing crawl depth or page count for better reliability."
            )
        
        return recommendations
    
    async def _analyze_content_and_design_parallel(self, site: Site) -> Site:
        """Analyze content and design in parallel for better performance."""
        self.error_handler.logger.info("Phase 2-3: Parallel content and design analysis")
        
        # Process pages in batches for content and design analysis
        pages_to_analyze = list(site.crawled_pages)
        
        async def analyze_page_content_and_design(page: Page) -> Page:
            """Analyze both content and design for a single page."""
            try:
                # Content analysis
                page = await self.safe_executor.safe_execute(
                    self.content_extractor.extract_content,
                    page,
                    error_context={"phase": "content_analysis", "url": str(page.url)},
                    default_return=page
                )
                
                # Design analysis
                page = await self.safe_executor.safe_execute(
                    self.design_extractor.extract_design,
                    page,
                    error_context={"phase": "design_analysis", "url": str(page.url)},
                    default_return=page
                )
                
                # Structure analysis
                page = await self.safe_executor.safe_execute(
                    self.structure_extractor.extract_structure,
                    page,
                    error_context={"phase": "structure_analysis", "url": str(page.url)},
                    default_return=page
                )
                
                # Mark page as analyzed (THIS WAS MISSING!)
                page.mark_analyzed()
                
                return page
                
            except Exception as e:
                page.add_warning(f"Analysis failed: {e}")
                self.error_handler.handle_error(
                    e, {"phase": "parallel_analysis", "url": str(page.url)}
                )
                return page
        
        # Process pages concurrently
        processed_pages = await self.processor.process_batch(
            pages_to_analyze,
            analyze_page_content_and_design,
            batch_size=3,  # Smaller batches for memory efficiency
            progress_callback=lambda completed, total: self.error_handler.logger.info(
                f"Analysis progress: {completed}/{total} pages completed"
            )
        )
        
        # Update site with processed pages
        for page in processed_pages:
            if page:  # Check for None results from failed processing
                site.pages[str(page.url)] = page
        
        # Global design system analysis
        site = await self.safe_executor.safe_execute(
            self.design_extractor.analyze_global_design_system,
            site,
            error_context={"phase": "global_design_analysis"},
            default_return=site
        )
        
        self.error_handler.logger.info(
            f"Parallel analysis completed: {len(processed_pages)} pages analyzed"
        )
        
        return site

    def _calculate_validation_scores(self, site: Site) -> None:
        """Calculate validation scores for the site and pages."""
        # Calculate page validation scores
        for page in site.pages.values():
            if page.is_successful and page.analyzed_at:
                page.validation.completeness_score = self._calculate_page_completeness(page)
                page.validation.quality_metrics = self._calculate_page_quality_metrics(page)
        
        # Calculate site validation score
        if site.pages:
            page_scores = [p.validation.completeness_score for p in site.pages.values() 
                          if p.is_successful and p.analyzed_at]
            site.validation.completeness_score = sum(page_scores) / len(page_scores) if page_scores else 0.0
            site.validation.quality_metrics = self._calculate_site_quality_metrics(site)
    
    def _calculate_page_completeness(self, page: Page) -> float:
        """Calculate completeness score for a single page."""
        score = 0.0
        
        # Content analysis (25%)
        if page.content.text_content:
            score += 0.25
        
        # Structure analysis (25%)
        if page.structure.components:
            score += 0.25
        
        # Design analysis (25%)
        if page.design.color_palette or page.design.typography:
            score += 0.25
        
        # SEO completeness (25%)
        if page.seo.title and page.seo.description:
            score += 0.25
        
        return score
    
    def _calculate_page_quality_metrics(self, page: Page) -> Dict[str, float]:
        """Calculate quality metrics for a page."""
        return {
            "content_length": min(len(page.content.unique_copy or "") / 1000, 1.0),
            "component_count": min(len(page.structure.components) / 10, 1.0),
            "color_variety": min(len(page.design.color_palette) / 5, 1.0),
            "font_variety": min(len(page.design.typography) / 3, 1.0),
            "seo_completeness": 1.0 if (page.seo.title and page.seo.description) else 0.5 if page.seo.title else 0.0,
        }
    
    def _calculate_site_quality_metrics(self, site: Site) -> Dict[str, float]:
        """Calculate quality metrics for the entire site."""
        total_components = sum(len(p.structure.components) for p in site.pages.values() if p.is_successful)
        total_colors = len(site.global_color_palette)
        total_fonts = len(site.global_typography)
        
        return {
            "total_components": min(total_components / 20, 1.0),
            "global_design_consistency": min((total_colors + total_fonts) / 10, 1.0),
            "crawl_success_rate": site.stats.total_pages_crawled / max(site.stats.total_pages_discovered, 1),
            "analysis_success_rate": site.stats.total_pages_analyzed / max(site.stats.total_pages_crawled, 1),
        }


async def analyze_website(url: str, 
                         config: Optional[Dict[str, Any]] = None,
                         output_dir: Optional[Path] = None) -> Site:
    """Main entry point for website analysis."""
    analyzer = SiteAnalyzer(
        output_directory=output_dir,
        use_dynamic_crawler=config.get("use_dynamic_crawler", True) if config else True,
        generate_markdown=config.get("generate_markdown", True) if config else True,
        download_assets=config.get("download_assets", False) if config else False
    )
    
    crawl_config = CrawlConfig(**config.get("crawl_config", {})) if config and "crawl_config" in config else None
    metadata = AnalysisMetadata(**config.get("metadata", {})) if config and "metadata" in config else None
    
    return await analyzer.analyze_site(url, crawl_config, metadata)