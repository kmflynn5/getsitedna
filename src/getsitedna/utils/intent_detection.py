"""Intent and feature detection for pages."""

import re
from typing import Dict, List, Set, Optional, Tuple
from urllib.parse import urlparse
from enum import Enum

from ..models.page import Page
from ..models.schemas import ComponentType


class PageIntent(Enum):
    """Business intent categories for pages."""
    LANDING = "landing"
    AUTHENTICATION = "authentication"
    ECOMMERCE = "e-commerce"
    PAYMENT = "payment"
    LEAD_GENERATION = "lead_generation"
    CONTENT = "content"
    SUPPORT = "support"
    ADMIN = "admin"
    BLOG = "blog"
    PRODUCT = "product"
    PRICING = "pricing"
    ABOUT = "about"
    CONTACT = "contact"
    SEARCH = "search"
    USER_ACCOUNT = "user_account"
    DASHBOARD = "dashboard"
    ANALYTICS = "analytics"
    API = "api"
    DOCUMENTATION = "documentation"


class BusinessFeature(Enum):
    """Business features that need implementation."""
    USER_REGISTRATION = "user_registration"
    USER_LOGIN = "user_login"
    PASSWORD_RESET = "password_reset"
    PAYMENT_PROCESSING = "payment_processing"
    SHOPPING_CART = "shopping_cart"
    PRODUCT_CATALOG = "product_catalog"
    SEARCH_FUNCTIONALITY = "search_functionality"
    CONTACT_FORMS = "contact_forms"
    EMAIL_SUBSCRIPTION = "email_subscription"
    BLOG_SYSTEM = "blog_system"
    CONTENT_MANAGEMENT = "content_management"
    USER_PROFILES = "user_profiles"
    ADMIN_PANEL = "admin_panel"
    ANALYTICS_TRACKING = "analytics_tracking"
    REVIEW_SYSTEM = "review_system"
    NOTIFICATION_SYSTEM = "notification_system"
    FILE_UPLOAD = "file_upload"
    SOCIAL_INTEGRATION = "social_integration"
    API_INTEGRATION = "api_integration"
    LIVE_CHAT = "live_chat"


