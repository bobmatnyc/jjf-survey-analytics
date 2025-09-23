"""
CLI commands for Hybrid Surveyor.

This module provides async CLI commands with rich output, progress tracking,
and comprehensive error handling.
"""

import asyncio
import click
import sys
from typing import List, Optional
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.table import Table
from rich.panel import Panel
from datetime import datetime

from dependency_injector.wiring import Provide, inject

from ..config.container import Container
from ..config.settings import Settings
from ..services.data_extraction_service import IDataExtractionService
from ..services.database_service import IDatabaseService
from ..models.domain import JobStatus
from ..core.exceptions import HybridSurveyorException

console = Console()


@click.command()
@click.pass_context
@inject
async def init_db(
    ctx: click.Context,
    database_service: IDatabaseService = Provide[Container.database_service]
) -> None:
    """Initialize the database schema."""
    try:
        with console.status("[bold green]Initializing database..."):
            await database_service.initialize()
        
        console.print("✅ [green]Database initialized successfully![/green]")
        
    except Exception as e:
        console.print(f"❌ [red]Database initialization failed: {e}[/red]")
        if ctx.obj['verbose']:
            console.print_exception()
        raise


@click.command()
@click.option('--urls', '-u', multiple=True, help='Specific URLs to extract (can be used multiple times)')
@click.option('--job-name', '-n', help='Name for the extraction job')
@click.option('--use-default-urls', '-d', is_flag=True, help='Use default configured URLs')
@click.option('--extract-only', is_flag=True, help='Extract data only, skip processing')
@click.option('--batch-size', '-b', type=int, help='Batch size for processing')
@click.pass_context
@inject
async def extract(
    ctx: click.Context,
    urls: tuple,
    job_name: Optional[str],
    use_default_urls: bool,
    extract_only: bool,
    batch_size: Optional[int],
    settings: Settings = Provide[Container.settings],
    extraction_service: IDataExtractionService = Provide[Container.data_extraction_service]
) -> None:
    """Extract data from Google Sheets."""
    
    # Determine which URLs to process
    urls_to_process = []
    
    if urls:
        urls_to_process.extend(urls)
    
    if use_default_urls or not urls:
        urls_to_process.extend([str(url) for url in settings.sheet_urls])
    
    if not urls_to_process:
        console.print("❌ [red]No URLs specified. Use --urls or --use-default-urls[/red]")
        return
    
    # Generate job name if not provided
    if not job_name:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        job_name = f"extraction_{timestamp}"
    
    try:
        console.print(f"🚀 [bold blue]Starting extraction job: {job_name}[/bold blue]")
        console.print(f"📊 Processing {len(urls_to_process)} spreadsheet(s)")
        
        if extract_only:
            console.print("ℹ️  [yellow]Extract-only mode: Data will not be processed[/yellow]")
        
        # Start extraction with progress tracking
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console
        ) as progress:
            
            # Create progress task
            task = progress.add_task("Extracting data...", total=100)
            
            # Start extraction
            job = await extraction_service.extract_and_process(
                sheet_urls=urls_to_process,
                job_name=job_name,
                extract_only=extract_only
            )
            
            # Monitor progress
            while job.status in [JobStatus.PENDING, JobStatus.RUNNING]:
                await asyncio.sleep(2)  # Check every 2 seconds
                
                # Get updated job status
                updated_job = await extraction_service.get_job_status(job.id)
                if updated_job:
                    job = updated_job
                    
                    # Update progress
                    progress_percent = job.progress_percentage
                    progress.update(
                        task,
                        completed=progress_percent,
                        description=f"Processing... ({job.processed_rows}/{job.total_rows} rows)"
                    )
        
        # Display results
        if job.status == JobStatus.COMPLETED:
            console.print("✅ [green]Extraction completed successfully![/green]")
            
            # Create results table
            table = Table(title="Extraction Results", show_header=True, header_style="bold magenta")
            table.add_column("Metric", style="cyan", no_wrap=True)
            table.add_column("Value", style="green")
            
            table.add_row("Job ID", job.id)
            table.add_row("Job Name", job.name)
            table.add_row("Spreadsheets Processed", f"{job.processed_spreadsheets}/{job.total_spreadsheets}")
            table.add_row("Worksheets Processed", f"{job.processed_worksheets}/{job.total_worksheets}")
            table.add_row("Rows Processed", f"{job.processed_rows}/{job.total_rows}")
            
            if job.duration:
                table.add_row("Duration", f"{job.duration:.2f} seconds")
            
            console.print(table)
            
        else:
            console.print(f"❌ [red]Extraction failed: {job.error_message}[/red]")
            console.print(f"Job ID: {job.id}")
            
    except Exception as e:
        console.print(f"❌ [red]Extraction failed: {e}[/red]")
        if ctx.obj['verbose']:
            console.print_exception()
        raise


