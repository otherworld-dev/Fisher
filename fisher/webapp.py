"""Flask web application for Fisher."""

import json
import logging
from typing import Optional

from flask import Flask, render_template, request, jsonify
from fisher.data.models import SearchQuery, MarketplaceType
from fisher.data.collector import DataCollector
from fisher.analysis.analyzer import ProductAnalyzer
from fisher.config import config

app = Flask(__name__)
app.config['SECRET_KEY'] = 'fisher-marketplace-analysis-tool'

logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@app.route('/')
def index():
    """Render the main page."""
    return render_template('index.html')


@app.route('/api/status')
def api_status():
    """Get API configuration status."""
    status = {
        'ebay': {
            'configured': config.validate_ebay(),
            'has_app_id': bool(config.EBAY_APP_ID),
        },
        'amazon': {
            'configured': config.validate_amazon(),
            'has_access_key': bool(config.AMAZON_ACCESS_KEY),
        },
        'etsy': {
            'configured': config.validate_etsy(),
            'has_api_key': bool(config.ETSY_API_KEY),
        }
    }

    configured_marketplaces = config.get_configured_marketplaces()

    return jsonify({
        'status': status,
        'configured_marketplaces': configured_marketplaces
    })


@app.route('/api/search', methods=['POST'])
def api_search():
    """Search for products and return analysis."""
    try:
        data = request.json

        # Extract parameters
        keywords = data.get('keywords', '').strip()
        if not keywords:
            return jsonify({'error': 'Keywords are required'}), 400

        # Parse marketplaces
        marketplace_str = data.get('marketplaces', '')
        if marketplace_str:
            marketplace_list = [
                MarketplaceType(mp.strip().lower())
                for mp in marketplace_str.split(',')
            ]
        else:
            configured = config.get_configured_marketplaces()
            if not configured:
                return jsonify({'error': 'No marketplace credentials configured'}), 400
            marketplace_list = [MarketplaceType(mp) for mp in configured]

        # Create search query
        query = SearchQuery(
            keywords=keywords,
            marketplaces=marketplace_list,
            category=data.get('category') or None,
            min_price=data.get('min_price') or None,
            max_price=data.get('max_price') or None,
            condition=data.get('condition') or None,
            max_results=data.get('max_results', 50),
            sort_by=data.get('sort_by', 'relevance'),
        )

        # Collect data
        logger.info(f"Starting search for: {keywords}")
        with DataCollector() as collector:
            products = collector.collect(query, parallel=True)

        if not products:
            return jsonify({
                'products': [],
                'total': 0,
                'message': 'No products found'
            })

        logger.info(f"Collected {len(products)} products")

        # Analyze products
        analyzer = ProductAnalyzer()
        top_n = data.get('top_n', 50)
        report = analyzer.analyze(products, query, top_n=top_n)

        # Convert to dict for JSON response
        report_dict = analyzer.export_to_dict(report)

        return jsonify({
            'success': True,
            'total': len(products),
            'report': report_dict
        })

    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Search error: {str(e)}", exc_info=True)
        return jsonify({'error': f'Search failed: {str(e)}'}), 500


@app.route('/api/product/<marketplace>/<product_id>')
def api_product_details(marketplace: str, product_id: str):
    """Get detailed information for a specific product."""
    try:
        marketplace_type = MarketplaceType(marketplace.lower())

        with DataCollector() as collector:
            product = collector.get_product_details(marketplace_type, product_id)

        if not product:
            return jsonify({'error': 'Product not found'}), 404

        return jsonify({
            'success': True,
            'product': product.model_dump()
        })

    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Product details error: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500


def run_webapp(host='127.0.0.1', port=5000, debug=False):
    """Run the Flask web application."""
    app.run(host=host, port=port, debug=debug)


if __name__ == '__main__':
    run_webapp(debug=True)
