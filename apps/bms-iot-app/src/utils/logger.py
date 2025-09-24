"""
Simple and reliable logging configuration using Loguru.
Captures ALL logs without infinite loops or configuration hell.
"""

import os
import sys
import logging
from loguru import logger

# Create logs directory
os.makedirs("logs", exist_ok=True)


class InterceptHandler(logging.Handler):
    """Handler to intercept standard logging calls and route them through Loguru."""

    def emit(self, record):
        # Get corresponding Loguru level if it exists
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Find caller from where originated the logged message
        frame, depth = logging.currentframe(), 2
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        # Create a bound logger with the original logger name to preserve it
        bound_logger = logger.bind(logger_name=record.name)
        bound_logger.opt(depth=depth, exception=record.exc_info).log(
            level, f"[{record.name}] {record.getMessage()}"
        )


def setup_logging():
    """Setup Loguru logging configuration."""

    # Remove default handler to avoid duplicate console output
    logger.remove()

    # 1. Console handler - show only app and BAC0 logs (filtered)
    def console_filter(record):
        """Filter console output to show only relevant logs."""
        logger_name = record["name"]

        # Allow these patterns
        allowed_patterns = [
            "src.",
            "BAC0.",
            "bacpypes3.",  # BACpypes3 library logs
            "async_tasks.",
            "__main__",
        ]

        # Block these patterns
        blocked_patterns = [
            "aiosqlite",
            "asyncio",
            "sqlalchemy",
            "pykka",
            "trio",
            "urllib3",
            "requests",
            "paho",
        ]

        # Check blocked patterns first
        for pattern in blocked_patterns:
            if logger_name.startswith(pattern):
                return False

        # Allow specific patterns
        for pattern in allowed_patterns:
            if logger_name.startswith(pattern):
                return True

        # Allow root logger warnings and errors only
        if logger_name == "root" and record["level"].no >= 30:  # WARNING and above
            return True

        return False

    logger.add(
        sys.stdout,
        format="{time:HH:mm:ss} - {name} - {level} - {message}",
        level="DEBUG",
        filter=console_filter,
        colorize=True,
    )

    # 2. Main log file - capture EVERYTHING
    logger.add(
        "logs/bms-iot-app-all.log",
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} - [{thread.name}] - {name} - {level} - {function}:{line} - {message}",
        level="DEBUG",
        rotation="50 MB",
        retention="10 days",
        compression="zip",
        enqueue=True,  # Thread-safe
        catch=True,  # Catch errors in logging itself
    )

    # 3. Error log file - errors only
    logger.add(
        "logs/bms-iot-app-errors.log",
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} - [{thread.name}] - {name} - {level} - {function}:{line} - {message}",
        level="ERROR",
        rotation="10 MB",
        retention="30 days",
        compression="zip",
        enqueue=True,
        catch=True,
    )

    # 4. Async tasks log - for monitoring specific async operations
    def async_filter(record):
        """Filter for async task logs."""
        logger_name = record["name"]
        thread_name = record["thread"].name
        func_name = record["function"]

        return (
            "async_tasks" in logger_name
            or "Task-" in thread_name
            or "async" in func_name.lower()
            or "monitor_loop" in func_name
            or "handle_messages_loop" in func_name
        )

    logger.add(
        "logs/async-tasks.log",
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} - [{thread.name}] - {name} - {level} - {function}:{line} - {message}",
        level="DEBUG",
        filter=async_filter,
        rotation="10 MB",
        retention="7 days",
        compression="zip",
        enqueue=True,
        catch=True,
    )

    # 5. BMS IoT App only - for clean app-level logs
    def app_only_filter(record):
        """Filter for BMS IoT app logs only."""
        logger_name = record["name"]

        # Include only our application code
        app_patterns = [
            "src.",
            "async_tasks.",
            "__main__",
        ]

        for pattern in app_patterns:
            if logger_name.startswith(pattern):
                return True

        return False

    logger.add(
        "logs/bms-iot-app-only.log",
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} - [{thread.name}] - {name} - {level} - {function}:{line} - {message}",
        level="DEBUG",
        filter=app_only_filter,
        rotation="25 MB",
        retention="14 days",
        compression="zip",
        enqueue=True,
        catch=True,
    )

    # Intercept standard library logging and route to Loguru
    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)
    logging.getLogger().handlers = [InterceptHandler()]

    # Set specific loggers to ensure they're captured
    # BAC0 logger configuration - INFO level for third-party
    bac0_logger = logging.getLogger("BAC0")
    bac0_logger.setLevel(logging.INFO)
    bac0_logger.handlers = [InterceptHandler()]
    bac0_logger.propagate = False

    # BACpypes3 logger configuration - INFO level for third-party
    bacpypes3_loggers = [
        "bacpypes3",  # Root BACpypes3 logger
        "bacpypes3.bvl",  # BACnet Virtual Link
        "bacpypes3.ipv4",  # IPv4 specific
        "bacpypes3.udp",  # UDP layer
        "bacpypes3.bvlpdu",  # BVLPDU layer
        "bacpypes3.npdu",  # Network PDU
        "bacpypes3.apdu",  # Application PDU
        "bacpypes3.app",  # Application layer
        "bacpypes3.appservice",  # Application services
        "bacpypes3.netservice",  # Network services
        "bacpypes3.comm",  # Communications
        "bacpypes3.task",  # Task management
        "bacpypes3.state_machine",  # State machines
    ]

    for logger_name in bacpypes3_loggers:
        bp3_logger = logging.getLogger(logger_name)
        bp3_logger.setLevel(logging.INFO)
        bp3_logger.handlers = [InterceptHandler()]
        bp3_logger.propagate = False

    # Other important third-party loggers - INFO level
    important_loggers = ["aiosqlite", "sqlalchemy", "asyncio", "paho", "urllib3"]
    for logger_name in important_loggers:
        third_party_logger = logging.getLogger(logger_name)
        third_party_logger.setLevel(logging.INFO)
        third_party_logger.handlers = [InterceptHandler()]
        third_party_logger.propagate = False

    # BMS IoT App loggers - DEBUG level for our code
    app_loggers = ["src", "async_tasks"]
    for logger_name in app_loggers:
        app_logger = logging.getLogger(logger_name)
        app_logger.setLevel(logging.DEBUG)
        app_logger.handlers = [InterceptHandler()]
        app_logger.propagate = False

    # Log successful initialization
    logger.info("=" * 60)
    logger.info("BMS IoT App Logging Initialized (Loguru)")
    logger.info("Main log: logs/bms-iot-app-all.log")
    logger.info("Error log: logs/bms-iot-app-errors.log")
    logger.info("Async log: logs/async-tasks.log")
    logger.info("App-only log: logs/bms-iot-app-only.log")
    logger.info("Standard logging interception: ENABLED")
    logger.info("BAC0 logging level: INFO")
    logger.info("BACpypes3 logging level: INFO")
    logger.info("=" * 60)


# Initialize logging immediately when module is imported
setup_logging()
