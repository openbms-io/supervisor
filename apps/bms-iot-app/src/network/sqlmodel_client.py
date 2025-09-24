from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy import text
from ..config.paths import get_database_url
from ..config.bacnet_constants import SQLITE_CACHE_SIZE_PAGES
import asyncio
import logging
import contextlib
from functools import wraps
import sys
import tempfile
import os
from collections import defaultdict
from typing import DefaultDict

logger = logging.getLogger(__name__)

# Use test database if running under pytest
if "pytest" in sys.modules or "PYTEST_CURRENT_TEST" in os.environ:
    # Create temporary test database for pytest
    test_db_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    test_db_path = test_db_file.name
    test_db_file.close()
    DATABASE_URL = f"sqlite+aiosqlite:///{test_db_path}"
    logger.info(f"Using test database: {test_db_path}")
else:
    DATABASE_URL = get_database_url()
    logger.info(f"Using production database: {DATABASE_URL}")

# SQLite-specific connection arguments for concurrency
connect_args = {
    "timeout": 30,  # 30 second timeout for database locks
    "isolation_level": None,  # Autocommit mode for better concurrency
    "check_same_thread": False,  # Allow multi-thread access
}

# Create engine with SQLite optimizations
engine = create_async_engine(
    DATABASE_URL,
    connect_args=connect_args,
    poolclass=None,  # Use NullPool for SQLite - no connection pooling
    pool_pre_ping=True,  # Verify connections before use
    echo=False,
    future=True,
)

async_session = async_sessionmaker(
    bind=engine, class_=AsyncSession, expire_on_commit=False
)


async def enable_wal_mode():
    """Enable Write-Ahead Logging for better SQLite concurrency"""
    async with engine.begin() as conn:
        await conn.execute(text("PRAGMA journal_mode=WAL;"))
        await conn.execute(
            text("PRAGMA synchronous=NORMAL;")
        )  # Balance safety/performance
        await conn.execute(text("PRAGMA busy_timeout=30000;"))  # 30 second timeout
        await conn.execute(
            text("PRAGMA temp_store=MEMORY;")
        )  # Use memory for temp tables
        await conn.execute(
            text(f"PRAGMA cache_size={SQLITE_CACHE_SIZE_PAGES};")
        )  # Increase cache size
        await conn.execute(text("PRAGMA mmap_size=268435456;"))  # 256MB memory map

    logger.info("SQLite WAL mode and performance optimizations enabled")


async def verify_database_connectivity():
    """Verify database connectivity"""
    try:
        async with get_session() as session:
            # Simple connectivity test
            result = await session.execute(text("SELECT 1"))
            result.fetchone()
        logger.info("Database connectivity verification passed")
    except Exception as e:
        logger.error(f"Database connectivity verification failed: {e}")
        raise


async def initialize_database():
    """Initialize database with optimal SQLite settings"""

    # Configure SQLite for concurrency
    await enable_wal_mode()

    # Verify database connectivity
    await verify_database_connectivity()


def get_engine():
    return engine


def _is_retryable_error(error: Exception) -> bool:
    """Determine if an error is retryable"""
    error_msg = str(error).lower()
    error_type = type(error).__name__.lower()

    # Phase 5: NON-RETRYABLE SESSION STATE ERRORS (check first)
    non_retryable_patterns = [
        "could not refresh instance",  # Session refresh on detached object
        "invalidrequesterror",  # General SQLAlchemy request errors
        "is not persistent within this session",  # Detached object errors
        "object is not bound to a session",  # Detached object errors
        "object is already attached to session",  # Session attachment conflicts
    ]

    # Return False immediately for non-retryable session state errors
    if any(pattern in error_msg for pattern in non_retryable_patterns):
        logger.info(
            f"Database error marked as NON-retryable (session state issue): {error_type}: {error_msg[:200]}"
        )
        return False

    retryable_patterns = [
        "database is locked",
        "database table is locked",
        "sqlite3.operationalerror",
        "connection was invalidated",
        "cannot operate on a closed database",  # Raspberry Pi specific
        "disk i/o error",  # SD card issues on Raspberry Pi
        "database file is encrypted or is not a database",
        "attempt to write a readonly database",
        "no such table",  # Transient during table creation
        "interrupted",  # System interrupt during operation
    ]

    # Check for SQLAlchemy-specific patterns
    sqlalchemy_patterns = [
        "this connection is on a different thread",
        "connection pool exhausted",
        "pool timeout",
    ]

    # SQLAlchemy 2.0+ concurrency error patterns
    sqlalchemy_concurrency_patterns = [
        "illegalstatechangeerror",  # Session concurrency violation
        "this session's transaction has been rolled back",  # Transaction rollback
        "session is already begun",  # Session state violation
        "session is not in a transaction",  # Transaction state error
        "concurrent access",  # Generic concurrent access error
        "session has been closed",  # Session lifecycle error
        "greenlet_spawn has not been called",  # Async context violation
    ]

    is_retryable = (
        any(pattern in error_msg for pattern in retryable_patterns)
        or any(pattern in error_msg for pattern in sqlalchemy_patterns)
        or any(pattern in error_msg for pattern in sqlalchemy_concurrency_patterns)
        or any(
            keyword in error_type
            for keyword in [
                "operationalerror",
                "databaseerror",
                "illegalstatechangeerror",
            ]
        )
    )

    # Log error analysis for debugging
    if is_retryable:
        logger.info(
            f"Database error marked as retryable: {error_type}: {error_msg[:200]}"
        )
    else:
        logger.warning(
            f"Database error marked as non-retryable: {error_type}: {error_msg[:200]}"
        )

    return is_retryable


