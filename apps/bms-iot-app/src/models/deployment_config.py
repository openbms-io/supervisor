from typing import Optional
from sqlmodel import SQLModel, Field, select
from sqlalchemy import JSON
from datetime import datetime, timezone
from pydantic import BaseModel

from src.network.sqlmodel_client import get_session, with_db_retry


class DeploymentConfig(BaseModel):
    """Pydantic model for deployment configuration data"""

    organization_id: str
    site_id: str
    device_id: str
    config_metadata: Optional[dict] = None


class DeploymentConfigModel(SQLModel, table=True):  # type: ignore[call-arg]
    """SQLModel table for storing deployment configuration"""

    __tablename__ = "deployment_config"

    id: Optional[int] = Field(default=None, primary_key=True)
    organization_id: str = Field(index=True)
    site_id: str = Field(index=True)
    device_id: str = Field(index=True)
    config_metadata: Optional[dict] = Field(default=None, sa_type=JSON)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


@with_db_retry(max_retries=3, base_delay=0.1)
async def set_deployment_config(config: DeploymentConfig) -> DeploymentConfigModel:
    """Set/update the deployment configuration (only keeps one record)"""
    async with get_session() as session:
        # Delete existing config (we only want one active config)
        existing_result = await session.execute(select(DeploymentConfigModel))
        existing_configs = existing_result.scalars().all()
        for existing_config in existing_configs:
            await session.delete(existing_config)

        # Create new config
        new_config = DeploymentConfigModel(
            organization_id=config.organization_id,
            site_id=config.site_id,
            device_id=config.device_id,
            config_metadata=config.config_metadata,
            updated_at=datetime.now(timezone.utc),
        )
        session.add(new_config)
        await session.commit()
        await session.refresh(new_config)
        return new_config


@with_db_retry(max_retries=3, base_delay=0.1)
async def get_current_deployment_config() -> Optional[DeploymentConfigModel]:
    """Get the current deployment configuration"""
    async with get_session() as session:
        result = await session.execute(
            select(DeploymentConfigModel).order_by(
                DeploymentConfigModel.created_at.desc()
            )  # type: ignore
        )
        config = result.scalars().first()
        return config


async def get_current_deployment_config_as_dict() -> Optional[dict]:
    """Get the current deployment configuration as a dictionary"""
    config = await get_current_deployment_config()
    if not config:
        return None

    return {
        "organization_id": config.organization_id,
        "site_id": config.site_id,
        "device_id": config.device_id,
        "config_metadata": config.config_metadata or {},
    }


def validate_deployment_config(config: DeploymentConfig) -> tuple[bool, list[str]]:
    """Validate deployment configuration and return (is_valid, error_messages)"""
    errors = []

    if not config.organization_id or not config.organization_id.strip():
        errors.append("organization_id is required and cannot be empty")

    if not config.site_id or not config.site_id.strip():
        errors.append("site_id is required and cannot be empty")

    if not config.device_id or not config.device_id.strip():
        errors.append("device_id is required and cannot be empty")

    # Validate organization_id format (should start with "org_")
    if config.organization_id and not config.organization_id.startswith("org_"):
        errors.append("organization_id should start with 'org_'")

    return len(errors) == 0, errors


async def has_valid_deployment_config() -> tuple[bool, list[str]]:
    """Check if a valid deployment configuration exists"""
    config = await get_current_deployment_config()
    if not config:
        return False, [
            "No deployment configuration found. Run 'config set' to configure."
        ]

    deployment_config = DeploymentConfig(
        organization_id=config.organization_id,
        site_id=config.site_id,
        device_id=config.device_id,
        config_metadata=config.config_metadata,
    )

    return validate_deployment_config(deployment_config)
