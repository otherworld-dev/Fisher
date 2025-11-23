"""Metrics calculation for product popularity analysis."""

import logging
from typing import List, Optional
import numpy as np

from fisher.data.models import Product, ProductMetrics

logger = logging.getLogger(__name__)


def calculate_popularity_score(product: Product) -> float:
    """
    Calculate a normalized popularity score for a product.

    The score is based on multiple factors:
    - Sales count (if available)
    - View count
    - Review count and average rating
    - Favorites/watchers count
    - Search ranking position

    Args:
        product: Product to analyze

    Returns:
        Popularity score (0-100)
    """
    metrics = product.metrics
    score = 0.0
    weights_sum = 0.0

    # Sales count (weight: 0.30)
    if metrics.sales_count is not None:
        sales_score = min(metrics.sales_count / 1000, 1.0) * 100
        score += sales_score * 0.30
        weights_sum += 0.30

    # View count (weight: 0.20)
    if metrics.view_count is not None:
        view_score = min(metrics.view_count / 10000, 1.0) * 100
        score += view_score * 0.20
        weights_sum += 0.20

    # Review metrics (weight: 0.25)
    if metrics.review_count is not None:
        review_count_score = min(metrics.review_count / 500, 1.0) * 100

        if metrics.average_rating is not None:
            # Combine review count and rating
            rating_score = (metrics.average_rating / 5.0) * 100
            combined_review_score = (review_count_score * 0.6 + rating_score * 0.4)
            score += combined_review_score * 0.25
        else:
            score += review_count_score * 0.25

        weights_sum += 0.25

    # Favorites count (weight: 0.15)
    if metrics.favorites_count is not None:
        favorites_score = min(metrics.favorites_count / 500, 1.0) * 100
        score += favorites_score * 0.15
        weights_sum += 0.15

    # Search ranking (weight: 0.10)
    if metrics.search_rank is not None:
        # Lower rank (closer to 1) is better
        rank_score = max(0, 100 - (metrics.search_rank * 2))
        score += rank_score * 0.10
        weights_sum += 0.10

    # Normalize by actual weights used
    if weights_sum > 0:
        normalized_score = score / weights_sum
    else:
        normalized_score = 0.0

    return round(normalized_score, 2)


def calculate_velocity_score(product: Product) -> float:
    """
    Calculate sales velocity score (sales per day).

    Args:
        product: Product to analyze

    Returns:
        Velocity score representing sales per day
    """
    metrics = product.metrics

    if metrics.sales_count is None or metrics.listing_age_days is None:
        return 0.0

    if metrics.listing_age_days == 0:
        return 0.0

    velocity = metrics.sales_count / metrics.listing_age_days
    return round(velocity, 2)


def calculate_engagement_rate(product: Product) -> float:
    """
    Calculate engagement rate (interactions per view).

    Args:
        product: Product to analyze

    Returns:
        Engagement rate as percentage
    """
    metrics = product.metrics

    if metrics.view_count is None or metrics.view_count == 0:
        return 0.0

    interactions = 0

    if metrics.sales_count:
        interactions += metrics.sales_count

    if metrics.favorites_count:
        interactions += metrics.favorites_count

    engagement_rate = (interactions / metrics.view_count) * 100
    return round(engagement_rate, 2)


def calculate_price_competitiveness(products: List[Product]) -> dict:
    """
    Analyze price competitiveness across a list of products.

    Args:
        products: List of products to analyze

    Returns:
        Dictionary with price statistics
    """
    prices = [p.price for p in products if p.price is not None]

    if not prices:
        return {
            "min_price": None,
            "max_price": None,
            "avg_price": None,
            "median_price": None,
            "std_dev": None,
        }

    return {
        "min_price": round(min(prices), 2),
        "max_price": round(max(prices), 2),
        "avg_price": round(np.mean(prices), 2),
        "median_price": round(np.median(prices), 2),
        "std_dev": round(np.std(prices), 2),
    }


def enrich_product_metrics(product: Product) -> Product:
    """
    Calculate and add derived metrics to a product.

    Args:
        product: Product to enrich

    Returns:
        Product with updated metrics
    """
    # Calculate popularity score
    product.metrics.popularity_score = calculate_popularity_score(product)

    # Calculate velocity score
    product.metrics.velocity_score = calculate_velocity_score(product)

    return product


def rank_products_by_popularity(products: List[Product]) -> List[Product]:
    """
    Rank products by popularity score.

    Args:
        products: List of products to rank

    Returns:
        Sorted list of products (highest popularity first)
    """
    # Enrich all products with metrics
    enriched = [enrich_product_metrics(p) for p in products]

    # Sort by popularity score
    ranked = sorted(
        enriched,
        key=lambda p: p.metrics.popularity_score or 0,
        reverse=True
    )

    return ranked
