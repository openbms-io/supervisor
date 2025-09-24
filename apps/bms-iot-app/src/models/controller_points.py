from typing import Optional, Union
from sqlmodel import SQLModel, Field, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone
from sqlalchemy import Column, Computed, BigInteger

from src.models.bacnet_types import BacnetObjectTypeEnum
from src.network.sqlmodel_client import get_session, with_db_retry
from src.config.config import DEFAULT_CONTROLLER_PORT
from src.utils.logger import logger
from src.utils.performance import performance_metrics


class ControllerPointsModel(SQLModel, table=True):  # type: ignore[call-arg]
    __tablename__ = "controller_points"

    id: Optional[int] = Field(default=None, primary_key=True)
    controller_ip_address: str = Field(description="IP address of the controller")
    controller_port: int = Field(
        default=DEFAULT_CONTROLLER_PORT,
        description="Port of the controller, defaults to BACnet/IP standard port",
    )
    bacnet_object_type: BacnetObjectTypeEnum = Field(description="BACnet object type")
    point_id: int = Field(description="Point instance ID")
    iot_device_point_id: str = Field(
        description="iot_device_point_id for linking supabase"
    )
    controller_id: str = Field(description="Supabase controller_id")
    units: Optional[str] = Field(default=None, description="Units of the point")
    present_value: Union[str, None] = Field(description="Present value of the point")
    controller_device_id: str = Field(description="Device ID of the controller")
    is_uploaded: bool = Field(
        default=False, description="Whether the point has been uploaded"
    )
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # Health monitoring fields (stored as semicolon-separated strings for SQLite compatibility)
    status_flags: Optional[str] = Field(
        default=None,
        description="BACnet status flags as semicolon-separated string (e.g., 'fault;overridden')",
    )
    event_state: Optional[str] = Field(
        default=None,
        description="BACnet event state (e.g., 'normal', 'fault', 'offnormal')",
    )
    out_of_service: Optional[bool] = Field(
        default=None, description="BACnet out-of-service flag"
    )
    reliability: Optional[str] = Field(
        default=None,
        description="BACnet reliability (e.g., 'noFaultDetected', 'overRange')",
    )

    # ============================================================================
    # BACnet Optional Properties (24 additional properties)
    # ============================================================================

    # Value Limit Properties
    min_pres_value: Optional[float] = Field(
        default=None, description="Minimum present value allowed"
    )
    max_pres_value: Optional[float] = Field(
        default=None, description="Maximum present value allowed"
    )
    high_limit: Optional[float] = Field(
        default=None, description="High limit for alarm generation"
    )
    low_limit: Optional[float] = Field(
        default=None, description="Low limit for alarm generation"
    )
    resolution: Optional[float] = Field(
        default=None, description="Smallest recognizable change"
    )

    # Control Properties
    priority_array: Optional[str] = Field(
        default=None,
        description="JSON array of 16 priority values (nulls or Real values)",
    )
    relinquish_default: Optional[float] = Field(
        default=None, description="Default value when all priorities null"
    )

    # Notification Configuration Properties
    cov_increment: Optional[float] = Field(
        default=None, description="Change required to trigger COV notification"
    )
    time_delay: Optional[int] = Field(
        default=None, description="Seconds before transition to alarm"
    )
    time_delay_normal: Optional[int] = Field(
        default=None, description="Seconds before return to normal"
    )
    notification_class: Optional[int] = Field(
        default=None, description="Notification class identifier"
    )
    notify_type: Optional[str] = Field(
        default=None, description="Notification type enum: ALARM/EVENT"
    )
    deadband: Optional[float] = Field(
        default=None, description="Range for alarm condition clearing"
    )
    limit_enable: Optional[str] = Field(
        default=None, description="JSON with lowLimitEnable and highLimitEnable bits"
    )

    # Event Properties
    event_enable: Optional[str] = Field(
        default=None, description="JSON with toFault, toNormal, toOffnormal bits"
    )
    acked_transitions: Optional[str] = Field(
        default=None, description="JSON with acknowledgment status bits"
    )
    event_time_stamps: Optional[str] = Field(
        default=None, description="JSON array of 3 timestamps (ISO 8601 strings)"
    )
    event_message_texts: Optional[str] = Field(
        default=None, description="JSON array of 3 message strings"
    )
    event_message_texts_config: Optional[str] = Field(
        default=None, description="JSON array of 3 config strings"
    )

    # Algorithm Control Properties
    event_detection_enable: Optional[bool] = Field(
        default=None, description="Enable event detection"
    )
    event_algorithm_inhibit_ref: Optional[str] = Field(
        default=None,
        description="JSON with objectIdentifier, propertyIdentifier, arrayIndex",
    )
    event_algorithm_inhibit: Optional[bool] = Field(
        default=None, description="Inhibit event algorithm"
    )
    reliability_evaluation_inhibit: Optional[bool] = Field(
        default=None, description="Inhibit reliability evaluation"
    )

    error_info: Optional[str] = Field(
        default=None, description="Error information as JSON string"
    )
    created_at_unix_milli_timestamp: int = Field(
        sa_column=Column(
            "created_at_unix_milli_timestamp",
            BigInteger,
            Computed("(strftime('%s', created_at) * 1000)", persisted=True),
        ),
        description="Unix milli timestamp of the point",
    )


