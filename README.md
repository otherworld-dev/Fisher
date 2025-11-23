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
- **Web Interface**: Modern, user-friendly web GUI for easy product searching and analysis
- **CLI Interface**: Powerful command-line interface for automation and scripting

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

Fisher offers two interfaces: a modern web GUI and a powerful CLI.

### Web Interface (Recommended for New Users)

Start the web application:

```bash
python run_webapp.py
```

Then open your browser to: `http://127.0.0.1:5000`

The web interface provides:
- Interactive search form with all filters
- Real-time product analysis
- Visual insights and metrics
- Easy export to JSON
- API status dashboard

**Optional arguments:**
```bash
python run_webapp.py --host 0.0.0.0 --port 8080 --debug
```

### Command Line Interface (CLI)

#### Basic Search

```bash
python -m fisher search "vintage watches" --marketplaces ebay,etsy,amazon
```

#### Check API Status

```bash
python -m fisher status
```

#### Get Product Details

```bash
python -m fisher details PRODUCT_ID --marketplace ebay
```

For more CLI options, see `python -m fisher --help`

## Project Structure

```
fisher/
├── api/          # Marketplace API clients
├── data/         # Data collection and models
├── analysis/     # Analysis engine
├── utils/        # Helper utilities
├── webapp.py     # Flask web application
├── templates/    # HTML templates
└── static/       # CSS and JavaScript files
```

## API Rate Limits

Be mindful of API rate limits for each platform:
- **eBay**: 5,000 calls/day (standard)
- **Amazon**: Varies by API type
- **Etsy**: 10,000 calls/day

## License

MIT
