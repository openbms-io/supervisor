"""Credentials management module."""

import json
from pathlib import Path
from pydantic import BaseModel
from rich.console import Console
from ..config.paths import get_credentials_file

# Path to credentials file
CREDENTIALS_FILE = Path(get_credentials_file())


class Credentials(BaseModel):
    """Credentials model for authentication."""

    client_id: str
    secret_key: str


def ensure_credentials_dir():
    """Ensure the credentials directory exists."""
    CREDENTIALS_FILE.parent.mkdir(parents=True, exist_ok=True)


def save_credentials(client_id: str, secret_key: str) -> None:
    """Save credentials to file.

    Args:
        client_id: Client ID for authentication
        secret_key: Secret key for authentication

    Raises:
        Exception: If there's an error saving the credentials
    """
    console = Console()
    try:
        ensure_credentials_dir()
        credentials = Credentials(client_id=client_id, secret_key=secret_key)

        # Save credentials to file
        with open(CREDENTIALS_FILE, "w") as f:
            json.dump(credentials.model_dump(), f, indent=2)

        console.print("[green]Credentials saved successfully![/]")
    except Exception as e:
        console.print(f"[red]Error saving credentials: {str(e)}[/]")
        raise
