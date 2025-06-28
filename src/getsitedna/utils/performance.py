"""Performance optimization utilities."""

import asyncio
import time
import psutil
import gc
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from typing import Any, Callable, List, Dict, Optional, Tuple, Union
from dataclasses import dataclass
from functools import wraps
import threading
from contextlib import asynccontextmanager

from .error_handling import ErrorHandler, SafeExecutor


@dataclass
class PerformanceMetrics:
    """Container for performance metrics."""
    execution_time: float
    memory_usage: float
    cpu_usage: float
    concurrent_tasks: int
    cache_hits: int = 0
    cache_misses: int = 0
    
    @property
    def cache_hit_rate(self) -> float:
        """Calculate cache hit rate."""
        total = self.cache_hits + self.cache_misses
        return self.cache_hits / total if total > 0 else 0.0


class PerformanceMonitor:
    """Monitor and track performance metrics."""
    
    def __init__(self):
        self.error_handler = ErrorHandler("PerformanceMonitor")
        self._metrics_history: List[PerformanceMetrics] = []
        self._current_metrics: Optional[PerformanceMetrics] = None
        self._start_time: Optional[float] = None
        self._initial_memory: Optional[float] = None
    
    def start_monitoring(self) -> None:
        """Start performance monitoring."""
        self._start_time = time.time()
        self._initial_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
    
    def stop_monitoring(self, concurrent_tasks: int = 1) -> PerformanceMetrics:
        """Stop monitoring and return metrics."""
        if self._start_time is None:
            raise ValueError("Monitoring not started")
        
        execution_time = time.time() - self._start_time
        current_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        memory_usage = current_memory - (self._initial_memory or 0)
        cpu_usage = psutil.cpu_percent()
        
        metrics = PerformanceMetrics(
            execution_time=execution_time,
            memory_usage=memory_usage,
            cpu_usage=cpu_usage,
            concurrent_tasks=concurrent_tasks
        )
        
        self._metrics_history.append(metrics)
        self._current_metrics = metrics
        
        return metrics
    
    def get_average_metrics(self) -> Optional[PerformanceMetrics]:
        """Get average metrics from history."""
        if not self._metrics_history:
            return None
        
        avg_execution = sum(m.execution_time for m in self._metrics_history) / len(self._metrics_history)
        avg_memory = sum(m.memory_usage for m in self._metrics_history) / len(self._metrics_history)
        avg_cpu = sum(m.cpu_usage for m in self._metrics_history) / len(self._metrics_history)
        avg_concurrent = sum(m.concurrent_tasks for m in self._metrics_history) / len(self._metrics_history)
        
        return PerformanceMetrics(
            execution_time=avg_execution,
            memory_usage=avg_memory,
            cpu_usage=avg_cpu,
            concurrent_tasks=avg_concurrent
        )
    
    def clear_history(self) -> None:
        """Clear metrics history."""
        self._metrics_history.clear()


