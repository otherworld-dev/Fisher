"""Product analysis engine."""

import logging
from typing import List, Dict, Any, Optional
from collections import Counter, defaultdict

from fisher.data.models import Product, AnalysisReport, SearchQuery, MarketplaceType
from fisher.analysis.metrics import (
    rank_products_by_popularity,
    calculate_price_competitiveness,
    enrich_product_metrics,
)

logger = logging.getLogger(__name__)


class ProductAnalyzer:
    """Analyzes product data to identify trends and popular items."""

    def __init__(self):
        """Initialize product analyzer."""
        pass

    def analyze(
        self, products: List[Product], query: SearchQuery, top_n: int = 20
    ) -> AnalysisReport:
        """
        Perform comprehensive analysis on product data.

        Args:
            products: List of products to analyze
            query: Original search query
            top_n: Number of top products to include in report

        Returns:
            Analysis report with insights
        """
        logger.info(f"Analyzing {len(products)} products")

        if not products:
            return AnalysisReport(
                query=query,
                total_products=0,
                top_products=[],
                insights={
                    "error": "No products to analyze"
                },
            )

        # Rank products by popularity
        ranked_products = rank_products_by_popularity(products)
        top_products = ranked_products[:top_n]

        # Generate insights
        insights = self._generate_insights(products, ranked_products)

        report = AnalysisReport(
            query=query,
            total_products=len(products),
            top_products=top_products,
            insights=insights,
        )

        logger.info(f"Analysis complete. Top product: {top_products[0].title if top_products else 'N/A'}")
        return report

    def _generate_insights(
        self, products: List[Product], ranked_products: List[Product]
    ) -> Dict[str, Any]:
        """Generate insights from product data."""
        insights = {}

        # Price analysis
        insights["price_analysis"] = calculate_price_competitiveness(products)

        # Marketplace distribution
        marketplace_counts = Counter(p.marketplace for p in products)
        insights["marketplace_distribution"] = dict(marketplace_counts)

        # Category analysis
        category_counts = Counter(
            p.category for p in products if p.category
        )
        insights["top_categories"] = dict(category_counts.most_common(10))

        # Brand analysis
        brand_counts = Counter(p.brand for p in products if p.brand)
        insights["top_brands"] = dict(brand_counts.most_common(10))

        # Condition analysis
        condition_counts = Counter(p.condition for p in products if p.condition)
        insights["condition_distribution"] = dict(condition_counts)

        # Rating analysis
        rated_products = [
            p for p in products
            if p.metrics.average_rating is not None
        ]
        if rated_products:
            avg_rating = sum(p.metrics.average_rating for p in rated_products) / len(rated_products)
            insights["average_rating"] = round(avg_rating, 2)

        # Popularity insights
        if ranked_products:
            top_product = ranked_products[0]
            insights["most_popular"] = {
                "title": top_product.title,
                "marketplace": top_product.marketplace,
                "popularity_score": top_product.metrics.popularity_score,
                "price": top_product.price,
            }

            # Calculate average popularity score
            popularity_scores = [
                p.metrics.popularity_score
                for p in ranked_products
                if p.metrics.popularity_score is not None
            ]
            if popularity_scores:
                insights["avg_popularity_score"] = round(
                    sum(popularity_scores) / len(popularity_scores), 2
                )

        # Price vs popularity correlation
        insights["price_ranges"] = self._analyze_price_ranges(ranked_products)

        return insights

    def _analyze_price_ranges(self, products: List[Product]) -> Dict[str, Any]:
        """Analyze popularity across different price ranges."""
        price_ranges = {
            "under_25": [],
            "25_50": [],
            "50_100": [],
            "100_250": [],
            "over_250": [],
        }

        for product in products:
            if product.price is None:
                continue

            if product.price < 25:
                price_ranges["under_25"].append(product)
            elif product.price < 50:
                price_ranges["25_50"].append(product)
            elif product.price < 100:
                price_ranges["50_100"].append(product)
            elif product.price < 250:
                price_ranges["100_250"].append(product)
            else:
                price_ranges["over_250"].append(product)

        # Calculate average popularity for each range
        range_stats = {}
        for range_name, range_products in price_ranges.items():
            if not range_products:
                continue

            popularity_scores = [
                p.metrics.popularity_score
                for p in range_products
                if p.metrics.popularity_score is not None
            ]

            if popularity_scores:
                range_stats[range_name] = {
                    "count": len(range_products),
                    "avg_popularity": round(sum(popularity_scores) / len(popularity_scores), 2),
                }

        return range_stats

    def compare_marketplaces(self, products: List[Product]) -> Dict[str, Any]:
        """
        Compare performance across different marketplaces.

        Args:
            products: List of products to analyze

        Returns:
            Dictionary with marketplace comparison data
        """
        marketplace_data = defaultdict(list)

        # Group products by marketplace
        for product in products:
            marketplace_data[product.marketplace].append(product)

        comparison = {}

        for marketplace, mp_products in marketplace_data.items():
            # Calculate statistics for this marketplace
            prices = [p.price for p in mp_products if p.price is not None]
            popularity_scores = [
                p.metrics.popularity_score
                for p in mp_products
                if p.metrics.popularity_score is not None
            ]

            comparison[marketplace.value] = {
                "product_count": len(mp_products),
                "avg_price": round(sum(prices) / len(prices), 2) if prices else None,
                "avg_popularity": round(sum(popularity_scores) / len(popularity_scores), 2)
                if popularity_scores else None,
            }

        return comparison

    def identify_trending_products(
        self, products: List[Product], min_velocity: float = 1.0
    ) -> List[Product]:
        """
        Identify trending products based on sales velocity.

        Args:
            products: List of products to analyze
            min_velocity: Minimum velocity score to be considered trending

        Returns:
            List of trending products
        """
        trending = []

        for product in products:
            # Enrich product metrics
            enriched = enrich_product_metrics(product)

            if enriched.metrics.velocity_score and enriched.metrics.velocity_score >= min_velocity:
                trending.append(enriched)

        # Sort by velocity score
        trending.sort(key=lambda p: p.metrics.velocity_score or 0, reverse=True)

        logger.info(f"Found {len(trending)} trending products")
        return trending

    def export_to_dict(self, report: AnalysisReport) -> Dict[str, Any]:
        """
        Export analysis report to dictionary format.

        Args:
            report: Analysis report to export

        Returns:
            Dictionary representation
        """
        return {
            "query": {
                "keywords": report.query.keywords,
                "marketplaces": [mp.value for mp in report.query.marketplaces],
                "category": report.query.category,
            },
            "total_products": report.total_products,
            "top_products": [
                {
                    "title": p.title,
                    "marketplace": p.marketplace.value,
                    "price": p.price,
                    "currency": p.currency,
                    "category": p.category,
                    "popularity_score": p.metrics.popularity_score,
                    "product_url": p.product_url,
                }
                for p in report.top_products
            ],
            "insights": report.insights,
            "generated_at": report.generated_at.isoformat(),
        }