class IntentDetector:
    """Detects business intent and features from page content."""
    
    def __init__(self):
        self.url_patterns = self._init_url_patterns()
        self.content_patterns = self._init_content_patterns()
        self.form_patterns = self._init_form_patterns()
        self.component_patterns = self._init_component_patterns()
    
    def analyze_page(self, page: Page) -> Dict[str, any]:
        """Analyze a page and return intent and features."""
        url_lower = str(page.url).lower()
        title_lower = (page.title or "").lower()
        
        # Detect primary intent
        primary_intent = self._detect_primary_intent(page, url_lower, title_lower)
        
        # Detect business features needed
        features = self._detect_business_features(page, url_lower, title_lower)
        
        # Get feature description
        description = self._get_feature_description(primary_intent, features)
        
        # Determine reconstruction requirements
        requirements = self._get_reconstruction_requirements(features)
        
        return {
            "primary_intent": primary_intent.value if primary_intent else None,
            "business_features": [f.value for f in features],
            "description": description,
            "reconstruction_requirements": requirements,
            "priority": self._get_priority(primary_intent, features),
            "icon": self._get_icon(primary_intent)
        }
    
    def _detect_primary_intent(self, page: Page, url_lower: str, title_lower: str) -> Optional[PageIntent]:
        """Detect the primary business intent of a page."""
        
        # URL-based detection (highest priority)
        for intent, patterns in self.url_patterns.items():
            for pattern in patterns:
                if re.search(pattern, url_lower):
                    return intent
        
        # Title-based detection
        for intent, keywords in [
            (PageIntent.AUTHENTICATION, ["login", "sign in", "log in", "register", "sign up", "signup"]),
            (PageIntent.PAYMENT, ["checkout", "payment", "billing"]),
            (PageIntent.PRICING, ["pricing", "plans", "subscription"]),
            (PageIntent.ABOUT, ["about", "about us", "company"]),
            (PageIntent.CONTACT, ["contact", "contact us", "get in touch"]),
            (PageIntent.BLOG, ["blog", "news", "articles"]),
            (PageIntent.SUPPORT, ["support", "help", "faq"]),
        ]:
            for keyword in keywords:
                if keyword in title_lower:
                    return intent
        
        # Component-based detection
        components = [comp.component_type for comp in page.structure.components]
        
        # Check for form components (could indicate authentication/contact)
        if ComponentType.FORM in components:
            return PageIntent.AUTHENTICATION  # Could be login/register
        
        # Check for forms to determine intent
        for form in page.technical.forms:
            form_intent = self._analyze_form_intent(form)
            if form_intent:
                return form_intent
        
        # Default fallback based on URL structure
        if url_lower.endswith('/') or '/index' in url_lower or url_lower.count('/') <= 2:
            return PageIntent.LANDING
        
        return PageIntent.CONTENT  # Default fallback
    
    def _detect_business_features(self, page: Page, url_lower: str, title_lower: str) -> Set[BusinessFeature]:
        """Detect all business features present on a page."""
        features = set()
        
        # URL-based feature detection
        if re.search(r'/login|/signin|/sign-in', url_lower):
            features.add(BusinessFeature.USER_LOGIN)
        if re.search(r'/register|/signup|/sign-up', url_lower):
            features.add(BusinessFeature.USER_REGISTRATION)
        if re.search(r'/reset|/forgot', url_lower):
            features.add(BusinessFeature.PASSWORD_RESET)
        if re.search(r'/checkout|/payment|/billing', url_lower):
            features.add(BusinessFeature.PAYMENT_PROCESSING)
        if re.search(r'/cart|/basket', url_lower):
            features.add(BusinessFeature.SHOPPING_CART)
        if re.search(r'/products?|/catalog|/shop', url_lower):
            features.add(BusinessFeature.PRODUCT_CATALOG)
        if re.search(r'/search', url_lower):
            features.add(BusinessFeature.SEARCH_FUNCTIONALITY)
        if re.search(r'/admin|/dashboard', url_lower):
            features.add(BusinessFeature.ADMIN_PANEL)
        if re.search(r'/blog|/news|/articles', url_lower):
            features.add(BusinessFeature.BLOG_SYSTEM)
        if re.search(r'/profile|/account|/settings', url_lower):
            features.add(BusinessFeature.USER_PROFILES)
        
        # Form-based feature detection
        for form in page.technical.forms:
            form_features = self._analyze_form_features(form)
            features.update(form_features)
        
        # Component-based feature detection
        components = [comp.component_type for comp in page.structure.components]
        
        # Use actual component types available in the schema
        if ComponentType.FORM in components:
            features.add(BusinessFeature.CONTACT_FORMS)
        if ComponentType.CARD in components:
            features.add(BusinessFeature.PRODUCT_CATALOG)  # Cards might be products
        
        # Content-based feature detection
        content_lower = ""
        for content_list in page.content.text_content.values():
            content_lower += " ".join(content_list).lower()
        
        if "subscribe" in content_lower or "newsletter" in content_lower:
            features.add(BusinessFeature.EMAIL_SUBSCRIPTION)
        if "review" in content_lower or "rating" in content_lower:
            features.add(BusinessFeature.REVIEW_SYSTEM)
        if "chat" in content_lower or "live support" in content_lower:
            features.add(BusinessFeature.LIVE_CHAT)
        
        return features
    
    def _analyze_form_intent(self, form) -> Optional[PageIntent]:
        """Analyze a form to determine page intent."""
        field_names = [field.name.lower() for field in form.fields]
        field_types = [field.type.lower() for field in form.fields]
        
        # Login forms
        if any("password" in name for name in field_names) and any("email" in name or "username" in name for name in field_names):
            if len(form.fields) <= 3:  # Login forms are typically simple
                return PageIntent.AUTHENTICATION
        
        # Payment forms
        if any("card" in name or "credit" in name or "payment" in name for name in field_names):
            return PageIntent.PAYMENT
        
        # Contact forms
        if any("message" in name or "subject" in name for name in field_names):
            return PageIntent.CONTACT
        
        return None
    
    def _analyze_form_features(self, form) -> Set[BusinessFeature]:
        """Analyze a form to detect business features."""
        features = set()
        field_names = [field.name.lower() for field in form.fields]
        
        # Authentication features
        if any("password" in name for name in field_names):
            if any("confirm" in name for name in field_names) or len(form.fields) > 3:
                features.add(BusinessFeature.USER_REGISTRATION)
            else:
                features.add(BusinessFeature.USER_LOGIN)
        
        # Payment features
        if any("card" in name or "credit" in name or "payment" in name for name in field_names):
            features.add(BusinessFeature.PAYMENT_PROCESSING)
        
        # Contact features
        if any("message" in name or "subject" in name for name in field_names):
            features.add(BusinessFeature.CONTACT_FORMS)
        
        # Email subscription
        if any("email" in name for name in field_names) and any("subscribe" in name or "newsletter" in name for name in field_names):
            features.add(BusinessFeature.EMAIL_SUBSCRIPTION)
        
        # File upload
        if any("file" in field.type.lower() for field in form.fields):
            features.add(BusinessFeature.FILE_UPLOAD)
        
        return features
    
    def _get_feature_description(self, intent: Optional[PageIntent], features: Set[BusinessFeature]) -> str:
        """Generate a human-readable description of page purpose."""
        if intent == PageIntent.LANDING:
            return "Homepage/Landing → Brand awareness, user acquisition"
        elif intent == PageIntent.AUTHENTICATION:
            return "User Authentication → Account access, security"
        elif intent == PageIntent.ECOMMERCE:
            return "E-commerce → Product sales, revenue generation"
        elif intent == PageIntent.PAYMENT:
            return "Payment Processing → Transaction completion, billing"
        elif intent == PageIntent.LEAD_GENERATION:
            return "Lead Generation → Customer acquisition, marketing"
        elif intent == PageIntent.CONTACT:
            return "Customer Contact → Support, communication"
        elif intent == PageIntent.PRICING:
            return "Pricing Information → Plan comparison, sales conversion"
        elif intent == PageIntent.ABOUT:
            return "Company Information → Trust building, transparency"
        elif intent == PageIntent.BLOG:
            return "Content Marketing → SEO, thought leadership"
        elif intent == PageIntent.SUPPORT:
            return "Customer Support → Help, troubleshooting"
        elif intent == PageIntent.ADMIN:
            return "Administration → Internal management, operations"
        elif intent == PageIntent.DASHBOARD:
            return "User Dashboard → Data visualization, user management"
        else:
            return "Content Page → Information delivery, user engagement"
    
    def _get_reconstruction_requirements(self, features: Set[BusinessFeature]) -> List[str]:
        """Generate technical requirements for reconstruction."""
        requirements = []
        
        if BusinessFeature.PAYMENT_PROCESSING in features:
            requirements.append("Payment gateway integration (Stripe/PayPal)")
        if BusinessFeature.USER_REGISTRATION in features or BusinessFeature.USER_LOGIN in features:
            requirements.append("User authentication system")
        if BusinessFeature.SHOPPING_CART in features:
            requirements.append("Shopping cart functionality")
        if BusinessFeature.PRODUCT_CATALOG in features:
            requirements.append("Product database and catalog system")
        if BusinessFeature.SEARCH_FUNCTIONALITY in features:
            requirements.append("Search engine integration")
        if BusinessFeature.EMAIL_SUBSCRIPTION in features:
            requirements.append("Email marketing system integration")
        if BusinessFeature.CONTACT_FORMS in features:
            requirements.append("Form handling and email delivery")
        if BusinessFeature.BLOG_SYSTEM in features:
            requirements.append("Content management system")
        if BusinessFeature.ADMIN_PANEL in features:
            requirements.append("Administrative interface")
        if BusinessFeature.FILE_UPLOAD in features:
            requirements.append("File storage and upload handling")
        if BusinessFeature.LIVE_CHAT in features:
            requirements.append("Real-time chat system")
        if BusinessFeature.REVIEW_SYSTEM in features:
            requirements.append("Rating and review functionality")
        
        return requirements
    
    def _get_priority(self, intent: Optional[PageIntent], features: Set[BusinessFeature]) -> str:
        """Determine implementation priority."""
        if intent == PageIntent.LANDING or BusinessFeature.PAYMENT_PROCESSING in features:
            return "High"
        elif intent in [PageIntent.AUTHENTICATION, PageIntent.ECOMMERCE, PageIntent.CONTACT]:
            return "High"
        elif intent in [PageIntent.PRICING, PageIntent.ABOUT]:
            return "Medium"
        else:
            return "Low"
    
    def _get_icon(self, intent: Optional[PageIntent]) -> str:
        """Get emoji icon for page intent."""
        icon_map = {
            PageIntent.LANDING: "🏠",
            PageIntent.AUTHENTICATION: "🔐",
            PageIntent.ECOMMERCE: "🛍️",
            PageIntent.PAYMENT: "💳",
            PageIntent.LEAD_GENERATION: "📈",
            PageIntent.CONTACT: "📞",
            PageIntent.PRICING: "💰",
            PageIntent.ABOUT: "ℹ️",
            PageIntent.BLOG: "📝",
            PageIntent.SUPPORT: "❓",
            PageIntent.ADMIN: "⚙️",
            PageIntent.DASHBOARD: "📊",
            PageIntent.PRODUCT: "📦",
            PageIntent.SEARCH: "🔍",
            PageIntent.USER_ACCOUNT: "👤",
            PageIntent.API: "🔌",
            PageIntent.DOCUMENTATION: "📚",
        }
        return icon_map.get(intent, "📄")
    
    def _init_url_patterns(self) -> Dict[PageIntent, List[str]]:
        """Initialize URL patterns for intent detection."""
        return {
            PageIntent.AUTHENTICATION: [
                r'/login', r'/signin', r'/sign-in', r'/register', r'/signup', r'/sign-up',
                r'/auth', r'/oauth', r'/sso'
            ],
            PageIntent.PAYMENT: [
                r'/checkout', r'/payment', r'/billing', r'/pay', r'/purchase',
                r'/subscription', r'/upgrade'
            ],
            PageIntent.ECOMMERCE: [
                r'/shop', r'/store', r'/products?', r'/catalog', r'/cart', r'/basket'
            ],
            PageIntent.ADMIN: [
                r'/admin', r'/dashboard', r'/manage', r'/control', r'/backend'
            ],
            PageIntent.BLOG: [
                r'/blog', r'/news', r'/articles', r'/posts?'
            ],
            PageIntent.SUPPORT: [
                r'/support', r'/help', r'/faq', r'/contact', r'/tickets?'
            ],
            PageIntent.ABOUT: [
                r'/about', r'/company', r'/team', r'/history'
            ],
            PageIntent.PRICING: [
                r'/pricing', r'/plans', r'/packages', r'/rates'
            ],
            PageIntent.SEARCH: [
                r'/search', r'/find', r'/results'
            ],
            PageIntent.USER_ACCOUNT: [
                r'/profile', r'/account', r'/settings', r'/preferences'
            ],
            PageIntent.API: [
                r'/api', r'/v[0-9]', r'/endpoints'
            ],
            PageIntent.DOCUMENTATION: [
                r'/docs', r'/documentation', r'/guide', r'/manual'
            ],
        }
    
    def _init_content_patterns(self) -> Dict[PageIntent, List[str]]:
        """Initialize content patterns for intent detection."""
        return {}  # Could be expanded for content-based detection
    
    def _init_form_patterns(self) -> Dict[PageIntent, List[str]]:
        """Initialize form patterns for intent detection."""
        return {}  # Could be expanded for form-based detection
    
    def _init_component_patterns(self) -> Dict[PageIntent, List[ComponentType]]:
        """Initialize component patterns for intent detection."""
        return {}  # Could be expanded for component-based detection