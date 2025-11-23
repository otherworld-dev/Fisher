# Fisher Usage Guide

This guide provides detailed instructions for using Fisher to analyze marketplace products.

## Quick Start

### 1. Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Or install in development mode
pip install -e .
```

### 2. Configuration

Copy the example environment file and add your API credentials:

```bash
cp .env.example .env
```

Edit `.env` and add your API credentials for the marketplaces you want to use.

### 3. Check Configuration

Verify your API credentials are configured correctly:

```bash
python -m fisher status
```

## Commands

### Search for Products

Search across multiple marketplaces and analyze popularity:

```bash
# Basic search
python -m fisher search "vintage watches"

# Search specific marketplaces
python -m fisher search "handmade jewelry" --marketplaces etsy,ebay

# Search with filters
python -m fisher search "laptop" \
  --marketplaces amazon,ebay \
  --min-price 500 \
  --max-price 1500 \
  --condition new \
  --category Electronics

# Save results to file
python -m fisher search "gaming console" --output report.json

# Get more results
python -m fisher search "coffee maker" --max-results 100 --top-n 50
```

### Get Product Details

Fetch detailed information for a specific product:

```bash
# eBay product
python -m fisher details 123456789 --marketplace ebay

# Amazon product (ASIN)
python -m fisher details B08N5WRWNW --marketplace amazon

# Etsy listing
python -m fisher details 987654321 --marketplace etsy

# Save details to file
python -m fisher details B08N5WRWNW --marketplace amazon --output product.json
```

### Check Status

View configuration status for all marketplaces:

```bash
# Check all marketplaces
python -m fisher status

# Check specific marketplace
python -m fisher status --marketplaces ebay
```

## Command Options

### Search Options

- `--marketplaces, -m`: Comma-separated list of marketplaces (ebay, amazon, etsy)
- `--category, -c`: Category filter
- `--min-price`: Minimum price filter
- `--max-price`: Maximum price filter
- `--condition`: Product condition (new, used, refurbished)
- `--max-results`: Maximum results per marketplace (default: 50)
- `--sort-by`: Sort order (relevance, price_low, price_high, newest)
- `--output, -o`: Output file path (JSON format)
- `--top-n`: Number of top products to display (default: 20)

### Details Options

- `--marketplace, -m`: Marketplace platform (required)
- `--output, -o`: Output file path (JSON format)

## Examples

### Find Popular Products in a Niche

```bash
python -m fisher search "mechanical keyboard" \
  --marketplaces amazon,ebay \
  --min-price 50 \
  --max-price 200 \
  --max-results 100 \
  --output keyboards.json
```

### Compare Prices Across Marketplaces

```bash
python -m fisher search "iPhone 14 Pro" \
  --marketplaces ebay,amazon \
  --condition new \
  --max-results 50
```

### Find Trending Etsy Products

```bash
python -m fisher search "minimalist wall art" \
  --marketplaces etsy \
  --max-results 100 \
  --sort-by newest
```

### Analyze Product Category

```bash
python -m fisher search "vintage" \
  --marketplaces etsy \
  --category "Home & Living" \
  --max-results 200 \
  --top-n 30
```

## Understanding the Output

### Popularity Score

Fisher calculates a popularity score (0-100) based on:

- **Sales count** (30%): Number of items sold
- **View count** (20%): Product page views
- **Review metrics** (25%): Number and quality of reviews
- **Favorites count** (15%): Watchers/favorites
- **Search rank** (10%): Position in search results

Higher scores indicate more popular products.

### Analysis Report

The analysis report includes:

1. **Top Products**: Ranked by popularity score
2. **Price Analysis**: Min, max, average, and median prices
3. **Category Distribution**: Most common categories
4. **Brand Analysis**: Top brands
5. **Marketplace Comparison**: Performance across platforms

### Report Structure (JSON)

```json
{
  "query": {
    "keywords": "search terms",
    "marketplaces": ["ebay", "amazon"],
    "category": null
  },
  "total_products": 150,
  "top_products": [
    {
      "title": "Product Name",
      "marketplace": "ebay",
      "price": 29.99,
      "currency": "USD",
      "popularity_score": 85.5,
      "product_url": "https://..."
    }
  ],
  "insights": {
    "price_analysis": {
      "min_price": 15.00,
      "max_price": 299.99,
      "avg_price": 67.45
    },
    "top_categories": {
      "Electronics": 45,
      "Home & Garden": 32
    }
  }
}
```

## Tips

1. **Start with broad searches**: Use general keywords to get an overview
2. **Refine with filters**: Use price and category filters to narrow results
3. **Compare marketplaces**: Search across multiple platforms to find best opportunities
4. **Save reports**: Use `--output` to save results for later analysis
5. **Check configuration**: Run `fisher status` if you encounter API errors

## API Rate Limits

Be mindful of API rate limits:

- **eBay**: 5,000 calls/day (standard tier)
- **Amazon**: Varies by product type (typically 1-10 requests/second)
- **Etsy**: 10,000 calls/day

Fisher includes rate limiting to help manage these constraints.

## Troubleshooting

### "No marketplace credentials configured"

Make sure you've set up your API credentials in the `.env` file.

### "API authentication failed"

Verify your API credentials are correct and active.

### "Rate limit exceeded"

Wait a few minutes before making more requests. Consider reducing `--max-results`.

### Empty results

Try:
- Broadening your search keywords
- Removing or relaxing filters
- Checking if the category exists on that marketplace

## Advanced Usage

### Using Fisher as a Python Library

```python
from fisher.data.models import SearchQuery, MarketplaceType
from fisher.data.collector import DataCollector
from fisher.analysis.analyzer import ProductAnalyzer

# Create search query
query = SearchQuery(
    keywords="vintage watches",
    marketplaces=[MarketplaceType.EBAY, MarketplaceType.ETSY],
    max_results=50
)

# Collect data
with DataCollector() as collector:
    products = collector.collect(query)

# Analyze
analyzer = ProductAnalyzer()
report = analyzer.analyze(products, query)

# Access results
for product in report.top_products:
    print(f"{product.title}: {product.metrics.popularity_score}")
```

## Getting Help

```bash
# General help
python -m fisher --help

# Command-specific help
python -m fisher search --help
python -m fisher details --help
python -m fisher status --help
```
