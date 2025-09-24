"""
MQTT payload size monitoring for BACnet optional properties.

This module provides utilities to monitor MQTT payload sizes and warn about
large payloads that could impact network performance.
"""

import json
import sys
import logging
from typing import Dict, List, Any
from datetime import datetime

from src.config.bacnet_constants import LARGE_PAYLOAD_THRESHOLD_BYTES

logger = logging.getLogger(__name__)


class PayloadSizeMonitor:
    """Monitor MQTT payload sizes for optional properties."""

    def __init__(self) -> None:
        self.payload_sizes: List[Dict[str, Any]] = []
        self._max_history: int = 100

    def record_payload_size(
        self, payload: Any, property_count: int, has_optional_properties: bool = False
    ) -> None:
        """Record MQTT payload size metrics."""
        # Calculate payload size
        if isinstance(payload, (dict, list)):
            payload_json = json.dumps(payload)
            size_bytes = len(payload_json.encode("utf-8"))
        elif isinstance(payload, str):
            size_bytes = len(payload.encode("utf-8"))
        else:
            size_bytes = sys.getsizeof(payload)

        record = {
            "timestamp": datetime.now(),
            "size_bytes": size_bytes,
            "property_count": property_count,
            "has_optional_properties": has_optional_properties,
            "size_kb": round(size_bytes / 1024, 2),
        }

        self.payload_sizes.append(record)

        # Maintain history limit
        if len(self.payload_sizes) > self._max_history:
            self.payload_sizes = self.payload_sizes[-self._max_history :]

        # Log large payloads
        if size_bytes > LARGE_PAYLOAD_THRESHOLD_BYTES:
            logger.warning(
                f"Large MQTT payload: {record['size_kb']:.2f}KB with {property_count} properties "
                f"(optional: {has_optional_properties})"
            )

        logger.debug(
            f"MQTT payload: {record['size_kb']}KB, properties: {property_count}, "
            f"optional: {has_optional_properties}"
        )

    def get_payload_summary(self) -> Dict[str, Any]:
        """Get payload size summary statistics."""
        if not self.payload_sizes:
            return {"message": "No payload data available"}

        sizes = [p["size_bytes"] for p in self.payload_sizes]
        optional_payloads = [
            p for p in self.payload_sizes if p["has_optional_properties"]
        ]
        basic_payloads = [
            p for p in self.payload_sizes if not p["has_optional_properties"]
        ]

        summary = {
            "total_payloads": len(self.payload_sizes),
            "avg_size_kb": round(sum(sizes) / len(sizes) / 1024, 2),
            "max_size_kb": round(max(sizes) / 1024, 2),
            "min_size_kb": round(min(sizes) / 1024, 2),
            "large_payloads": len(
                [s for s in sizes if s > LARGE_PAYLOAD_THRESHOLD_BYTES]
            ),
        }

        if optional_payloads:
            opt_sizes = [p["size_bytes"] for p in optional_payloads]
            summary["with_optional_properties"] = {
                "count": len(optional_payloads),
                "avg_size_kb": round(sum(opt_sizes) / len(opt_sizes) / 1024, 2),
                "max_size_kb": round(max(opt_sizes) / 1024, 2),
            }

        if basic_payloads:
            basic_sizes = [p["size_bytes"] for p in basic_payloads]
            summary["basic_properties_only"] = {
                "count": len(basic_payloads),
                "avg_size_kb": round(sum(basic_sizes) / len(basic_sizes) / 1024, 2),
                "max_size_kb": round(max(basic_sizes) / 1024, 2),
            }

        return summary


# Global payload monitor instance
payload_monitor = PayloadSizeMonitor()
