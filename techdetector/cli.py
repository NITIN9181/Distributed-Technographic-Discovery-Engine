"""
Rich CLI for TechDetector.

Commands:
  scan <url>              Scan single domain
  scan-batch <file>       Scan multiple domains from file
  query                   Query database
  export                  Export data to JSON/CSV
  init-db                 Initialize database
  stats                   Show scanning statistics
"""

import asyncio
import logging
import click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn
from rich.table import Table

from techdetector.config import load_config
from techdetector.scanner import init_database, perform_scan
from techdetector.batch_scanner import scan_batch, BatchConfig, ScanProgress
from techdetector.storage import (
    query_by_technology,
    query_by_vector,
    get_all_companies,
    query_detections,
)
from techdetector.export import export_json, export_csv
from techdetector.models import DetectionVector
from techdetector.orchestrator import Orchestrator

console = Console()


@click.group()
def cli():
    """TechDetector - Distributed Technographic Discovery Engine"""
    logging.basicConfig(
        level=logging.ERROR
    )  # Suppress normal logs for beautiful output
    load_config()


@cli.command()
@click.argument("url")
@click.option("--vectors", default="all", help="Comma-separated: html,headers,dns,jobs")
def scan(url: str, vectors: str):
    """Scan a single domain for technologies."""
    if vectors == "all":
        vec_list = ["html", "headers", "dns", "job_posting"]
    else:
        vec_list = [v.strip() for v in vectors.split(",")]

    with console.status(f"[bold green]Scanning {url}..."):
        result = perform_scan(url, vec_list)

    console.print(f"\n[bold blue]Scan Results for: {result.domain}[/]")
    console.print(
        f"Scanned at: {result.scan_timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}"
    )
    console.print("-" * 40)

    if not result.detections:
        console.print("[yellow]No technologies detected.[/]")
        return

    for d in result.detections:
        console.print(
            f"[green]OK[/] [bold]{d.technology.name:<25}[/] [{d.technology.category}] ({d.vector.value})"
        )


@cli.command("scan-batch")
@click.argument("filepath", type=click.Path(exists=True))
@click.option("--concurrency", "-c", default=10, help="Max concurrent scans")
@click.option("--rate", "-r", default=2.0, help="Max requests/sec per domain")
@click.option("--no-robots", is_flag=True, help="Ignore robots.txt")
@click.option("--force", "-f", is_flag=True, help="Re-scan even if recent")
def scan_batch_cmd(filepath, concurrency, rate, no_robots, force):
    """
    Scan multiple domains from a file (one domain per line).

    Shows real-time progress with ETA.
    """
    with open(filepath, "r") as f:
        domains = [
            line.strip() for line in f if line.strip() and not line.startswith("#")
        ]

    if not domains:
        console.print("[red]No domains found in file.[/]")
        return

    config = BatchConfig(
        max_concurrent=concurrency,
        max_per_domain=rate,
        respect_robots=not no_robots,
        skip_recent=not force,
    )

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TextColumn("({task.completed}/{task.total})"),
        console=console,
    ) as progress:
        task = progress.add_task("[cyan]Scanning domains...", total=len(domains))

        def update_progress(p: ScanProgress):
            desc = f"[cyan]Scanning...[/] [white]{p.current_domain or ''}[/]"
            progress.update(task, completed=p.completed, description=desc)

        summary = asyncio.run(scan_batch(domains, config, update_progress))

    console.print("\n[bold green]Batch Scan Complete![/]")
    console.print(f"Total: {summary['total']}")
    console.print(f"[green]Successful: {summary['successful']}[/]")
    console.print(f"[red]Failed: {summary['failed']}[/]")
    console.print(f"[yellow]Skipped: {summary['skipped']}[/]")


