"""Main CLI interface for Fisher."""

import logging
import json
import sys
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

from fisher.data.models import SearchQuery, MarketplaceType
from fisher.data.collector import DataCollector
from fisher.analysis.analyzer import ProductAnalyzer
from fisher.config import config

# Set up logging
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

console = Console()


@click.group()
@click.version_option(version="0.1.0")
def cli():
    """
    Fisher - Marketplace Product Analysis Tool

    Identify popular products across eBay, Amazon, and Etsy.
    """
    pass


@cli.command()
@click.argument("keywords")
@click.option(
    "--marketplaces",
    "-m",
    default="",
    help="Comma-separated list of marketplaces (ebay,amazon,etsy). Default: all configured",
)
@click.option(
    "--category",
    "-c",
    default=None,
    help="Category filter",
)
@click.option(
    "--min-price",
    type=float,
    default=None,
    help="Minimum price filter",
)
@click.option(
    "--max-price",
    type=float,
    default=None,
    help="Maximum price filter",
)
@click.option(
    "--condition",
    type=click.Choice(["new", "used", "refurbished"], case_sensitive=False),
    default=None,
    help="Product condition filter",
)
@click.option(
    "--max-results",
    type=int,
    default=50,
    help="Maximum results per marketplace (default: 50)",
)
@click.option(
    "--sort-by",
    type=click.Choice(["relevance", "price_low", "price_high", "newest"], case_sensitive=False),
    default="relevance",
    help="Sort order (default: relevance)",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(),
    default=None,
    help="Output file path (JSON format)",
)
@click.option(
    "--top-n",
    type=int,
    default=20,
    help="Number of top products to display (default: 20)",
)
def search(
    keywords: str,
    marketplaces: str,
    category: Optional[str],
    min_price: Optional[float],
    max_price: Optional[float],
    condition: Optional[str],
    max_results: int,
    sort_by: str,
    output: Optional[str],
    top_n: int,
):
    """
    Search for products and analyze popularity.

    KEYWORDS: Search terms (e.g., "vintage watches")
    """
    console.print(f"\n[bold cyan]Fisher - Product Search[/bold cyan]")
    console.print(f"Keywords: [yellow]{keywords}[/yellow]\n")

    # Parse marketplaces
    if marketplaces:
        marketplace_list = [
            MarketplaceType(mp.strip().lower())
            for mp in marketplaces.split(",")
        ]
    else:
        # Use all configured marketplaces
        configured = config.get_configured_marketplaces()
        if not configured:
            console.print("[red]Error:[/red] No marketplace credentials configured.")
            console.print("Please set up API credentials in .env file.")
            sys.exit(1)
        marketplace_list = [MarketplaceType(mp) for mp in configured]

    console.print(f"Marketplaces: [green]{', '.join(mp.value for mp in marketplace_list)}[/green]\n")

    # Create search query
    query = SearchQuery(
        keywords=keywords,
        marketplaces=marketplace_list,
        category=category,
        min_price=min_price,
        max_price=max_price,
        condition=condition,
        max_results=max_results,
        sort_by=sort_by,
    )

    # Collect data
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Collecting product data...", total=None)

        with DataCollector() as collector:
            products = collector.collect(query, parallel=True)

        progress.update(task, completed=True)

    if not products:
        console.print("[yellow]No products found.[/yellow]")
        return

    console.print(f"\n[green]✓[/green] Collected {len(products)} products\n")

    # Analyze products
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Analyzing products...", total=None)

        analyzer = ProductAnalyzer()
        report = analyzer.analyze(products, query, top_n=top_n)

        progress.update(task, completed=True)

    # Display results
    _display_report(report, top_n)

    # Save to file if specified
    if output:
        _save_report(report, output, analyzer)
        console.print(f"\n[green]✓[/green] Report saved to: {output}")


@cli.command()
@click.option(
    "--marketplaces",
    "-m",
    default="",
    help="Comma-separated list of marketplaces to check (ebay,amazon,etsy)",
)
def status(marketplaces: str):
    """Check API configuration status."""
    console.print("\n[bold cyan]Fisher - Configuration Status[/bold cyan]\n")

    table = Table(title="Marketplace API Status")
    table.add_column("Marketplace", style="cyan")
    table.add_column("Status", style="bold")
    table.add_column("Details")

    # Check each marketplace
    marketplaces_to_check = ["ebay", "amazon", "etsy"]
    if marketplaces:
        marketplaces_to_check = [mp.strip().lower() for mp in marketplaces.split(",")]

    for marketplace in marketplaces_to_check:
        if marketplace == "ebay":
            is_valid = config.validate_ebay()
            details = f"App ID: {'✓' if config.EBAY_APP_ID else '✗'}"
        elif marketplace == "amazon":
            is_valid = config.validate_amazon()
            details = f"Access Key: {'✓' if config.AMAZON_ACCESS_KEY else '✗'}"
        elif marketplace == "etsy":
            is_valid = config.validate_etsy()
            details = f"API Key: {'✓' if config.ETSY_API_KEY else '✗'}"
        else:
            continue

        status_text = "[green]Configured ✓[/green]" if is_valid else "[red]Not Configured ✗[/red]"
        table.add_row(marketplace.upper(), status_text, details)

    console.print(table)
    console.print()


