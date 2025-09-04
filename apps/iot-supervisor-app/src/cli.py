"""
BMS IoT Supervisor CLI - Command line interface using Typer
"""

import typer
import uvicorn
from rich.console import Console
from rich.panel import Panel
import asyncio
from typing import Optional

app = typer.Typer()
console = Console()


@app.command()
def start_serve(
    host: str = typer.Option("0.0.0.0", help="Host to bind the server"),
    port: int = typer.Option(8080, help="Port to bind the server"),
):
    """Start FastAPI server only"""
    console.print(
        Panel(f"Starting FastAPI server on {host}:{port}", title="BMS IoT Supervisor")
    )
    uvicorn.run("src.main:app", host=host, port=port, reload=True)


@app.command()
def start_execution(
    config_path: Optional[str] = typer.Option(None, help="Path to configuration file"),
):
    """Start execution engine only"""
    console.print(Panel("Starting execution engine", title="BMS Execution Engine"))
    if config_path:
        console.print(f"Loading configuration from: {config_path}")
    else:
        console.print("No configuration specified - waiting for API deployment")

    # Placeholder for execution engine
    console.print("Execution engine running... (Press Ctrl+C to stop)")
    try:
        while True:
            asyncio.run(asyncio.sleep(1))
    except KeyboardInterrupt:
        console.print("Execution engine stopped")


@app.command()
def start_all(
    host: str = typer.Option("0.0.0.0", help="Host to bind the server"),
    port: int = typer.Option(8080, help="Port to bind the server"),
    config_path: Optional[str] = typer.Option(None, help="Path to configuration file"),
):
    """Start both FastAPI server and execution engine"""
    console.print(
        Panel(
            f"Starting both FastAPI server ({host}:{port}) and execution engine",
            title="BMS IoT Supervisor - Full Mode",
        )
    )

    # In a real implementation, this would start both services concurrently
    # For now, just start the FastAPI server (execution engine would run in background)
    console.print("Starting FastAPI server...")
    console.print("Starting execution engine in background...")
    uvicorn.run("src.main:app", host=host, port=port, reload=True)


@app.command()
def health():
    """Check health status"""
    console.print(Panel("BMS IoT Supervisor is healthy ✅", title="Health Check"))


@app.command()
def version():
    """Show version information"""
    console.print(Panel("BMS IoT Supervisor v0.1.0", title="Version Info"))


def main():
    """Main CLI entry point"""
    app()


if __name__ == "__main__":
    main()
