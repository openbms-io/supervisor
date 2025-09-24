from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class DeploymentRuntimeConfig:
    """
    Runtime configuration for deployment settings.

    This is a read-only configuration object that holds the deployment
    settings loaded from the database. Using a frozen dataclass ensures
    immutability and type safety.
    """

    organization_id: str
    site_id: str
    device_id: str
    config_metadata: Optional[dict] = None

    def __post_init__(self):
        """Validate configuration values after initialization"""
        if not self.organization_id or not self.organization_id.strip():
            raise ValueError("organization_id cannot be empty")
        if not self.site_id or not self.site_id.strip():
            raise ValueError("site_id cannot be empty")
        if not self.device_id or not self.device_id.strip():
            raise ValueError("device_id cannot be empty")