def with_db_retry(max_retries=3, base_delay=0.1):
    """Decorator to add retry logic to database operations with enhanced logging"""

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            operation_name = func.__name__
            logger.debug(f"Starting database operation: {operation_name}")

            for attempt in range(max_retries + 1):
                try:
                    result = await func(*args, **kwargs)

                    if attempt > 0:
                        logger.info(
                            f"✅ Database operation {operation_name} succeeded after {attempt + 1} attempts"
                        )
                    else:
                        logger.debug(
                            f"Database operation {operation_name} succeeded on first attempt"
                        )

                    return result

                except Exception as e:
                    error_type = type(e).__name__

                    if _is_retryable_error(e) and attempt < max_retries:
                        delay = base_delay * (2**attempt)
                        logger.warning(
                            f"🔄 DB operation {operation_name} failed (attempt {attempt + 1}/{max_retries + 1}), "
                            f"retrying in {delay:.3f}s. Error: {error_type}: {str(e)[:200]}"
                        )
                        await asyncio.sleep(delay)
                    else:
                        if attempt > 0:
                            logger.error(
                                f"❌ Database operation {operation_name} failed permanently after {attempt + 1} attempts. "
                                f"Final error: {error_type}: {str(e)[:200]}"
                            )
                        else:
                            logger.error(
                                f"❌ Database operation {operation_name} failed with non-retryable error: "
                                f"{error_type}: {str(e)[:200]}"
                            )
                        raise

        return wrapper

    return decorator


def get_session_metrics() -> dict:
    """Get current session usage metrics for monitoring"""
    return dict(session_metrics)


def log_session_metrics():
    """Log current session metrics - useful for debugging"""
    metrics = get_session_metrics()
    logger.info(
        f"📊 Session Metrics - Active: {metrics['active_sessions']}, "
        f"Total Created: {metrics['total_sessions']}"
    )


# Session usage tracking for monitoring
session_metrics: DefaultDict[str, int] = defaultdict(int)


@contextlib.asynccontextmanager
async def get_session():
    """Session manager with comprehensive logging and monitoring"""
    session_id = None
    session_metrics["total_sessions"] += 1
    session_metrics["active_sessions"] += 1

    try:
        async with async_session() as session:
            session_id = id(session)
            logger.debug(
                f"Created new database session {session_id} (active: {session_metrics['active_sessions']})"
            )

            # Log warning if high concurrent sessions
            if session_metrics["active_sessions"] > 20:
                logger.warning(
                    f"High concurrent database sessions detected: {session_metrics['active_sessions']} active, "
                    f"{session_metrics['total_sessions']} total created"
                )

            yield session
            logger.debug(f"Database session {session_id} completed successfully")

    except Exception as e:
        error_type = type(e).__name__
        logger.error(
            f"Database session {session_id} failed with {error_type}: {str(e)[:200]}"
        )

        # Special handling for session concurrency errors
        if "illegalstatechangeerror" in str(e).lower():
            logger.error(
                f"❌ SQLAlchemy session concurrency violation detected! "
                f"This indicates session sharing across concurrent tasks. "
                f"Session {session_id}, Active sessions: {session_metrics['active_sessions']}"
            )

        raise
    finally:
        session_metrics["active_sessions"] -= 1
        if session_id:
            logger.debug(
                f"Cleaned up database session {session_id} (remaining active: {session_metrics['active_sessions']})"
            )
