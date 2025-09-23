"""
Main CLI interface for Hybrid Surveyor.

This module provides a comprehensive command-line interface that combines
the best UX patterns from Surveyor with the processing capabilities of
sheets_processor.
"""

import asyncio
import click
import logging
import sys
from pathlib import Path
from typing import Optional
from rich.console import Console
from rich.logging import RichHandler
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from dependency_injector.wiring import Provide, inject

from ..config.container import Container, wire_container, unwire_container
from ..config.settings import Settings
from ..core.exceptions import HybridSurveyorException
from .. import __version__

# Initialize rich console for better output
console = Console()


def setup_logging(verbose: bool = False, structured: bool = False) -> None:
    """Set up logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    
    if structured:
        # Use structured logging
        import structlog
        structlog.configure(
            processors=[
                structlog.stdlib.filter_by_level,
                structlog.stdlib.add_logger_name,
                structlog.stdlib.add_log_level,
                structlog.stdlib.PositionalArgumentsFormatter(),
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.StackInfoRenderer(),
                structlog.processors.format_exc_info,
                structlog.processors.UnicodeDecoder(),
                structlog.processors.JSONRenderer()
            ],
            context_class=dict,
            logger_factory=structlog.stdlib.LoggerFactory(),
            wrapper_class=structlog.stdlib.BoundLogger,
            cache_logger_on_first_use=True,
        )
        logging.basicConfig(level=level, format="%(message)s")
    else:
        # Use rich logging for better console output
        logging.basicConfig(
            level=level,
            format="%(message)s",
            datefmt="[%X]",
            handlers=[RichHandler(console=console, rich_tracebacks=True)]
        )


@click.group()
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose logging')
@click.option('--structured-logs', is_flag=True, help='Enable structured JSON logging')
@click.option('--config-file', '-c', type=click.Path(exists=True), help='Configuration file path')
@click.pass_context
def cli(ctx: click.Context, verbose: bool, structured_logs: bool, config_file: Optional[str]) -> None:
    """
    🔍 Hybrid Surveyor - Advanced Google Sheets Data Extraction Tool
    
    Extract, transform, and normalize data from Google Spreadsheets with
    async processing, comprehensive error handling, and production-ready features.
    """
    # Ensure context object exists
    ctx.ensure_object(dict)
    
    # Set up logging
    setup_logging(verbose, structured_logs)
    
    # Store CLI options
    ctx.obj['verbose'] = verbose
    ctx.obj['structured_logs'] = structured_logs
    ctx.obj['config_file'] = config_file
    
    # Wire dependency injection
    wire_container()


@cli.command()
@click.pass_context
def version(ctx: click.Context) -> None:
    """Show version information."""
    console.print(f"[bold blue]Hybrid Surveyor[/bold blue] version [green]{__version__}[/green]")


@cli.command()
@click.pass_context
@inject
def config(
    ctx: click.Context,
    settings: Settings = Provide[Container.settings]
) -> None:
    """Show current configuration."""
    table = Table(title="Configuration", show_header=True, header_style="bold magenta")
    table.add_column("Setting", style="cyan", no_wrap=True)
    table.add_column("Value", style="green")
    
    # Application settings
    table.add_row("App Name", settings.app_name)
    table.add_row("App Version", settings.app_version)
    table.add_row("Debug Mode", str(settings.debug))
    
    # Database settings
    table.add_row("Database URL", settings.database.url.split("://")[0] + "://***")
    table.add_row("Database Echo", str(settings.database.echo))
    
    # Google Sheets settings
    creds_status = "✅ Configured" if settings.google_sheets.credentials_file else "❌ Not configured"
    table.add_row("Google Credentials", creds_status)
    table.add_row("Rate Limit", f"{settings.google_sheets.rate_limit_requests}/min")
    
    # Processing settings
    table.add_row("Batch Size", str(settings.processing.batch_size))
    table.add_row("Max Concurrent Jobs", str(settings.processing.max_concurrent_jobs))
    
    # Sheet URLs
    table.add_row("Default Sheet URLs", str(len(settings.sheet_urls)))
    
    console.print(table)


@cli.command()
@click.pass_context
@inject
def health(
    ctx: click.Context,
    health_checker = Provide[Container.health_checker]
) -> None:
    """Check system health and dependencies."""
    async def _check_health():
        with console.status("[bold green]Checking system health..."):
            health_status = await health_checker.check_health()
        
        # Display overall status
        status_color = {
            "healthy": "green",
            "warning": "yellow", 
            "unhealthy": "red"
        }.get(health_status["status"], "white")
        
        console.print(f"\n[bold {status_color}]System Status: {health_status['status'].upper()}[/bold {status_color}]")
        
        # Display summary
        summary = health_status["summary"]
        console.print(f"Total Checks: {summary['total_checks']}")
        console.print(f"[green]Passed: {summary['passed_checks']}[/green]")
        if summary['warning_checks'] > 0:
            console.print(f"[yellow]Warnings: {summary['warning_checks']}[/yellow]")
        if summary['failed_checks'] > 0:
            console.print(f"[red]Failed: {summary['failed_checks']}[/red]")
        
        # Display detailed results
        table = Table(title="Health Check Details", show_header=True, header_style="bold magenta")
        table.add_column("Component", style="cyan", no_wrap=True)
        table.add_column("Status", style="white")
        table.add_column("Details", style="dim")
        
        for check_name, result in health_status["checks"].items():
            status_icon = {
                "healthy": "✅",
                "warning": "⚠️",
                "unhealthy": "❌"
            }.get(result["status"], "❓")
            
            details = []
            if "response_time_seconds" in result:
                details.append(f"Response: {result['response_time_seconds']:.3f}s")
            if "error" in result:
                details.append(f"Error: {result['error']}")
            if "warnings" in result and result["warnings"]:
                details.extend(result["warnings"])
            
            table.add_row(
                check_name.replace("_", " ").title(),
                f"{status_icon} {result['status']}",
                "; ".join(details) if details else "OK"
            )
        
        console.print(table)
    
    # Run async health check
    try:
        asyncio.run(_check_health())
    except Exception as e:
        console.print(f"[red]Health check failed: {e}[/red]")
        if ctx.obj['verbose']:
            console.print_exception()
        sys.exit(1)


def main() -> None:
    """Main entry point for the CLI."""
    try:
        # Create and wire container
        container = Container()
        
        # Handle async commands by wrapping them
        def make_async_command(command_func):
            """Convert async command to sync for Click."""
            def sync_wrapper(*args, **kwargs):
                try:
                    return asyncio.run(command_func(*args, **kwargs))
                except KeyboardInterrupt:
                    console.print("\n[yellow]Operation cancelled by user[/yellow]")
                    sys.exit(1)
                except HybridSurveyorException as e:
                    console.print(f"[red]Error: {e}[/red]")
                    sys.exit(1)
                except Exception as e:
                    console.print(f"[red]Unexpected error: {e}[/red]")
                    sys.exit(1)
            return sync_wrapper
        
        # Import and add async commands
        from .commands import extract, process, status, init_db
        
        # Wrap async commands
        cli.add_command(click.command()(make_async_command(extract)))
        cli.add_command(click.command()(make_async_command(process)))
        cli.add_command(click.command()(make_async_command(status)))
        cli.add_command(click.command()(make_async_command(init_db)))
        
        # Run CLI
        cli()
        
    except Exception as e:
        console.print(f"[red]Fatal error: {e}[/red]")
        sys.exit(1)
    finally:
        # Clean up
        try:
            unwire_container()
        except:
            pass


if __name__ == '__main__':
    main()