@cli.command()
@click.argument("product_id")
@click.option(
    "--marketplace",
    "-m",
    type=click.Choice(["ebay", "amazon", "etsy"], case_sensitive=False),
    required=True,
    help="Marketplace platform",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(),
    default=None,
    help="Output file path (JSON format)",
)
def details(product_id: str, marketplace: str, output: Optional[str]):
    """
    Get detailed information for a specific product.

    PRODUCT_ID: Product identifier (ASIN, listing ID, etc.)
    """
    console.print(f"\n[bold cyan]Fisher - Product Details[/bold cyan]")
    console.print(f"Product ID: [yellow]{product_id}[/yellow]")
    console.print(f"Marketplace: [green]{marketplace.upper()}[/green]\n")

    marketplace_type = MarketplaceType(marketplace.lower())

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Fetching product details...", total=None)

        with DataCollector() as collector:
            product = collector.get_product_details(marketplace_type, product_id)

        progress.update(task, completed=True)

    if not product:
        console.print("[red]Product not found.[/red]")
        return

    # Display product details
    _display_product_details(product)

    # Save to file if specified
    if output:
        with open(output, "w") as f:
            json.dump(product.model_dump(), f, indent=2, default=str)
        console.print(f"\n[green]✓[/green] Product details saved to: {output}")


def _display_report(report, top_n: int):
    """Display analysis report in terminal."""
    console.print("[bold cyan]Top Products by Popularity[/bold cyan]\n")

    # Create table
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Rank", style="dim", width=6)
    table.add_column("Title", style="white", width=40)
    table.add_column("Marketplace", style="cyan", width=12)
    table.add_column("Price", style="green", width=10)
    table.add_column("Score", style="yellow", width=8)

    for idx, product in enumerate(report.top_products[:top_n], 1):
        price_str = f"{product.currency} {product.price:.2f}" if product.price else "N/A"
        score_str = f"{product.metrics.popularity_score:.1f}" if product.metrics.popularity_score else "N/A"

        # Truncate title if too long
        title = product.title[:37] + "..." if len(product.title) > 40 else product.title

        table.add_row(
            str(idx),
            title,
            product.marketplace.value.upper(),
            price_str,
            score_str,
        )

    console.print(table)
    console.print()

    # Display insights
    _display_insights(report.insights)


def _display_insights(insights: dict):
    """Display analysis insights."""
    console.print("[bold cyan]Insights[/bold cyan]\n")

    # Price analysis
    if "price_analysis" in insights:
        price = insights["price_analysis"]
        console.print(f"[bold]Price Range:[/bold]")
        if price["min_price"] is not None:
            console.print(f"  Min: ${price['min_price']:.2f}")
            console.print(f"  Max: ${price['max_price']:.2f}")
            console.print(f"  Avg: ${price['avg_price']:.2f}")
            console.print(f"  Median: ${price['median_price']:.2f}\n")

    # Top categories
    if "top_categories" in insights and insights["top_categories"]:
        console.print(f"[bold]Top Categories:[/bold]")
        for category, count in list(insights["top_categories"].items())[:5]:
            console.print(f"  {category}: {count}")
        console.print()

    # Most popular product
    if "most_popular" in insights:
        mp = insights["most_popular"]
        console.print(f"[bold]Most Popular Product:[/bold]")
        console.print(f"  {mp['title']}")
        console.print(f"  Score: {mp['popularity_score']:.1f}")
        console.print()


def _display_product_details(product):
    """Display detailed product information."""
    console.print(f"[bold]Title:[/bold] {product.title}\n")

    if product.price:
        console.print(f"[bold]Price:[/bold] {product.currency} {product.price:.2f}")

    if product.category:
        console.print(f"[bold]Category:[/bold] {product.category}")

    if product.brand:
        console.print(f"[bold]Brand:[/bold] {product.brand}")

    if product.condition:
        console.print(f"[bold]Condition:[/bold] {product.condition}")

    if product.seller_name:
        console.print(f"[bold]Seller:[/bold] {product.seller_name}")

    console.print()

    # Metrics
    if any([
        product.metrics.sales_count,
        product.metrics.view_count,
        product.metrics.review_count,
        product.metrics.average_rating,
    ]):
        console.print("[bold cyan]Metrics:[/bold cyan]")

        if product.metrics.sales_count:
            console.print(f"  Sales: {product.metrics.sales_count}")

        if product.metrics.view_count:
            console.print(f"  Views: {product.metrics.view_count}")

        if product.metrics.review_count:
            console.print(f"  Reviews: {product.metrics.review_count}")

        if product.metrics.average_rating:
            console.print(f"  Rating: {product.metrics.average_rating:.1f}/5.0")

        console.print()

    if product.product_url:
        console.print(f"[bold]URL:[/bold] {product.product_url}\n")


def _save_report(report, output_path: str, analyzer: ProductAnalyzer):
    """Save analysis report to file."""
    report_dict = analyzer.export_to_dict(report)

    with open(output_path, "w") as f:
        json.dump(report_dict, f, indent=2, default=str)


if __name__ == "__main__":
    cli()
