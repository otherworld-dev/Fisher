"""Etsy API v3 client implementation."""

import logging
from typing import List, Optional, Dict, Any

from fisher.api.base import BaseAPIClient
from fisher.data.models import Product, ProductMetrics, MarketplaceType, SearchQuery
from fisher.config import config

logger = logging.getLogger(__name__)


class EtsyClient(BaseAPIClient):
    """Etsy API v3 client."""

    BASE_URL = "https://openapi.etsy.com/v3/application"

    def __init__(self):
        """Initialize Etsy API client."""
        super().__init__(
            api_key=config.ETSY_API_KEY,
            rate_limit=10000,  # Etsy allows 10,000 calls/day
        )
        self.api_key = config.ETSY_API_KEY

        if not self.api_key:
            raise ValueError("Etsy API key not configured")

        # Add API key to session headers
        self.session.headers.update({
            "x-api-key": self.api_key,
        })

    def search_products(self, query: SearchQuery) -> List[Product]:
        """
        Search for products on Etsy.

        Args:
            query: Search query parameters

        Returns:
            List of products matching the query
        """
        params = {
            "keywords": query.keywords,
            "limit": min(query.max_results, 100),
            "sort_on": self._get_sort_order(query.sort_by),
        }

        # Add price filters
        if query.min_price is not None:
            params["min_price"] = query.min_price
        if query.max_price is not None:
            params["max_price"] = query.max_price

        # Add category filter if specified
        if query.category:
            params["category"] = query.category

        logger.info(f"Searching Etsy for: {query.keywords}")
        url = f"{self.BASE_URL}/listings/active"

        response_data = self._make_request("GET", url, params=params)

        if not response_data:
            logger.warning("Etsy search returned no data")
            return []

        return self._parse_search_results(response_data)

    def get_product_details(self, product_id: str) -> Optional[Product]:
        """
        Get detailed information for a specific Etsy listing.

        Args:
            product_id: Etsy listing ID

        Returns:
            Product details or None if not found
        """
        url = f"{self.BASE_URL}/listings/{product_id}"

        # Request additional data
        params = {
            "includes": "Images,Shop,User",
        }

        logger.info(f"Fetching Etsy listing details: {product_id}")
        response_data = self._make_request("GET", url, params=params)

        if not response_data:
            logger.warning(f"Etsy listing not found: {product_id}")
            return None

        return self._parse_item(response_data)

    def get_listing_stats(self, product_id: str) -> Optional[Dict[str, Any]]:
        """
        Get statistics for an Etsy listing (views, favorites).

        Args:
            product_id: Etsy listing ID

        Returns:
            Statistics dictionary or None
        """
        # Note: This endpoint may require OAuth authentication
        url = f"{self.BASE_URL}/listings/{product_id}/stats"

        logger.info(f"Fetching Etsy listing stats: {product_id}")
        return self._make_request("GET", url)

    def _parse_search_results(self, data: Dict[str, Any]) -> List[Product]:
        """Parse Etsy search results into Product objects."""
        products = []

        try:
            results = data.get("results", [])

            for idx, item in enumerate(results):
                try:
                    product = self._parse_item(item, search_rank=idx + 1)
                    if product:
                        products.append(product)
                except Exception as e:
                    logger.error(f"Error parsing Etsy item: {e}")
                    continue

        except Exception as e:
            logger.error(f"Error parsing Etsy search results: {e}")

        logger.info(f"Parsed {len(products)} Etsy products")
        return products

    def _parse_item(self, item: Dict[str, Any], search_rank: Optional[int] = None) -> Optional[Product]:
        """Parse a single Etsy listing into a Product object."""
        try:
            # Extract basic info
            listing_id = str(item.get("listing_id", ""))
            title = item.get("title", "")
            description = item.get("description", "")

            # Extract price
            price = None
            currency = "USD"

            if "price" in item:
                price_info = item["price"]
                if isinstance(price_info, dict):
                    price = float(price_info.get("amount", 0)) / 100  # Etsy returns cents
                    currency = price_info.get("currency_code", "USD")
                else:
                    price = float(price_info)

            # Extract category - Etsy uses taxonomy
            category = ""
            if "taxonomy_path" in item:
                taxonomy = item["taxonomy_path"]
                if taxonomy:
                    category = taxonomy[-1] if isinstance(taxonomy, list) else taxonomy

            # Extract shop info (seller)
            seller_id = None
            seller_name = None

            if "shop" in item:
                shop = item["shop"]
                seller_id = str(shop.get("shop_id", ""))
                seller_name = shop.get("shop_name", "")
            else:
                seller_id = str(item.get("shop_id", ""))

            # Extract user (seller) info
            if "user" in item:
                user = item["user"]
                if not seller_name:
                    seller_name = user.get("login_name", "")

            # Extract image URL
            image_url = None
            if "images" in item:
                images = item["images"]
                if images and isinstance(images, list):
                    image_url = images[0].get("url_570xN") or images[0].get("url_fullxfull")
            elif "url" in item:
                image_url = item["url"]

            # Build product URL
            product_url = item.get("url", f"https://www.etsy.com/listing/{listing_id}")

            # Extract metrics
            views = item.get("views", None)
            favorites = item.get("num_favorers", None)

            # Calculate listing age
            listing_age_days = None
            if "created_timestamp" in item:
                from datetime import datetime
                created = datetime.fromtimestamp(item["created_timestamp"])
                listing_age_days = (datetime.utcnow() - created).days

            # Create metrics
            metrics = ProductMetrics(
                view_count=views,
                favorites_count=favorites,
                listing_age_days=listing_age_days,
                search_rank=search_rank,
            )

            # Extract state/condition
            condition = "Handmade"  # Most Etsy items are handmade
            if "state" in item:
                state = item["state"]
                if state == "active":
                    condition = "New/Handmade"

            product = Product(
                product_id=listing_id,
                title=title,
                description=description[:500] if description else None,  # Truncate long descriptions
                marketplace=MarketplaceType.ETSY,
                price=price,
                currency=currency,
                category=category,
                condition=condition,
                image_url=image_url,
                product_url=product_url,
                seller_id=seller_id,
                seller_name=seller_name,
                metrics=metrics,
                raw_data=item,
            )

            return product

        except Exception as e:
            logger.error(f"Error parsing Etsy item: {e}")
            logger.debug(f"Item data: {item}")
            return None

    def _get_sort_order(self, sort_by: Optional[str]) -> str:
        """Convert generic sort order to Etsy-specific value."""
        sort_map = {
            "relevance": "relevance",
            "price_low": "price",
            "price_high": "price",  # Use with sort_order=desc
            "newest": "created",
        }
        return sort_map.get(sort_by or "relevance", "relevance")
