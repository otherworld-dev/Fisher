"""eBay API client implementation."""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime

from fisher.api.base import BaseAPIClient
from fisher.data.models import Product, ProductMetrics, MarketplaceType, SearchQuery
from fisher.config import config

logger = logging.getLogger(__name__)


class EbayClient(BaseAPIClient):
    """eBay API client using Finding and Shopping APIs."""

    BASE_URL_FINDING = "https://svcs.ebay.com/services/search/FindingService/v1"
    BASE_URL_SHOPPING = "https://open.api.ebay.com/shopping"

    def __init__(self):
        """Initialize eBay API client."""
        super().__init__(
            api_key=config.EBAY_APP_ID,
            rate_limit=5000,  # eBay allows 5000 calls/day
        )
        self.app_id = config.EBAY_APP_ID
        self.cert_id = config.EBAY_CERT_ID
        self.dev_id = config.EBAY_DEV_ID

        if not self.app_id:
            raise ValueError("eBay App ID not configured")

    def search_products(self, query: SearchQuery) -> List[Product]:
        """
        Search for products on eBay.

        Args:
            query: Search query parameters

        Returns:
            List of products matching the query
        """
        params = {
            "OPERATION-NAME": "findItemsAdvanced",
            "SERVICE-VERSION": "1.0.0",
            "SECURITY-APPNAME": self.app_id,
            "RESPONSE-DATA-FORMAT": "JSON",
            "REST-PAYLOAD": "",
            "keywords": query.keywords,
            "paginationInput.entriesPerPage": min(query.max_results, 100),
            "sortOrder": self._get_sort_order(query.sort_by),
        }

        # Add category filter if specified
        if query.category:
            params["categoryId"] = query.category

        # Add price filters
        item_filters = []
        filter_index = 0

        if query.min_price is not None:
            item_filters.append({
                f"itemFilter({filter_index}).name": "MinPrice",
                f"itemFilter({filter_index}).value": str(query.min_price),
            })
            filter_index += 1

        if query.max_price is not None:
            item_filters.append({
                f"itemFilter({filter_index}).name": "MaxPrice",
                f"itemFilter({filter_index}).value": str(query.max_price),
            })
            filter_index += 1

        if query.condition:
            condition_map = {
                "new": "1000",
                "used": "3000",
                "refurbished": "2000",
            }
            condition_id = condition_map.get(query.condition.lower())
            if condition_id:
                item_filters.append({
                    f"itemFilter({filter_index}).name": "Condition",
                    f"itemFilter({filter_index}).value": condition_id,
                })

        # Flatten item filters into params
        for filter_dict in item_filters:
            params.update(filter_dict)

        logger.info(f"Searching eBay for: {query.keywords}")
        response_data = self._make_request("GET", self.BASE_URL_FINDING, params=params)

        if not response_data:
            logger.warning("eBay search returned no data")
            return []

        return self._parse_search_results(response_data)

    def get_product_details(self, product_id: str) -> Optional[Product]:
        """
        Get detailed information for a specific eBay listing.

        Args:
            product_id: eBay item ID

        Returns:
            Product details or None if not found
        """
        params = {
            "callname": "GetSingleItem",
            "responseencoding": "JSON",
            "appid": self.app_id,
            "siteid": "0",
            "version": "967",
            "ItemID": product_id,
            "IncludeSelector": "Description,Details,ItemSpecifics",
        }

        logger.info(f"Fetching eBay item details: {product_id}")
        response_data = self._make_request("GET", self.BASE_URL_SHOPPING, params=params)

        if not response_data or "Item" not in response_data:
            logger.warning(f"eBay item not found: {product_id}")
            return None

        return self._parse_item_details(response_data["Item"])

    def _parse_search_results(self, data: Dict[str, Any]) -> List[Product]:
        """Parse eBay search results into Product objects."""
        products = []

        try:
            search_result = data.get("findItemsAdvancedResponse", [{}])[0]
            items = search_result.get("searchResult", [{}])[0].get("item", [])

            for idx, item in enumerate(items):
                try:
                    product = self._parse_item(item, search_rank=idx + 1)
                    if product:
                        products.append(product)
                except Exception as e:
                    logger.error(f"Error parsing eBay item: {e}")
                    continue

        except Exception as e:
            logger.error(f"Error parsing eBay search results: {e}")

        logger.info(f"Parsed {len(products)} eBay products")
        return products

    def _parse_item(self, item: Dict[str, Any], search_rank: Optional[int] = None) -> Optional[Product]:
        """Parse a single eBay item into a Product object."""
        try:
            # Extract basic info
            item_id = item.get("itemId", [""])[0] if isinstance(item.get("itemId"), list) else item.get("itemId", "")
            title = item.get("title", [""])[0] if isinstance(item.get("title"), list) else item.get("title", "")

            # Extract price
            price_info = item.get("sellingStatus", [{}])[0] if isinstance(item.get("sellingStatus"), list) else item.get("sellingStatus", {})
            current_price = price_info.get("currentPrice", [{}])[0] if isinstance(price_info.get("currentPrice"), list) else price_info.get("currentPrice", {})
            price = float(current_price.get("__value__", 0))
            currency = current_price.get("@currencyId", "USD")

            # Extract category
            category_name = ""
            if "primaryCategory" in item:
                primary_cat = item["primaryCategory"][0] if isinstance(item["primaryCategory"], list) else item["primaryCategory"]
                category_name = primary_cat.get("categoryName", [""])[0] if isinstance(primary_cat.get("categoryName"), list) else primary_cat.get("categoryName", "")

            # Extract condition
            condition = ""
            if "condition" in item:
                cond = item["condition"][0] if isinstance(item["condition"], list) else item["condition"]
                condition = cond.get("conditionDisplayName", [""])[0] if isinstance(cond.get("conditionDisplayName"), list) else cond.get("conditionDisplayName", "")

            # Extract image URL
            image_url = item.get("galleryURL", [""])[0] if isinstance(item.get("galleryURL"), list) else item.get("galleryURL", "")

            # Extract product URL
            product_url = item.get("viewItemURL", [""])[0] if isinstance(item.get("viewItemURL"), list) else item.get("viewItemURL", "")

            # Extract listing info
            listing_info = item.get("listingInfo", [{}])[0] if isinstance(item.get("listingInfo"), list) else item.get("listingInfo", {})

            # Create metrics
            metrics = ProductMetrics(
                search_rank=search_rank,
            )

            product = Product(
                product_id=item_id,
                title=title,
                marketplace=MarketplaceType.EBAY,
                price=price,
                currency=currency,
                category=category_name,
                condition=condition,
                image_url=image_url,
                product_url=product_url,
                metrics=metrics,
                raw_data=item,
            )

            return product

        except Exception as e:
            logger.error(f"Error parsing eBay item: {e}")
            return None

    def _parse_item_details(self, item: Dict[str, Any]) -> Optional[Product]:
        """Parse detailed eBay item information."""
        return self._parse_item(item)

    def _get_sort_order(self, sort_by: Optional[str]) -> str:
        """Convert generic sort order to eBay-specific value."""
        sort_map = {
            "relevance": "BestMatch",
            "price_low": "PricePlusShippingLowest",
            "price_high": "PricePlusShippingHighest",
            "newest": "StartTimeNewest",
            "ending": "EndTimeSoonest",
        }
        return sort_map.get(sort_by or "relevance", "BestMatch")
