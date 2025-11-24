"""Amazon Product Advertising API client implementation."""

import logging
import hashlib
import hmac
import base64
from typing import List, Optional, Dict, Any
from datetime import datetime
from urllib.parse import quote, urlencode

from fisher.api.base import BaseAPIClient
from fisher.data.models import Product, ProductMetrics, MarketplaceType, SearchQuery
from fisher.config import config

logger = logging.getLogger(__name__)


class AmazonClient(BaseAPIClient):
    """Amazon Product Advertising API (PA-API 5.0) client."""

    BASE_URL = "https://webservices.amazon.com/paapi5"
    SERVICE = "ProductAdvertisingAPI"

    def __init__(self):
        """Initialize Amazon PA-API client."""
        super().__init__(
            api_key=config.AMAZON_ACCESS_KEY,
            rate_limit=10,  # Conservative limit, adjust based on your tier
        )
        self.access_key = config.AMAZON_ACCESS_KEY
        self.secret_key = config.AMAZON_SECRET_KEY
        self.partner_tag = config.AMAZON_PARTNER_TAG
        self.region = config.AMAZON_REGION

        if not all([self.access_key, self.secret_key, self.partner_tag]):
            raise ValueError("Amazon API credentials not fully configured")

        # Set region-specific endpoint (defaulting to UK for GBP)
        region_hosts = {
            "us-east-1": "webservices.amazon.com",
            "eu-west-1": "webservices.amazon.co.uk",
            "us-west-2": "webservices.amazon.com",
        }
        # Use UK endpoint for GBP prices
        self.host = "webservices.amazon.co.uk"
        self.marketplace = "www.amazon.co.uk"
        self.endpoint = f"https://{self.host}/paapi5/searchitems"

    def search_products(self, query: SearchQuery) -> List[Product]:
        """
        Search for products on Amazon.

        Args:
            query: Search query parameters

        Returns:
            List of products matching the query
        """
        # Build request payload
        payload = {
            "Keywords": query.keywords,
            "Resources": [
                "Images.Primary.Large",
                "ItemInfo.Title",
                "ItemInfo.Features",
                "ItemInfo.ProductInfo",
                "ItemInfo.ContentInfo",
                "ItemInfo.ByLineInfo",
                "Offers.Listings.Price",
                "Offers.Listings.Condition",
                "BrowseNodeInfo.BrowseNodes",
            ],
            "PartnerTag": self.partner_tag,
            "PartnerType": "Associates",
            "Marketplace": self.marketplace,  # UK marketplace for GBP
            "ItemCount": min(query.max_results, 10),  # Max 10 per request
        }

        # Add optional filters
        if query.min_price is not None or query.max_price is not None:
            payload["MinPrice"] = int(query.min_price * 100) if query.min_price else 0
            if query.max_price is not None:
                payload["MaxPrice"] = int(query.max_price * 100)

        if query.condition:
            condition_map = {
                "new": "New",
                "used": "Used",
                "refurbished": "Refurbished",
            }
            payload["Condition"] = condition_map.get(query.condition.lower(), "New")

        logger.info(f"Searching Amazon for: {query.keywords}")

        # Note: Amazon PA-API requires AWS Signature V4
        # For production use, consider using the official amazon-paapi library
        # This is a simplified implementation

        headers = {
            "Content-Type": "application/json",
            "X-Amz-Target": "com.amazon.paapi5.v1.ProductAdvertisingAPIv1.SearchItems",
        }

        response_data = self._make_request(
            "POST",
            self.endpoint,
            headers=headers,
            json_data=payload,
        )

        if not response_data:
            logger.warning("Amazon search returned no data")
            return []

        return self._parse_search_results(response_data)

    def get_product_details(self, product_id: str) -> Optional[Product]:
        """
        Get detailed information for a specific Amazon product.

        Args:
            product_id: Amazon ASIN

        Returns:
            Product details or None if not found
        """
        payload = {
            "ItemIds": [product_id],
            "Resources": [
                "Images.Primary.Large",
                "ItemInfo.Title",
                "ItemInfo.Features",
                "ItemInfo.ProductInfo",
                "ItemInfo.ContentInfo",
                "ItemInfo.ByLineInfo",
                "ItemInfo.Classifications",
                "Offers.Listings.Price",
                "Offers.Listings.Condition",
                "Offers.Listings.Availability",
                "BrowseNodeInfo.BrowseNodes",
                "CustomerReviews.Count",
                "CustomerReviews.StarRating",
            ],
            "PartnerTag": self.partner_tag,
            "PartnerType": "Associates",
            "Marketplace": self.marketplace,  # UK marketplace for GBP
        }

        headers = {
            "Content-Type": "application/json",
            "X-Amz-Target": "com.amazon.paapi5.v1.ProductAdvertisingAPIv1.GetItems",
        }

        logger.info(f"Fetching Amazon product details: {product_id}")
        endpoint = f"https://{self.host}/paapi5/getitems"

        response_data = self._make_request(
            "POST",
            endpoint,
            headers=headers,
            json_data=payload,
        )

        if not response_data or "ItemsResult" not in response_data:
            logger.warning(f"Amazon product not found: {product_id}")
            return None

        items = response_data.get("ItemsResult", {}).get("Items", [])
        if items:
            return self._parse_item(items[0])

        return None

    def _parse_search_results(self, data: Dict[str, Any]) -> List[Product]:
        """Parse Amazon search results into Product objects."""
        products = []

        try:
            search_result = data.get("SearchResult", {})
            items = search_result.get("Items", [])

            for idx, item in enumerate(items):
                try:
                    product = self._parse_item(item, search_rank=idx + 1)
                    if product:
                        products.append(product)
                except Exception as e:
                    logger.error(f"Error parsing Amazon item: {e}")
                    continue

        except Exception as e:
            logger.error(f"Error parsing Amazon search results: {e}")

        logger.info(f"Parsed {len(products)} Amazon products")
        return products

    def _parse_item(self, item: Dict[str, Any], search_rank: Optional[int] = None) -> Optional[Product]:
        """Parse a single Amazon item into a Product object."""
        try:
            # Extract ASIN
            asin = item.get("ASIN", "")

            # Extract title
            title = item.get("ItemInfo", {}).get("Title", {}).get("DisplayValue", "")

            # Extract price
            offers = item.get("Offers", {}).get("Listings", [])
            price = None
            currency = "GBP"
            condition = "New"

            if offers:
                offer = offers[0]
                price_info = offer.get("Price", {})
                if price_info:
                    price = price_info.get("Amount")
                    currency = price_info.get("Currency", "GBP")

                cond_info = offer.get("Condition", {})
                if cond_info:
                    condition = cond_info.get("Value", "New")

            # Extract brand
            brand = item.get("ItemInfo", {}).get("ByLineInfo", {}).get("Brand", {}).get("DisplayValue")

            # Extract category
            category = ""
            browse_nodes = item.get("BrowseNodeInfo", {}).get("BrowseNodes", [])
            if browse_nodes:
                category = browse_nodes[0].get("DisplayName", "")

            # Extract image URL
            image_url = item.get("Images", {}).get("Primary", {}).get("Large", {}).get("URL")

            # Build product URL
            product_url = item.get("DetailPageURL", f"https://www.amazon.co.uk/dp/{asin}")

            # Extract reviews
            reviews_info = item.get("CustomerReviews", {})
            review_count = None
            average_rating = None

            if reviews_info:
                review_count = reviews_info.get("Count")
                rating_value = reviews_info.get("StarRating", {}).get("Value")
                if rating_value:
                    average_rating = float(rating_value)

            # Create metrics
            metrics = ProductMetrics(
                review_count=review_count,
                average_rating=average_rating,
                search_rank=search_rank,
            )

            product = Product(
                product_id=asin,
                title=title,
                marketplace=MarketplaceType.AMAZON,
                price=price,
                currency=currency,
                category=category,
                brand=brand,
                condition=condition,
                image_url=image_url,
                product_url=product_url,
                metrics=metrics,
                raw_data=item,
            )

            return product

        except Exception as e:
            logger.error(f"Error parsing Amazon item: {e}")
            return None