class ConcurrentProcessor:
    """Handle concurrent processing with optimal worker management."""
    
    def __init__(
        self, 
        max_workers: Optional[int] = None,
        use_process_pool: bool = False,
        enable_monitoring: bool = True
    ):
        """Initialize concurrent processor.
        
        Args:
            max_workers: Maximum number of workers (auto-detected if None)
            use_process_pool: Use ProcessPoolExecutor instead of ThreadPoolExecutor
            enable_monitoring: Enable performance monitoring
        """
        self.use_process_pool = use_process_pool
        self.max_workers = max_workers or self._get_optimal_workers()
        self.enable_monitoring = enable_monitoring
        self.error_handler = ErrorHandler("ConcurrentProcessor")
        self.monitor = PerformanceMonitor() if enable_monitoring else None
        
        # Semaphore to limit concurrent operations
        self._semaphore = asyncio.Semaphore(self.max_workers)
        
    def _get_optimal_workers(self) -> int:
        """Calculate optimal number of workers based on system resources."""
        cpu_count = psutil.cpu_count(logical=True)
        available_memory = psutil.virtual_memory().available / (1024 ** 3)  # GB
        
        # For I/O bound tasks, use more workers
        # For CPU bound tasks, use fewer workers
        if self.use_process_pool:
            # CPU bound - use physical cores
            return min(cpu_count, int(available_memory / 0.5))  # 500MB per process
        else:
            # I/O bound - can use more threads
            return min(cpu_count * 2, int(available_memory / 0.1))  # 100MB per thread
    
    async def process_batch(
        self, 
        items: List[Any], 
        process_func: Callable,
        batch_size: Optional[int] = None,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> List[Any]:
        """Process items in batches with concurrency control.
        
        Args:
            items: List of items to process
            process_func: Function to process each item
            batch_size: Size of each batch (auto-calculated if None)
            progress_callback: Optional callback for progress updates
        
        Returns:
            List of processed results
        """
        if self.monitor:
            self.monitor.start_monitoring()
        
        if batch_size is None:
            batch_size = max(1, len(items) // self.max_workers)
        
        # Split items into batches
        batches = [
            items[i:i + batch_size] 
            for i in range(0, len(items), batch_size)
        ]
        
        results = []
        completed = 0
        
        # Process batches concurrently
        async def process_batch_worker(batch: List[Any]) -> List[Any]:
            nonlocal completed
            
            async with self._semaphore:
                batch_results = []
                
                if asyncio.iscoroutinefunction(process_func):
                    # Async function
                    for item in batch:
                        try:
                            result = await process_func(item)
                            batch_results.append(result)
                        except Exception as e:
                            self.error_handler.handle_error(e)
                            batch_results.append(None)
                else:
                    # Sync function - run in executor
                    executor_class = ProcessPoolExecutor if self.use_process_pool else ThreadPoolExecutor
                    
                    with executor_class(max_workers=min(len(batch), self.max_workers)) as executor:
                        loop = asyncio.get_event_loop()
                        
                        for item in batch:
                            try:
                                result = await loop.run_in_executor(executor, process_func, item)
                                batch_results.append(result)
                            except Exception as e:
                                self.error_handler.handle_error(e)
                                batch_results.append(None)
                
                completed += len(batch)
                if progress_callback:
                    progress_callback(completed, len(items))
                
                return batch_results
        
        # Execute all batches
        batch_tasks = [process_batch_worker(batch) for batch in batches]
        batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
        
        # Flatten results
        for batch_result in batch_results:
            if isinstance(batch_result, Exception):
                self.error_handler.handle_error(batch_result)
            else:
                results.extend(batch_result)
        
        if self.monitor:
            self.monitor.stop_monitoring(len(batches))
        
        return results
    
    async def process_with_semaphore(
        self, 
        items: List[Any], 
        process_func: Callable,
        semaphore_limit: Optional[int] = None
    ) -> List[Any]:
        """Process items with semaphore-controlled concurrency.
        
        Args:
            items: List of items to process
            process_func: Function to process each item
            semaphore_limit: Custom semaphore limit (uses default if None)
        
        Returns:
            List of processed results
        """
        if semaphore_limit:
            semaphore = asyncio.Semaphore(semaphore_limit)
        else:
            semaphore = self._semaphore
        
        async def process_item_with_semaphore(item: Any) -> Any:
            async with semaphore:
                try:
                    if asyncio.iscoroutinefunction(process_func):
                        return await process_func(item)
                    else:
                        loop = asyncio.get_event_loop()
                        return await loop.run_in_executor(None, process_func, item)
                except Exception as e:
                    self.error_handler.handle_error(e)
                    return None
        
        tasks = [process_item_with_semaphore(item) for item in items]
        return await asyncio.gather(*tasks, return_exceptions=False)


class ResourceOptimizer:
    """Optimize resource usage during processing."""
    
    def __init__(self):
        self.error_handler = ErrorHandler("ResourceOptimizer")
        self._memory_threshold = 80  # Percentage
        self._cpu_threshold = 90     # Percentage
        
    def should_throttle(self) -> bool:
        """Check if processing should be throttled due to resource usage."""
        try:
            memory_percent = psutil.virtual_memory().percent
            cpu_percent = psutil.cpu_percent(interval=1)
            
            return (
                memory_percent > self._memory_threshold or 
                cpu_percent > self._cpu_threshold
            )
        except Exception as e:
            self.error_handler.handle_error(e)
            return False
    
    def get_resource_info(self) -> Dict[str, Any]:
        """Get current resource information."""
        try:
            memory = psutil.virtual_memory()
            cpu_percent = psutil.cpu_percent(interval=1)
            
            return {
                "memory": {
                    "total": memory.total / (1024 ** 3),  # GB
                    "available": memory.available / (1024 ** 3),  # GB
                    "percent": memory.percent,
                    "used": memory.used / (1024 ** 3)  # GB
                },
                "cpu": {
                    "percent": cpu_percent,
                    "count": psutil.cpu_count(logical=True),
                    "physical_count": psutil.cpu_count(logical=False)
                },
                "disk": {
                    "usage": psutil.disk_usage('/').percent
                }
            }
        except Exception as e:
            self.error_handler.handle_error(e)
            return {}
    
    async def adaptive_delay(self) -> None:
        """Add adaptive delay if resources are constrained."""
        if self.should_throttle():
            # Exponential backoff based on resource usage
            memory_percent = psutil.virtual_memory().percent
            delay = min(5.0, (memory_percent - self._memory_threshold) / 10)
            await asyncio.sleep(delay)
    
    def optimize_gc(self) -> None:
        """Optimize garbage collection."""
        try:
            # Force garbage collection
            collected = gc.collect()
            
            # Adjust GC thresholds based on memory usage
            memory_percent = psutil.virtual_memory().percent
            
            if memory_percent > 70:
                # More aggressive GC
                gc.set_threshold(100, 5, 5)
            else:
                # Normal GC
                gc.set_threshold(700, 10, 10)
                
        except Exception as e:
            self.error_handler.handle_error(e)


def performance_optimized(
    use_cache: bool = True,
    concurrent: bool = True,
    max_workers: Optional[int] = None,
    monitor: bool = True
):
    """Decorator for performance optimization.
    
    Args:
        use_cache: Enable result caching
        concurrent: Enable concurrent processing
        max_workers: Maximum concurrent workers
        monitor: Enable performance monitoring
    """
    def decorator(func: Callable) -> Callable:
        processor = ConcurrentProcessor(
            max_workers=max_workers,
            enable_monitoring=monitor
        ) if concurrent else None
        
        optimizer = ResourceOptimizer()
        
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            if monitor:
                monitor_instance = PerformanceMonitor()
                monitor_instance.start_monitoring()
            
            try:
                # Check if we should throttle
                await optimizer.adaptive_delay()
                
                # Execute function
                if processor and hasattr(func, '_batch_processing'):
                    # Handle batch processing
                    items = args[0] if args else []
                    result = await processor.process_batch(items, func, **kwargs)
                else:
                    result = await func(*args, **kwargs)
                
                # Optimize garbage collection
                optimizer.optimize_gc()
                
                return result
                
            finally:
                if monitor:
                    metrics = monitor_instance.stop_monitoring()
                    # Log metrics if needed
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # For synchronous functions, run in async context
            return asyncio.run(async_wrapper(*args, **kwargs))
        
        # Return appropriate wrapper
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


@asynccontextmanager
async def performance_context(
    enable_monitoring: bool = True,
    enable_optimization: bool = True
):
    """Context manager for performance monitoring and optimization."""
    monitor = PerformanceMonitor() if enable_monitoring else None
    optimizer = ResourceOptimizer() if enable_optimization else None
    
    if monitor:
        monitor.start_monitoring()
    
    try:
        yield {
            "monitor": monitor,
            "optimizer": optimizer
        }
    finally:
        if monitor:
            metrics = monitor.stop_monitoring()
            
        if optimizer:
            optimizer.optimize_gc()


# Global instances
global_processor = ConcurrentProcessor()
global_optimizer = ResourceOptimizer()