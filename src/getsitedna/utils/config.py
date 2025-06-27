"""Configuration management for performance and caching settings."""

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
from pydantic import BaseModel, Field


@dataclass
class CacheConfig:
    """Cache configuration settings."""
    enabled: bool = True
    cache_dir: str = ".getsitedna_cache"
    default_ttl: int = 3600  # 1 hour
    max_size: int = 100 * 1024 * 1024  # 100MB
    cleanup_interval: int = 600  # 10 minutes
    
    # Memory cache settings
    memory_cache_enabled: bool = True
    memory_cache_max_size: int = 1000
    memory_cache_ttl: int = 300  # 5 minutes


@dataclass
class PerformanceConfig:
    """Performance optimization settings."""
    # Concurrency settings
    max_concurrent_requests: int = 5
    max_concurrent_extractions: int = 4
    use_process_pool: bool = False
    
    # Resource monitoring
    enable_monitoring: bool = True
    memory_threshold: int = 80  # Percentage
    cpu_threshold: int = 90     # Percentage
    
    # Batch processing
    batch_size: int = 5
    adaptive_batching: bool = True
    
    # Optimization features
    enable_gc_optimization: bool = True
    enable_adaptive_delays: bool = True


@dataclass
class OptimizationSettings:
    """Overall optimization settings."""
    cache: CacheConfig = Field(default_factory=CacheConfig)
    performance: PerformanceConfig = Field(default_factory=PerformanceConfig)
    
    # Feature flags
    enable_caching: bool = True
    enable_concurrent_processing: bool = True
    enable_performance_monitoring: bool = True
    
    # Debugging
    debug_mode: bool = False
    log_performance_metrics: bool = False


class ConfigManager:
    """Manage application configuration."""
    
    def __init__(self, config_file: Optional[Path] = None):
        self.config_file = config_file or Path.home() / ".getsitedna" / "config.json"
        self._settings: Optional[OptimizationSettings] = None
        
    def load_config(self) -> OptimizationSettings:
        """Load configuration from file or use defaults."""
        if self._settings is not None:
            return self._settings
        
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    config_data = json.load(f)
                    
                # Convert to dataclass
                self._settings = OptimizationSettings(
                    cache=CacheConfig(**config_data.get('cache', {})),
                    performance=PerformanceConfig(**config_data.get('performance', {})),
                    enable_caching=config_data.get('enable_caching', True),
                    enable_concurrent_processing=config_data.get('enable_concurrent_processing', True),
                    enable_performance_monitoring=config_data.get('enable_performance_monitoring', True),
                    debug_mode=config_data.get('debug_mode', False),
                    log_performance_metrics=config_data.get('log_performance_metrics', False)
                )
                
            except Exception as e:
                # Use defaults if config loading fails
                self._settings = OptimizationSettings()
        else:
            self._settings = OptimizationSettings()
        
        # Override with environment variables
        self._apply_env_overrides()
        
        return self._settings
    
    def save_config(self, settings: OptimizationSettings) -> None:
        """Save configuration to file."""
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        
        config_data = {
            'cache': asdict(settings.cache),
            'performance': asdict(settings.performance),
            'enable_caching': settings.enable_caching,
            'enable_concurrent_processing': settings.enable_concurrent_processing,
            'enable_performance_monitoring': settings.enable_performance_monitoring,
            'debug_mode': settings.debug_mode,
            'log_performance_metrics': settings.log_performance_metrics
        }
        
        with open(self.config_file, 'w') as f:
            json.dump(config_data, f, indent=2)
        
        self._settings = settings
    
    def _apply_env_overrides(self) -> None:
        """Apply environment variable overrides."""
        if not self._settings:
            return
        
        # Cache settings
        if os.getenv('GETSITEDNA_CACHE_ENABLED'):
            self._settings.cache.enabled = os.getenv('GETSITEDNA_CACHE_ENABLED').lower() == 'true'
        
        if os.getenv('GETSITEDNA_CACHE_TTL'):
            try:
                self._settings.cache.default_ttl = int(os.getenv('GETSITEDNA_CACHE_TTL'))
            except ValueError:
                pass
        
        if os.getenv('GETSITEDNA_CACHE_MAX_SIZE'):
            try:
                self._settings.cache.max_size = int(os.getenv('GETSITEDNA_CACHE_MAX_SIZE'))
            except ValueError:
                pass
        
        # Performance settings
        if os.getenv('GETSITEDNA_MAX_WORKERS'):
            try:
                self._settings.performance.max_concurrent_requests = int(os.getenv('GETSITEDNA_MAX_WORKERS'))
            except ValueError:
                pass
        
        if os.getenv('GETSITEDNA_BATCH_SIZE'):
            try:
                self._settings.performance.batch_size = int(os.getenv('GETSITEDNA_BATCH_SIZE'))
            except ValueError:
                pass
        
        # Feature flags
        if os.getenv('GETSITEDNA_ENABLE_CACHING'):
            self._settings.enable_caching = os.getenv('GETSITEDNA_ENABLE_CACHING').lower() == 'true'
        
        if os.getenv('GETSITEDNA_DEBUG_MODE'):
            self._settings.debug_mode = os.getenv('GETSITEDNA_DEBUG_MODE').lower() == 'true'
    
    def get_cache_config(self) -> CacheConfig:
        """Get cache configuration."""
        return self.load_config().cache
    
    def get_performance_config(self) -> PerformanceConfig:
        """Get performance configuration."""
        return self.load_config().performance
    
    def is_caching_enabled(self) -> bool:
        """Check if caching is enabled."""
        return self.load_config().enable_caching and self.get_cache_config().enabled
    
    def is_concurrent_processing_enabled(self) -> bool:
        """Check if concurrent processing is enabled."""
        return self.load_config().enable_concurrent_processing
    
    def is_monitoring_enabled(self) -> bool:
        """Check if performance monitoring is enabled."""
        return self.load_config().enable_performance_monitoring
    
    def is_debug_mode(self) -> bool:
        """Check if debug mode is enabled."""
        return self.load_config().debug_mode
    
    def should_log_metrics(self) -> bool:
        """Check if performance metrics should be logged."""
        return self.load_config().log_performance_metrics
    
    def reset_to_defaults(self) -> None:
        """Reset configuration to defaults."""
        self._settings = OptimizationSettings()
        self.save_config(self._settings)
    
    def create_default_config(self) -> None:
        """Create a default configuration file."""
        default_settings = OptimizationSettings()
        self.save_config(default_settings)


# Global configuration manager instance
config_manager = ConfigManager()


def get_cache_config() -> CacheConfig:
    """Get global cache configuration."""
    return config_manager.get_cache_config()


def get_performance_config() -> PerformanceConfig:
    """Get global performance configuration."""
    return config_manager.get_performance_config()


def is_caching_enabled() -> bool:
    """Check if caching is globally enabled."""
    return config_manager.is_caching_enabled()


def is_concurrent_processing_enabled() -> bool:
    """Check if concurrent processing is globally enabled."""
    return config_manager.is_concurrent_processing_enabled()


def is_monitoring_enabled() -> bool:
    """Check if performance monitoring is globally enabled."""
    return config_manager.is_monitoring_enabled()