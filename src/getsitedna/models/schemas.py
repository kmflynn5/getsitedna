"""Pydantic schemas for GetSiteDNA data models."""

from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Union, Any

from pydantic import BaseModel, Field, HttpUrl, validator


class AnalysisPhilosophy(str, Enum):
    """Analysis approach philosophy."""
    MODERN_INTERPRETATION = "modern_interpretation"
    PIXEL_PERFECT = "pixel_perfect"
    COMPONENT_FOCUSED = "component_focused"


class TargetFramework(str, Enum):
    """Target framework for modern implementation."""
    REACT_NEXTJS = "react_nextjs"
    VUE_NUXT = "vue_nuxt"
    SVELTE_SVELTEKIT = "svelte_sveltekit"
    VANILLA_JS = "vanilla_js"


class AccessibilityLevel(str, Enum):
    """Accessibility compliance level."""
    WCAG_A = "wcag_a"
    WCAG_AA = "wcag_aa"
    WCAG_AAA = "wcag_aaa"


class ContentType(str, Enum):
    """Type of content identified."""
    HEADING = "heading"
    BODY_TEXT = "body_text"
    CTA = "call_to_action"
    NAVIGATION = "navigation"
    METADATA = "metadata"
    FORM = "form"
    MEDIA = "media"


class ComponentType(str, Enum):
    """Type of UI component."""
    HEADER = "header"
    FOOTER = "footer"
    NAVIGATION = "navigation"
    HERO = "hero"
    CARD = "card"
    BUTTON = "button"
    FORM = "form"
    MODAL = "modal"
    CAROUSEL = "carousel"
    SIDEBAR = "sidebar"


class CrawlStatus(str, Enum):
    """Page crawling status."""
    PENDING = "pending"
    CRAWLING = "crawling"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class ColorInfo(BaseModel):
    """Color information with usage context."""
    hex: str = Field(..., pattern=r"^#[0-9A-Fa-f]{6}$")
    rgb: tuple[int, int, int]
    usage_context: List[str] = Field(default_factory=list)
    frequency: int = Field(default=1, ge=0)


class FontInfo(BaseModel):
    """Typography information."""
    family: str
    weights: List[int] = Field(default_factory=list)
    sizes: List[str] = Field(default_factory=list)
    usage_context: List[str] = Field(default_factory=list)


class DesignToken(BaseModel):
    """Design system token."""
    name: str
    value: str
    category: str
    usage: List[str] = Field(default_factory=list)


class SEOMetadata(BaseModel):
    """SEO-related metadata."""
    title: Optional[str] = None
    description: Optional[str] = None
    keywords: List[str] = Field(default_factory=list)
    og_title: Optional[str] = None
    og_description: Optional[str] = None
    og_image: Optional[str] = None
    canonical_url: Optional[HttpUrl] = None
    schema_markup: Dict[str, Any] = Field(default_factory=dict)


class FormField(BaseModel):
    """Form field information."""
    name: str
    type: str
    label: Optional[str] = None
    placeholder: Optional[str] = None
    required: bool = False
    validation_pattern: Optional[str] = None


class FormInfo(BaseModel):
    """Form analysis data."""
    action: Optional[str] = None
    method: str = "GET"
    fields: List[FormField] = Field(default_factory=list)
    submit_text: Optional[str] = None


class AssetInfo(BaseModel):
    """Asset file information."""
    url: str
    local_path: Optional[Path] = None
    type: str
    size: Optional[int] = None
    alt_text: Optional[str] = None
    dimensions: Optional[tuple[int, int]] = None


class ComponentSpec(BaseModel):
    """Modern component specification."""
    component_name: str
    component_type: ComponentType
    design_intent: str
    modern_features: Dict[str, Any] = Field(default_factory=dict)
    accessibility_features: List[str] = Field(default_factory=list)
    performance_considerations: List[str] = Field(default_factory=list)


class ExperiencePattern(BaseModel):
    """User experience pattern."""
    pattern_name: str
    original_intent: str
    modern_implementation: Dict[str, Any] = Field(default_factory=dict)
    user_benefit: str
    technical_requirements: List[str] = Field(default_factory=list)


class TechnicalModernization(BaseModel):
    """Technical modernization recommendations."""
    performance_strategy: Dict[str, str] = Field(default_factory=dict)
    accessibility_baseline: Dict[str, str] = Field(default_factory=dict)
    security_considerations: List[str] = Field(default_factory=list)
    seo_optimizations: List[str] = Field(default_factory=list)


class DesignIntent(BaseModel):
    """Design intent analysis."""
    brand_personality: List[str] = Field(default_factory=list)
    user_experience_goals: List[str] = Field(default_factory=list)
    visual_hierarchy: Dict[str, str] = Field(default_factory=dict)
    conversion_focus: Optional[str] = None


class AnalysisMetadata(BaseModel):
    """Analysis metadata and configuration."""
    analysis_philosophy: AnalysisPhilosophy = AnalysisPhilosophy.MODERN_INTERPRETATION
    target_framework: TargetFramework = TargetFramework.REACT_NEXTJS
    design_era: str = "2025_modern_web"
    accessibility_level: AccessibilityLevel = AccessibilityLevel.WCAG_AA
    performance_targets: List[str] = Field(default_factory=lambda: ["core_web_vitals_optimized"])
    analysis_date: datetime = Field(default_factory=datetime.now)
    tool_version: str = "0.1.0"


class PageContent(BaseModel):
    """Page content analysis."""
    text_content: Dict[ContentType, List[str]] = Field(default_factory=dict)
    unique_copy: List[str] = Field(default_factory=list)
    boilerplate_text: List[str] = Field(default_factory=list)
    content_structure: Dict[str, Any] = Field(default_factory=dict)


class PageStructure(BaseModel):
    """Page structural analysis."""
    components: List[ComponentSpec] = Field(default_factory=list)
    layout_type: str = "unknown"
    grid_system: Optional[str] = None
    responsive_breakpoints: List[int] = Field(default_factory=list)
    navigation_structure: Dict[str, Any] = Field(default_factory=dict)


class PageDesign(BaseModel):
    """Page design analysis."""
    color_palette: List[ColorInfo] = Field(default_factory=list)
    typography: List[FontInfo] = Field(default_factory=list)
    design_tokens: List[DesignToken] = Field(default_factory=list)
    spacing_system: Dict[str, str] = Field(default_factory=dict)


class PageTechnical(BaseModel):
    """Page technical analysis."""
    forms: List[FormInfo] = Field(default_factory=list)
    api_endpoints: List[str] = Field(default_factory=list)
    javascript_frameworks: List[str] = Field(default_factory=list)
    performance_metrics: Dict[str, Any] = Field(default_factory=dict)


class CrawlConfig(BaseModel):
    """Configuration for website crawling."""
    max_depth: int = Field(default=3, description="Maximum crawling depth")
    max_pages: int = Field(default=50, description="Maximum pages to crawl")
    follow_external_links: bool = Field(default=False, description="Follow external links")
    respect_robots_txt: bool = Field(default=True, description="Respect robots.txt")
    delay_between_requests: float = Field(default=1.0, description="Delay between requests in seconds")


class ValidationReport(BaseModel):
    """Analysis validation and quality metrics."""
    completeness_score: float = Field(ge=0.0, le=1.0)
    quality_metrics: Dict[str, float] = Field(default_factory=dict)
    missing_elements: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    analysis_warnings: List[str] = Field(default_factory=list)