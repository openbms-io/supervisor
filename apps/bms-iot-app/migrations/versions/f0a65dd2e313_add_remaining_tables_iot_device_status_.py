"""add remaining tables: iot_device_status, bacnet_config, bacnet_readers

Revision ID: f0a65dd2e313
Revises: dc3c962443cb
Create Date: 2025-08-22 16:33:15.368689

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = "f0a65dd2e313"
down_revision: Union[str, Sequence[str], None] = "dc3c962443cb"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create remaining tables that were previously created manually

    # Create iot_device_status table
    op.create_table(
        "iot_device_status",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("iot_device_id", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column(
            "organization_id", sqlmodel.sql.sqltypes.AutoString(), nullable=False
        ),
        sa.Column("site_id", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column(
            "monitoring_status",
            sa.Enum(
                "ACTIVE", "STOPPED", "PAUSED", "ERROR", name="monitoringstatusenum"
            ),
            nullable=True,
        ),
        sa.Column(
            "mqtt_connection_status",
            sa.Enum(
                "CONNECTED",
                "DISCONNECTED",
                "CONNECTING",
                "ERROR",
                name="connectionstatusenum",
            ),
            nullable=True,
        ),
        sa.Column(
            "bacnet_connection_status",
            sa.Enum(
                "CONNECTED",
                "DISCONNECTED",
                "CONNECTING",
                "ERROR",
                name="connectionstatusenum",
            ),
            nullable=True,
        ),
        sa.Column("cpu_usage_percent", sa.Float(), nullable=True),
        sa.Column("memory_usage_percent", sa.Float(), nullable=True),
        sa.Column("disk_usage_percent", sa.Float(), nullable=True),
        sa.Column("temperature_celsius", sa.Float(), nullable=True),
        sa.Column("uptime_seconds", sa.Integer(), nullable=True),
        sa.Column("load_average", sa.Float(), nullable=True),
        sa.Column("bacnet_devices_connected", sa.Integer(), nullable=True),
        sa.Column("bacnet_points_monitored", sa.Integer(), nullable=True),
        sa.Column("payload", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("received_at", sa.DateTime(), nullable=False),
        sa.Column(
            "created_at_unix_milli_timestamp",
            sa.BigInteger(),
            sa.Computed("(strftime('%s', created_at) * 1000)", persisted=True),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("iot_device_id"),
    )
    op.create_index(
        op.f("ix_iot_device_status_iot_device_id"),
        "iot_device_status",
        ["iot_device_id"],
        unique=False,
    )

    # Create bacnet_config table
    op.create_table(
        "bacnet_config",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("bacnet_devices", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create bacnet_readers table
    op.create_table(
        "bacnet_readers",
        sa.Column("id", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("iot_device_id", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("ip_address", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("subnet_mask", sa.Integer(), nullable=False),
        sa.Column("bacnet_device_id", sa.Integer(), nullable=False),
        sa.Column("port", sa.Integer(), nullable=False),
        sa.Column("bbmd_enabled", sa.Boolean(), nullable=False),
        sa.Column("bbmd_server_ip", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column(
            "connection_status", sqlmodel.sql.sqltypes.AutoString(), nullable=True
        ),
        sa.Column("last_connected_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_bacnet_readers_iot_device_id"),
        "bacnet_readers",
        ["iot_device_id"],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Drop the tables that were created in upgrade
    op.drop_index(op.f("ix_bacnet_readers_iot_device_id"), table_name="bacnet_readers")
    op.drop_table("bacnet_readers")
    op.drop_table("bacnet_config")
    op.drop_index(
        op.f("ix_iot_device_status_iot_device_id"), table_name="iot_device_status"
    )
    op.drop_table("iot_device_status")
