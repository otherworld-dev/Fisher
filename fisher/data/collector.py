"""Data collection module for gathering product information."""

import logging
from typing import List, Dict, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

from fisher.data.models import Product, SearchQuery, MarketplaceType
from fisher.api.ebay import EbayClient
from fisher.api.amazon import AmazonClient
from fisher.api.etsy import EtsyClient
from fisher.config import config

logger = logging.getLogger(__name__)


class DataCollector:
    """Collects product data from multiple marketplaces."""

    def __init__(self):
        """Initialize data collector with API clients."""
        self.clients: Dict[MarketplaceType, object] = {}

        # Initialize available clients based on configuration
        if config.validate_ebay():
            try:
                self.clients[MarketplaceType.EBAY] = EbayClient()
                logger.info("eBay client initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize eBay client: {e}")

        if config.validate_amazon():
            try:
                self.clients[MarketplaceType.AMAZON] = AmazonClient()
                logger.info("Amazon client initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize Amazon client: {e}")

        if config.validate_etsy():
            try:
                self.clients[MarketplaceType.ETSY] = EtsyClient()
                logger.info("Etsy client initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize Etsy client: {e}")

        if not self.clients:
            logger.warning("No marketplace clients initialized. Check your API credentials.")

    def collect(self, query: SearchQuery, parallel: bool = True) -> List[Product]:
        """
        Collect product data from specified marketplaces.

        Args:
            query: Search query parameters
            parallel: Whether to query marketplaces in parallel

        Returns:
            List of products from all queried marketplaces
        """
        # Determine which marketplaces to query
        target_marketplaces = query.marketplaces or list(self.clients.keys())

        # Filter to only available clients
        available_marketplaces = [
            mp for mp in target_marketplaces
            if mp in self.clients
        ]

        if not available_marketplaces:
            logger.error("No valid marketplaces specified or configured")
            return []

        logger.info(f"Collecting from marketplaces: {[mp.value for mp in available_marketplaces]}")

        if parallel:
            return self._collect_parallel(query, available_marketplaces)
        else:
            return self._collect_sequential(query, available_marketplaces)

    def _collect_parallel(
        self, query: SearchQuery, marketplaces: List[MarketplaceType]
    ) -> List[Product]:
        """Collect data from multiple marketplaces in parallel."""
        all_products = []

        with ThreadPoolExecutor(max_workers=len(marketplaces)) as executor:
            # Submit search tasks for each marketplace
            future_to_marketplace = {
                executor.submit(self._search_marketplace, marketplace, query): marketplace
                for marketplace in marketplaces
            }

            # Collect results as they complete
            for future in as_completed(future_to_marketplace):
                marketplace = future_to_marketplace[future]
                try:
                    products = future.result()
                    logger.info(f"Collected {len(products)} products from {marketplace.value}")
                    all_products.extend(products)
                except Exception as e:
                    logger.error(f"Error collecting from {marketplace.value}: {e}")

        logger.info(f"Total products collected: {len(all_products)}")
        return all_products

    def _collect_sequential(
        self, query: SearchQuery, marketplaces: List[MarketplaceType]
    ) -> List[Product]:
        """Collect data from marketplaces sequentially."""
        all_products = []

        for marketplace in marketplaces:
            try:
                products = self._search_marketplace(marketplace, query)
                logger.info(f"Collected {len(products)} products from {marketplace.value}")
                all_products.extend(products)
            except Exception as e:
                logger.error(f"Error collecting from {marketplace.value}: {e}")

        logger.info(f"Total products collected: {len(all_products)}")
        return all_products

    def _search_marketplace(
        self, marketplace: MarketplaceType, query: SearchQuery
    ) -> List[Product]:
        """Search a specific marketplace."""
        client = self.clients.get(marketplace)
        if not client:
            logger.warning(f"No client available for {marketplace.value}")
            return []

        try:
            return client.search_products(query)
        except Exception as e:
            logger.error(f"Error searching {marketplace.value}: {e}")
            return []

    def get_product_details(
        self, marketplace: MarketplaceType, product_id: str
    ) -> Optional[Product]:
        """
        Get detailed information for a specific product.

        Args:
            marketplace: The marketplace platform
            product_id: Product identifier

        Returns:
            Product details or None
        """
        client = self.clients.get(marketplace)
        if not client:
            logger.warning(f"No client available for {marketplace.value}")
            return None

        try:
            return client.get_product_details(product_id)
        except Exception as e:
            logger.error(f"Error fetching product details from {marketplace.value}: {e}")
            return None

    def get_available_marketplaces(self) -> List[str]:
        """Get list of configured and available marketplaces."""
        return [mp.value for mp in self.clients.keys()]

    def close(self):
        """Close all API client sessions."""
        for client in self.clients.values():
            if hasattr(client, "close"):
                client.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
