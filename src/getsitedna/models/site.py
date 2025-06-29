"""Site data model for website analysis."""

from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Any
from urllib.parse import urlparse

from pydantic import BaseModel, Field, HttpUrl, field_validator

from .schemas import (
    AnalysisMetadata,
    DesignIntent,
    ExperiencePattern,
    ComponentSpec,
    TechnicalModernization,
    ValidationReport,
    ColorInfo,
    FontInfo,
    DesignToken,
)
from .page import Page


class CrawlConfig(BaseModel):
    """Crawling configuration for the site."""
    max_depth: int = Field(default=2, ge=1)
    max_pages: int = Field(default=50, ge=1)
    include_assets: bool = True
    respect_robots_txt: bool = True
    rate_limit_delay: float = Field(default=1.0, ge=0.1)
    concurrent_requests: int = Field(default=5, ge=1, le=20)
    browser_engine: str = "chromium"
    user_agent: Optional[str] = None
    timeout: int = Field(default=30, ge=5)


class SiteStats(BaseModel):
    """Site analysis statistics."""
    total_pages_discovered: int = 0
    total_pages_crawled: int = 0
    total_pages_analyzed: int = 0
    total_assets_found: int = 0
    total_assets_downloaded: int = 0
    total_components_identified: int = 0
    total_patterns_identified: int = 0
    crawl_duration_seconds: Optional[float] = None
    analysis_duration_seconds: Optional[float] = None


