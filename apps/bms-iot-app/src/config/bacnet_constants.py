"""
BACnet Protocol Constants and Configuration Values.

This module contains constants used throughout the BMS IoT application for
BACnet protocol compliance and performance configuration.
"""

# BACnet Array Sizes (from BACnet Protocol Specification)
PRIORITY_ARRAY_SIZE = 16  # BACnet priority array has 16 elements (priorities 1-16)
EVENT_ARRAY_SIZE = (
    3  # BACnet event arrays have 3 elements (toOffnormal, toFault, toNormal)
)

# MQTT Performance Thresholds
LARGE_PAYLOAD_THRESHOLD_BYTES = (
    10240  # 10KB - threshold for large MQTT payload warnings
)
LARGE_PAYLOAD_THRESHOLD_KB = 10.0  # 10KB - same threshold in KB for display

# SQLite Performance Configuration
SQLITE_CACHE_SIZE_PAGES = 10000  # Number of pages for SQLite cache optimization
