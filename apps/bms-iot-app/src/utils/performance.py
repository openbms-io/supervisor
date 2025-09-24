"""
Performance metrics decorator for timing and logging function execution.

This module provides a generic decorator that can be applied to any function
to measure execution time and log performance metrics with consistent formatting.
"""

import time
import functools
import asyncio
from typing import Any, Callable, Optional
from src.utils.logger import logger


def performance_metrics(operation_type: str, context_keys: Optional[dict] = None):
    """
    Generic decorator to measure and log performance metrics for any function.

    Args:
        operation_type: Type of operation (e.g., "bulk_read", "database_insert", "api_call")
        context_keys: Dict mapping log field names to function parameter names
                     e.g., {"device": "device_ip", "count": "point_requests"}

    Usage:
        @performance_metrics("bacnet_bulk_read", {"device": "device_ip", "count": "point_requests"})
        async def read_multiple_points(device_ip: str, point_requests: list):
            # function implementation

        # Logs: [PERF_METRICS] bacnet_bulk_read | function=read_multiple_points | duration_ms=245.67 | device=192.168.1.100 | count=15 | avg_per_item_ms=16.38
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            start_time = time.perf_counter()
            func_name = func.__name__

            # Extract context from function parameters
            context = {}
            if context_keys:
                for log_key, param_key in context_keys.items():
                    value = kwargs.get(param_key)
                    if value is not None:
                        # Handle lists/collections by getting length
                        if hasattr(value, "__len__") and not isinstance(value, str):
                            context[log_key] = len(value)
                        else:
                            context[log_key] = value

            try:
                result = await func(*args, **kwargs)
                end_time = time.perf_counter()
                duration_ms = (end_time - start_time) * 1000

                # Build performance log message
                log_parts = [
                    f"[PERF_METRICS] {operation_type}",
                    f"function={func_name}",
                    f"duration_ms={duration_ms:.2f}",
                ]

                # Add context information
                for key, value in context.items():
                    log_parts.append(f"{key}={value}")

                # Add result size if applicable
                if result is not None and hasattr(result, "__len__"):
                    log_parts.append(f"result_count={len(result)}")

                # Calculate per-item timing if we have a count
                if "count" in context and context["count"] > 0:
                    log_parts.append(
                        f"avg_per_item_ms={duration_ms / context['count']:.2f}"
                    )

                logger.info(" | ".join(log_parts))
                return result

            except Exception as e:
                end_time = time.perf_counter()
                duration_ms = (end_time - start_time) * 1000

                log_parts = [
                    f"[PERF_METRICS] {operation_type}_FAILED",
                    f"function={func_name}",
                    f"duration_ms={duration_ms:.2f}",
                    f"error={type(e).__name__}",
                ]

                # Add context even for failures
                for key, value in context.items():
                    log_parts.append(f"{key}={value}")

                logger.error(" | ".join(log_parts))
                raise

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            start_time = time.perf_counter()
            func_name = func.__name__

            # Extract context from function parameters
            context = {}
            if context_keys:
                for log_key, param_key in context_keys.items():
                    value = kwargs.get(param_key)
                    if value is not None:
                        if hasattr(value, "__len__") and not isinstance(value, str):
                            context[log_key] = len(value)
                        else:
                            context[log_key] = value

            try:
                result = func(*args, **kwargs)
                end_time = time.perf_counter()
                duration_ms = (end_time - start_time) * 1000

                log_parts = [
                    f"[PERF_METRICS] {operation_type}",
                    f"function={func_name}",
                    f"duration_ms={duration_ms:.2f}",
                ]

                for key, value in context.items():
                    log_parts.append(f"{key}={value}")

                if result is not None and hasattr(result, "__len__"):
                    log_parts.append(f"result_count={len(result)}")

                if "count" in context and context["count"] > 0:
                    log_parts.append(
                        f"avg_per_item_ms={duration_ms / context['count']:.2f}"
                    )

                logger.info(" | ".join(log_parts))
                return result

            except Exception as e:
                end_time = time.perf_counter()
                duration_ms = (end_time - start_time) * 1000

                log_parts = [
                    f"[PERF_METRICS] {operation_type}_FAILED",
                    f"function={func_name}",
                    f"duration_ms={duration_ms:.2f}",
                    f"error={type(e).__name__}",
                ]

                for key, value in context.items():
                    log_parts.append(f"{key}={value}")

                logger.error(" | ".join(log_parts))
                raise

        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper

    return decorator
