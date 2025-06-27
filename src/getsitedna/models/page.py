"""Page data model for website analysis."""

from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from urllib.parse import urljoin, urlparse

from pydantic import BaseModel, Field, HttpUrl, validator

from .schemas import (
    CrawlStatus,
    SEOMetadata,
    AssetInfo,
    PageContent,
    PageStructure,
    PageDesign,
    PageTechnical,
    ValidationReport,
)


class Page(BaseModel):
    """Represents a single analyzed webpage."""
    
    url: HttpUrl
    title: Optional[str] = None
    status: CrawlStatus = CrawlStatus.PENDING
    
    # Analysis timestamps
    discovered_at: datetime = Field(default_factory=datetime.now)
    crawled_at: Optional[datetime] = None
    analyzed_at: Optional[datetime] = None
    
    # HTTP response info
    status_code: Optional[int] = None
    redirect_url: Optional[HttpUrl] = None
    content_type: Optional[str] = None
    content_length: Optional[int] = None
    
    # Page hierarchy
    parent_url: Optional[HttpUrl] = None
    depth: int = Field(default=0, ge=0)
    children: List[HttpUrl] = Field(default_factory=list)
    
    # Raw content
    html_content: Optional[str] = None
    rendered_html: Optional[str] = None  # After JavaScript execution
    
    # SEO and metadata
    seo: SEOMetadata = Field(default_factory=SEOMetadata)
    
    # Content analysis
    content: PageContent = Field(default_factory=PageContent)
    
    # Structural analysis
    structure: PageStructure = Field(default_factory=PageStructure)
    
    # Design analysis
    design: PageDesign = Field(default_factory=PageDesign)
    
    # Technical analysis
    technical: PageTechnical = Field(default_factory=PageTechnical)
    
    # Assets found on this page
    assets: List[AssetInfo] = Field(default_factory=list)
    
    # Links found on this page
    internal_links: List[HttpUrl] = Field(default_factory=list)
    external_links: List[HttpUrl] = Field(default_factory=list)
    
    # Analysis quality
    validation: ValidationReport = Field(default_factory=ValidationReport)
    
    # Error tracking
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    
    @validator("url", "redirect_url", "parent_url", pre=True)
    def validate_urls(cls, v):
        """Ensure URLs are properly formatted."""
        if v is None:
            return v
        if isinstance(v, str):
            # Basic URL validation and cleanup
            if not v.startswith(("http://", "https://")):
                v = "https://" + v
        return v
    
    @property
    def domain(self) -> str:
        """Extract domain from URL."""
        return urlparse(str(self.url)).netloc
    
    @property
    def path(self) -> str:
        """Extract path from URL."""
        return urlparse(str(self.url)).path
    
    @property
    def is_crawled(self) -> bool:
        """Check if page has been crawled."""
        return self.status in [CrawlStatus.COMPLETED, CrawlStatus.FAILED]
    
    @property
    def is_successful(self) -> bool:
        """Check if page was successfully crawled and analyzed."""
        return (
            self.status == CrawlStatus.COMPLETED and
            self.status_code and
            200 <= self.status_code < 300
        )
    
    def add_child(self, child_url: HttpUrl) -> None:
        """Add a child page URL."""
        if child_url not in self.children:
            self.children.append(child_url)
    
    def add_internal_link(self, link_url: HttpUrl) -> None:
        """Add an internal link found on this page."""
        if link_url not in self.internal_links:
            self.internal_links.append(link_url)
    
    def add_external_link(self, link_url: HttpUrl) -> None:
        """Add an external link found on this page."""
        if link_url not in self.external_links:
            self.external_links.append(link_url)
    
    def add_asset(self, asset: AssetInfo) -> None:
        """Add an asset found on this page."""
        # Avoid duplicates based on URL
        existing_urls = [a.url for a in self.assets]
        if asset.url not in existing_urls:
            self.assets.append(asset)
    
    def add_error(self, error: str) -> None:
        """Add an error to the page."""
        if error not in self.errors:
            self.errors.append(error)
    
    def add_warning(self, warning: str) -> None:
        """Add a warning to the page."""
        if warning not in self.warnings:
            self.warnings.append(warning)
    
    def mark_crawled(self, status_code: int, content_type: Optional[str] = None) -> None:
        """Mark page as crawled with response info."""
        self.status = CrawlStatus.COMPLETED if 200 <= status_code < 300 else CrawlStatus.FAILED
        self.status_code = status_code
        self.content_type = content_type
        self.crawled_at = datetime.now()
    
    def mark_analyzed(self) -> None:
        """Mark page as fully analyzed."""
        self.analyzed_at = datetime.now()
    
    def resolve_url(self, relative_url: str) -> str:
        """Resolve a relative URL against this page's URL."""
        return urljoin(str(self.url), relative_url)
    
    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of page analysis."""
        return {
            "url": str(self.url),
            "title": self.title,
            "status": self.status.value,
            "status_code": self.status_code,
            "depth": self.depth,
            "content_length": self.content_length,
            "components_count": len(self.structure.components),
            "assets_count": len(self.assets),
            "internal_links_count": len(self.internal_links),
            "external_links_count": len(self.external_links),
            "errors_count": len(self.errors),
            "warnings_count": len(self.warnings),
            "validation_score": self.validation.completeness_score,
        }