@with_db_retry(max_retries=3, base_delay=0.1)
async def insert_controller_point(
    point: ControllerPointsModel,
) -> ControllerPointsModel:
    async with get_session() as session:
        session.add(point)
        await session.commit()
        await session.refresh(point)
        return point


@performance_metrics("database_bulk_insert", {"count": "points"})
@with_db_retry(max_retries=5, base_delay=0.1)
async def bulk_insert_controller_points(
    points: list[ControllerPointsModel],
):
    """
    Insert multiple controller points with defensive error handling.

    Session Concurrency Fixes:
    - Defensive ID validation (prevents id=0 issues)
    - No refresh operations (eliminates session dependency issues)

    Args:
        points: List of ControllerPointsModel instances to insert

    Returns:
        List of inserted points (same instances, no fetch-after-insert)

    Performance Benefits:
        - Single database transaction instead of N transactions
        - Reduced SQLite lock contention
        - No unnecessary fetch-after-insert queries
        - Retry logic protects against transient database locks

    Reliability Benefits:
        - Eliminates InvalidRequestError from session detachment
        - Future-proof against id=0 issues
        - Simple, fast insert-only operation
    """
    if not points:
        logger.info("No points to insert, skipping bulk insert")
        return []

    logger.info(f"Bulk inserting {len(points)} controller points")

    async with get_session() as session:
        # Defensive ID validation (fix id=0 issue for future-proofing)
        for point in points:
            if point.id == 0:
                logger.warning(
                    f"Found point with id=0, setting to None: point_id={point.point_id}"
                )
                point.id = None

        # Add all points and commit
        session.add_all(points)
        await session.commit()

        logger.info(f"Successfully bulk inserted {len(points)} controller points")


@with_db_retry(max_retries=3, base_delay=0.05)
async def fetch_fresh_point(
    session: AsyncSession, point_id: int
) -> Optional[ControllerPointsModel]:
    """Fetch fresh point data by ID - no session dependency

    This replaces refresh operations to avoid session detachment issues.
    Based on Phase 5 analysis: InvalidRequestError occurs when objects
    become detached from their sessions.
    """
    return await session.get(ControllerPointsModel, point_id)


@with_db_retry(max_retries=3, base_delay=0.1)
async def get_controller_points_by_controller_id(
    controller_id: str,
) -> list[ControllerPointsModel]:
    async with get_session() as session:
        result = await session.execute(
            select(ControllerPointsModel).where(
                ControllerPointsModel.controller_id == controller_id
            )
        )
        return list(result.scalars().all())


@with_db_retry(max_retries=3, base_delay=0.1)
async def delete_uploaded_points() -> int:
    """Delete all controller points where is_uploaded is True. Returns the number of deleted rows."""
    async with get_session() as session:
        result = await session.execute(
            select(ControllerPointsModel).where(
                ControllerPointsModel.is_uploaded is True
            )
        )
        points_to_delete = list(result.scalars().all())
        deleted_count = len(points_to_delete)
        for point in points_to_delete:
            await session.delete(point)
        await session.commit()
        return deleted_count


@performance_metrics("database_mark_uploaded", {"count": "points"})
@with_db_retry(max_retries=3, base_delay=0.1)
async def mark_points_as_uploaded(points: list[ControllerPointsModel]):
    logger.info(f"Marking points as uploaded: {len(points)}")
    # Explicitly type as list[int] for mypy type safety
    ids: list[int] = [point.id for point in points if point.id is not None]
    if not ids:
        return

    # Ensure all IDs are integers (mypy type assertion)
    assert all(isinstance(id_val, int) for id_val in ids), "All IDs must be integers"

    async with get_session() as session:
        await session.execute(
            update(ControllerPointsModel)
            .where(ControllerPointsModel.id.in_(ids))  # type: ignore[union-attr]
            .values(is_uploaded=True)
        )
        await session.commit()


@with_db_retry(max_retries=3, base_delay=0.1)
async def get_points_to_upload() -> list[ControllerPointsModel]:
    """Fetch all controller points where is_uploaded is False."""
    async with get_session() as session:
        result = await session.execute(
            select(ControllerPointsModel)
            .where(ControllerPointsModel.is_uploaded is False)
            .order_by(ControllerPointsModel.created_at)
            .limit(100)  # type: ignore[arg-type]
        )
        return list(result.scalars().all())