@click.command()
@click.option('--batch-size', '-b', type=int, default=1000, help='Batch size for processing')
@click.pass_context
@inject
async def process(
    ctx: click.Context,
    batch_size: int,
    extraction_service: IDataExtractionService = Provide[Container.data_extraction_service]
) -> None:
    """Process previously extracted but unprocessed data."""
    
    try:
        console.print("🔄 [bold blue]Starting data processing...[/bold blue]")
        
        with console.status("[bold green]Processing unprocessed data..."):
            job = await extraction_service.process_unprocessed_data(batch_size=batch_size)
        
        if job.status == JobStatus.COMPLETED:
            console.print("✅ [green]Data processing completed successfully![/green]")
            console.print(f"Processed {job.records_processed} records")
            if job.records_failed > 0:
                console.print(f"⚠️  [yellow]{job.records_failed} records failed processing[/yellow]")
        else:
            console.print(f"❌ [red]Processing failed: {job.error_message}[/red]")
            
    except Exception as e:
        console.print(f"❌ [red]Processing failed: {e}[/red]")
        if ctx.obj['verbose']:
            console.print_exception()
        raise


@click.command()
@click.option('--limit', '-l', default=10, help='Number of recent jobs to show')
@click.option('--job-id', help='Show details for specific job ID')
@click.pass_context
@inject
async def status(
    ctx: click.Context,
    limit: int,
    job_id: Optional[str],
    extraction_service: IDataExtractionService = Provide[Container.data_extraction_service]
) -> None:
    """Show status of extraction jobs."""
    
    try:
        if job_id:
            # Show specific job details
            job = await extraction_service.get_job_status(job_id)
            if not job:
                console.print(f"❌ [red]Job not found: {job_id}[/red]")
                return
            
            # Display detailed job information
            status_color = {
                JobStatus.COMPLETED: "green",
                JobStatus.RUNNING: "blue",
                JobStatus.FAILED: "red",
                JobStatus.CANCELLED: "yellow",
                JobStatus.PENDING: "cyan"
            }.get(job.status, "white")
            
            panel_content = f"""
[bold]Job ID:[/bold] {job.id}
[bold]Name:[/bold] {job.name}
[bold]Status:[/bold] [{status_color}]{job.status.value}[/{status_color}]
[bold]Started:[/bold] {job.started_at}
[bold]Completed:[/bold] {job.completed_at or 'N/A'}
[bold]Progress:[/bold] {job.progress_percentage:.1f}%

[bold]Spreadsheets:[/bold] {job.processed_spreadsheets}/{job.total_spreadsheets}
[bold]Worksheets:[/bold] {job.processed_worksheets}/{job.total_worksheets}
[bold]Rows:[/bold] {job.processed_rows}/{job.total_rows}

[bold]Configuration:[/bold]
  Extract Only: {job.extract_only}
  Batch Size: {job.batch_size}
            """
            
            if job.error_message:
                panel_content += f"\n[bold red]Error:[/bold red] {job.error_message}"
            
            console.print(Panel(panel_content.strip(), title=f"Job Details: {job.name}"))
            
        else:
            # Show recent jobs list
            # This would require implementing a method to get recent jobs
            console.print(f"📋 [bold blue]Recent extraction jobs (last {limit}):[/bold blue]")
            
            # For now, show a placeholder message
            console.print("ℹ️  [yellow]Job listing not yet implemented. Use --job-id to view specific job details.[/yellow]")
            
    except Exception as e:
        console.print(f"❌ [red]Failed to get job status: {e}[/red]")
        if ctx.obj['verbose']:
            console.print_exception()
        raise