@cli.command()
@click.option("--tech", help="Query by technology ID (e.g., snowflake)")
@click.option("--vector", help="Query by vector (e.g., JOB_POSTING_NLP)")
def query(tech, vector):
    """Query stored results."""
    if tech:
        res = query_by_technology(tech)
    elif vector:
        v_name = vector.upper()
        if v_name == "JOB_POSTING":
            v_name = "JOB_POSTING_NLP"
        try:
            vec = DetectionVector[v_name]
            res = query_by_vector(vec)
        except KeyError:
            console.print(f"[red]Invalid vector {v_name}[/]")
            return
    else:
        console.print("[red]Must specify --tech or --vector[/]")
        return

    if not res:
        console.print("[yellow]No results found.[/]")
        return

    table = Table(title="Query Results")
    table.add_column("Domain", style="cyan")
    table.add_column("Technology", style="magenta")
    table.add_column("Vector", style="green")
    table.add_column("Last Verified")

    for r in res:
        v = r.get("last_verified_at", r.get("first_detected_at", ""))
        table.add_row(
            r["canonical_domain"], r["technology_id"], r["detection_vector"], str(v)
        )

    console.print(table)


@cli.command()
@click.option("--format", "-f", type=click.Choice(["json", "csv"]), default="json")
@click.option("--output", "-o", type=click.Path(), required=True)
@click.option("--tech", help="Filter by technology ID")
@click.option("--vector", help="Filter by detection vector")
@click.option("--since", help="Only detections since date (YYYY-MM-DD)")
def export(format, output, tech, vector, since):
    """Export detection data to file."""
    filters = {}
    if tech:
        filters["tech"] = tech
    if vector:
        filters["vector"] = vector
    if since:
        filters["since"] = since

    with console.status("[bold green]Exporting data..."):
        if format == "json":
            export_json(output, filters)
        else:
            export_csv(output, filters)

    console.print(f"[bold green]OK[/] Exported to {output}")


@cli.command("init-db")
def init_db_cmd():
    """Initialize the database."""
    init_database()
    console.print("[bold green]OK[/] Database initialized successfully.")


@cli.command()
@click.argument("filepath", type=click.Path(exists=True))
@click.option("--force", "-f", is_flag=True, help="Ignore recency check")
def enqueue(filepath: str, force: bool):
    """Enqueue domains for distributed crawling."""
    config = load_config()
    orchestrator = Orchestrator(config.redis_url, config.database_url)

    with open(filepath) as f:
        domains = [line.strip() for line in f if line.strip()]

    result = orchestrator.enqueue(domains, force=force)
    console.print(f"[green]Enqueued: {result['enqueued']}[/green]")
    console.print(f"[yellow]Skipped: {result['skipped']}[/yellow]")


@cli.command()
def status():
    """Show distributed crawl status."""
    config = load_config()
    orchestrator = Orchestrator(config.redis_url, config.database_url)
    stats = orchestrator.get_queue_stats()

    table = Table(title="Crawl Status")
    table.add_column("Metric")
    table.add_column("Value")
    for k, v in stats.items():
        table.add_row(k.replace("_", " ").title(), str(v))
    console.print(table)


@cli.command()
def stats():
    """Show database statistics."""
    companies = get_all_companies()
    all_detections = query_detections({})

    table = Table(title="TechDetector Statistics")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="magenta")

    table.add_row("Total Companies Scanned", str(len(companies)))
    table.add_row("Total Detections", str(len(all_detections)))

    vec_counts = {}
    tech_counts = {}
    for d in all_detections:
        vec = d.get("detection_vector")
        tech = d.get("technology_id")
        vec_counts[vec] = vec_counts.get(vec, 0) + 1
        tech_counts[tech] = tech_counts.get(tech, 0) + 1

    console.print(table)

    vec_table = Table(title="Detections by Vector")
    vec_table.add_column("Vector", style="green")
    vec_table.add_column("Count")
    for k, v in sorted(vec_counts.items(), key=lambda item: item[1], reverse=True):
        vec_table.add_row(str(k), str(v))
    console.print(vec_table)

    top_tech_table = Table(title="Top 10 Technologies")
    top_tech_table.add_column("Technology", style="yellow")
    top_tech_table.add_column("Count")
    for k, v in sorted(tech_counts.items(), key=lambda item: item[1], reverse=True)[
        :10
    ]:
        top_tech_table.add_row(str(k), str(v))
    console.print(top_tech_table)


if __name__ == "__main__":
    cli()