class Site(BaseModel):
    """Represents a complete analyzed website."""
    
    # Basic site information
    base_url: HttpUrl
    domain: str = Field(default="")
    
    # Analysis configuration
    config: CrawlConfig = Field(default_factory=CrawlConfig)
    metadata: AnalysisMetadata = Field(default_factory=AnalysisMetadata)
    
    # Timing information
    analysis_started_at: datetime = Field(default_factory=datetime.now)
    analysis_completed_at: Optional[datetime] = None
    
    # Pages and structure
    pages: Dict[str, Page] = Field(default_factory=dict)
    sitemap_urls: List[HttpUrl] = Field(default_factory=list)
    robots_txt_content: Optional[str] = None
    
    # Global analysis results
    design_intent: DesignIntent = Field(default_factory=DesignIntent)
    experience_patterns: List[ExperiencePattern] = Field(default_factory=list)
    component_specifications: List[ComponentSpec] = Field(default_factory=list)
    technical_modernization: TechnicalModernization = Field(default_factory=TechnicalModernization)
    
    # Global design system
    global_color_palette: List[ColorInfo] = Field(default_factory=list)
    global_typography: List[FontInfo] = Field(default_factory=list)
    global_design_tokens: List[DesignToken] = Field(default_factory=list)
    
    # Output configuration
    output_directory: Optional[Path] = None
    
    # Analysis quality and validation
    validation: ValidationReport = Field(default_factory=ValidationReport)
    stats: SiteStats = Field(default_factory=SiteStats)
    
    # Global errors and warnings
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    
    @field_validator("base_url", mode="before")
    @classmethod
    def validate_base_url(cls, v):
        """Ensure base URL is properly formatted."""
        if isinstance(v, str):
            if not v.startswith(("http://", "https://")):
                v = "https://" + v
            # Remove trailing slash for consistency
            v = v.rstrip("/")
        return v
    
    def __init__(self, **data):
        # Set domain from base_url if not provided
        if 'domain' not in data and 'base_url' in data:
            base_url = data['base_url']
            if isinstance(base_url, str):
                if not base_url.startswith(("http://", "https://")):
                    base_url = "https://" + base_url
            data['domain'] = urlparse(str(base_url)).netloc
        super().__init__(**data)
    
    @property
    def total_pages(self) -> int:
        """Total number of pages discovered."""
        return len(self.pages)
    
    @property
    def crawled_pages(self) -> List[Page]:
        """Get all successfully crawled pages."""
        return [page for page in self.pages.values() if page.is_successful]
    
    @property
    def failed_pages(self) -> List[Page]:
        """Get all pages that failed to crawl."""
        return [page for page in self.pages.values() if page.status.value == "failed"]
    
    @property
    def is_analysis_complete(self) -> bool:
        """Check if analysis is complete."""
        return self.analysis_completed_at is not None
    
    def add_page(self, page: Page) -> None:
        """Add a page to the site."""
        url_str = str(page.url)
        self.pages[url_str] = page
        self.stats.total_pages_discovered = len(self.pages)
    
    def get_page(self, url: str) -> Optional[Page]:
        """Get a page by URL."""
        return self.pages.get(url)
    
    def has_page(self, url: str) -> bool:
        """Check if site has a specific page."""
        return url in self.pages
    
    def get_pages_by_depth(self, depth: int) -> List[Page]:
        """Get all pages at a specific depth."""
        return [page for page in self.pages.values() if page.depth == depth]
    
    def get_uncrawled_pages(self) -> List[Page]:
        """Get all pages that haven't been crawled yet."""
        return [page for page in self.pages.values() if page.status.value == "pending"]
    
    def add_experience_pattern(self, pattern: ExperiencePattern) -> None:
        """Add a user experience pattern."""
        # Avoid duplicates
        existing_names = [p.pattern_name for p in self.experience_patterns]
        if pattern.pattern_name not in existing_names:
            self.experience_patterns.append(pattern)
    
    def add_component_spec(self, component: ComponentSpec) -> None:
        """Add a component specification."""
        # Avoid duplicates
        existing_names = [c.component_name for c in self.component_specifications]
        if component.component_name not in existing_names:
            self.component_specifications.append(component)
    
    def add_global_color(self, color: ColorInfo) -> None:
        """Add a color to the global palette."""
        # Avoid duplicates based on hex value
        existing_colors = [c.hex for c in self.global_color_palette]
        if color.hex not in existing_colors:
            self.global_color_palette.append(color)
    
    def add_global_font(self, font: FontInfo) -> None:
        """Add a font to the global typography."""
        # Avoid duplicates based on family name
        existing_fonts = [f.family for f in self.global_typography]
        if font.family not in existing_fonts:
            self.global_typography.append(font)
    
    def add_design_token(self, token: DesignToken) -> None:
        """Add a design token."""
        # Avoid duplicates based on name
        existing_tokens = [t.name for t in self.global_design_tokens]
        if token.name not in existing_tokens:
            self.global_design_tokens.append(token)
    
    def add_error(self, error: str) -> None:
        """Add a site-level error."""
        if error not in self.errors:
            self.errors.append(error)
    
    def add_warning(self, warning: str) -> None:
        """Add a site-level warning."""
        if warning not in self.warnings:
            self.warnings.append(warning)
    
    def mark_analysis_complete(self) -> None:
        """Mark the analysis as complete and update stats."""
        self.analysis_completed_at = datetime.now()
        
        # Update statistics
        self.stats.total_pages_crawled = len(self.crawled_pages)
        self.stats.total_pages_analyzed = len([p for p in self.pages.values() if p.analyzed_at])
        self.stats.total_assets_found = sum(len(p.assets) for p in self.pages.values())
        self.stats.total_components_identified = sum(len(p.structure.components) for p in self.pages.values() if p.analyzed_at)
        self.stats.total_patterns_identified = len(self.experience_patterns)
        
        # Calculate duration
        if self.analysis_started_at:
            duration = (self.analysis_completed_at - self.analysis_started_at).total_seconds()
            self.stats.analysis_duration_seconds = duration
    
    def get_site_summary(self) -> Dict[str, Any]:
        """Get a comprehensive summary of the site analysis."""
        return {
            "base_url": str(self.base_url),
            "domain": self.domain,
            "analysis_date": self.metadata.analysis_date.isoformat(),
            "analysis_philosophy": self.metadata.analysis_philosophy.value,
            "target_framework": self.metadata.target_framework.value,
            "stats": self.stats.dict(),
            "design_intent": {
                "brand_personality": self.design_intent.brand_personality,
                "ux_goals": self.design_intent.user_experience_goals,
                "conversion_focus": self.design_intent.conversion_focus,
            },
            "patterns_count": len(self.experience_patterns),
            "components_count": self.stats.total_components_identified,
            "global_colors_count": len(self.global_color_palette),
            "global_fonts_count": len(self.global_typography),
            "validation_score": self.validation.completeness_score,
            "errors_count": len(self.errors),
            "warnings_count": len(self.warnings),
            "output_directory": str(self.output_directory) if self.output_directory else None,
        }
    
    def get_json_specification(self) -> Dict[str, Any]:
        """Generate the main JSON specification following PRD format."""
        return {
            "metadata": {
                "analysis_philosophy": self.metadata.analysis_philosophy.value,
                "target_framework": self.metadata.target_framework.value,
                "design_era": self.metadata.design_era,
                "accessibility_level": self.metadata.accessibility_level.value,
                "performance_targets": self.metadata.performance_targets,
                "analysis_date": self.metadata.analysis_date.isoformat(),
                "tool_version": self.metadata.tool_version,
                "base_url": str(self.base_url),
                "domain": self.domain,
            },
            "design_intent": {
                "brand_personality": self.design_intent.brand_personality,
                "user_experience_goals": self.design_intent.user_experience_goals,
                "visual_hierarchy": self.design_intent.visual_hierarchy,
                "conversion_focus": self.design_intent.conversion_focus,
            },
            "experience_patterns": [
                {
                    "pattern_name": pattern.pattern_name,
                    "original_intent": pattern.original_intent,
                    "modern_implementation": pattern.modern_implementation,
                    "user_benefit": pattern.user_benefit,
                    "technical_requirements": pattern.technical_requirements,
                }
                for pattern in self.experience_patterns
            ],
            "component_specifications": [
                {
                    "component_name": comp.component_name,
                    "component_type": comp.component_type.value,
                    "design_intent": comp.design_intent,
                    "modern_features": comp.modern_features,
                    "accessibility_features": comp.accessibility_features,
                    "performance_considerations": comp.performance_considerations,
                }
                for comp in self.component_specifications
            ],
            "technical_modernization": {
                "performance_strategy": self.technical_modernization.performance_strategy,
                "accessibility_baseline": self.technical_modernization.accessibility_baseline,
                "security_considerations": self.technical_modernization.security_considerations,
                "seo_optimizations": self.technical_modernization.seo_optimizations,
            },
            "design_system": {
                "color_palette": [
                    {
                        "hex": color.hex,
                        "rgb": color.rgb,
                        "usage_context": color.usage_context,
                        "frequency": color.frequency,
                    }
                    for color in self.global_color_palette
                ],
                "typography": [
                    {
                        "family": font.family,
                        "weights": font.weights,
                        "sizes": font.sizes,
                        "usage_context": font.usage_context,
                    }
                    for font in self.global_typography
                ],
                "design_tokens": [
                    {
                        "name": token.name,
                        "value": token.value,
                        "category": token.category,
                        "usage": token.usage,
                    }
                    for token in self.global_design_tokens
                ],
            },
            "validation": {
                "completeness_score": self.validation.completeness_score,
                "quality_metrics": self.validation.quality_metrics,
                "missing_elements": self.validation.missing_elements,
                "recommendations": self.validation.recommendations,
                "analysis_warnings": self.validation.analysis_warnings,
            },
            "statistics": self.stats.dict(),
        }