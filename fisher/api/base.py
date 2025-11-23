"""Base API client with common functionality."""

import logging
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
import requests
from datetime import datetime, timedelta

from fisher.data.models import Product, SearchQuery

logger = logging.getLogger(__name__)


class RateLimiter:
    """Simple rate limiter for API calls."""

    def __init__(self, max_calls: int, time_window: int):
        """
        Initialize rate limiter.

        Args:
            max_calls: Maximum number of calls allowed
            time_window: Time window in seconds
        """
        self.max_calls = max_calls
        self.time_window = time_window
        self.calls: List[datetime] = []

    def can_proceed(self) -> bool:
        """Check if a new call can be made."""
        now = datetime.utcnow()
        cutoff = now - timedelta(seconds=self.time_window)

        # Remove old calls
        self.calls = [call for call in self.calls if call > cutoff]

        if len(self.calls) < self.max_calls:
            self.calls.append(now)
            return True
        return False

    def wait_time(self) -> float:
        """Calculate wait time in seconds before next call."""
        if not self.calls:
            return 0.0

        oldest_call = min(self.calls)
        wait_until = oldest_call + timedelta(seconds=self.time_window)
        now = datetime.utcnow()

        if wait_until > now:
            return (wait_until - now).total_seconds()
        return 0.0


class BaseAPIClient(ABC):
    """Base class for marketplace API clients."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        rate_limit: Optional[int] = None,
        timeout: int = 30,
    ):
        """
        Initialize API client.

        Args:
            api_key: API authentication key
            rate_limit: Maximum API calls per minute
            timeout: Request timeout in seconds
        """
        self.api_key = api_key
        self.timeout = timeout
        self.session = requests.Session()

        # Set up rate limiter if specified
        self.rate_limiter = (
            RateLimiter(max_calls=rate_limit, time_window=60)
            if rate_limit
            else None
        )

        # Set common headers
        self.session.headers.update({
            "User-Agent": "Fisher/0.1.0",
            "Accept": "application/json",
        })

    @abstractmethod
    def search_products(
        self, query: SearchQuery
    ) -> List[Product]:
        """
        Search for products.

        Args:
            query: Search query parameters

        Returns:
            List of products matching the query
        """
        pass

    @abstractmethod
    def get_product_details(self, product_id: str) -> Optional[Product]:
        """
        Get detailed information for a specific product.

        Args:
            product_id: Product identifier

        Returns:
            Product details or None if not found
        """
        pass

    def _make_request(
        self,
        method: str,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        json_data: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Make an API request with rate limiting and error handling.

        Args:
            method: HTTP method (GET, POST, etc.)
            url: Request URL
            params: Query parameters
            headers: Additional headers
            json_data: JSON request body

        Returns:
            Response data as dictionary or None on error
        """
        # Check rate limit
        if self.rate_limiter and not self.rate_limiter.can_proceed():
            wait_time = self.rate_limiter.wait_time()
            logger.warning(f"Rate limit reached. Waiting {wait_time:.2f} seconds...")
            import time
            time.sleep(wait_time)

        try:
            response = self.session.request(
                method=method,
                url=url,
                params=params,
                headers=headers,
                json=json_data,
                timeout=self.timeout,
            )
            response.raise_for_status()
            return response.json()

        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error: {e}")
            if hasattr(e.response, "text"):
                logger.debug(f"Response: {e.response.text}")
        except requests.exceptions.Timeout:
            logger.error(f"Request timeout after {self.timeout}s")
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error: {e}")
        except Exception as e:
            logger.error(f"Unexpected error: {e}")

        return None

    def close(self):
        """Close the HTTP session."""
        self.session.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
