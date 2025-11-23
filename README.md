# Fisher - Marketplace Product Analysis Tool

Fisher is a tool for identifying popular products across multiple e-commerce marketplaces including eBay, Amazon, and Etsy.

## Features

- **Multi-Marketplace Support**: Access eBay, Amazon, and Etsy APIs
- **Data Aggregation**: Collect and normalize product data from multiple sources
- **Popularity Analysis**: Analyze products based on:
  - Sales volume and velocity
  - Review counts and ratings
  - Price trends
  - Search ranking
  - Listing performance metrics

## Installation

```bash
pip install -r requirements.txt
```

## Configuration

Copy `.env.example` to `.env` and add your API credentials:

```bash
cp .env.example .env
```

Required API credentials:
- **eBay**: App ID, Cert ID, Dev ID
- **Amazon**: Access Key, Secret Key, Partner Tag
- **Etsy**: API Key, Shared Secret

## Usage

### Basic Search

```bash
python -m fisher search "vintage watches" --marketplaces ebay,etsy,amazon
```

### Analyze Category

```bash
python -m fisher analyze --category "Electronics" --marketplace ebay
```

### Generate Report

```bash
python -m fisher report --keywords "handmade jewelry" --output report.json
```

## Project Structure

```
fisher/
├── api/          # Marketplace API clients
├── data/         # Data collection and models
├── analysis/     # Analysis engine
└── utils/        # Helper utilities
```

## API Rate Limits

Be mindful of API rate limits for each platform:
- **eBay**: 5,000 calls/day (standard)
- **Amazon**: Varies by API type
- **Etsy**: 10,000 calls/day

## License

MIT
