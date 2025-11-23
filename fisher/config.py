"""Configuration management for Fisher."""

import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Config:
    """Application configuration."""

    # eBay Configuration
    EBAY_APP_ID: str = os.getenv("EBAY_APP_ID", "")
    EBAY_CERT_ID: str = os.getenv("EBAY_CERT_ID", "")
    EBAY_DEV_ID: str = os.getenv("EBAY_DEV_ID", "")
    EBAY_ENVIRONMENT: str = os.getenv("EBAY_ENVIRONMENT", "production")

    # Amazon Configuration
    AMAZON_ACCESS_KEY: str = os.getenv("AMAZON_ACCESS_KEY", "")
    AMAZON_SECRET_KEY: str = os.getenv("AMAZON_SECRET_KEY", "")
    AMAZON_PARTNER_TAG: str = os.getenv("AMAZON_PARTNER_TAG", "")
    AMAZON_REGION: str = os.getenv("AMAZON_REGION", "us-east-1")

    # Etsy Configuration
    ETSY_API_KEY: str = os.getenv("ETSY_API_KEY", "")
    ETSY_SHARED_SECRET: str = os.getenv("ETSY_SHARED_SECRET", "")

    # General Settings
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    CACHE_ENABLED: bool = os.getenv("CACHE_ENABLED", "true").lower() == "true"
    CACHE_TTL: int = int(os.getenv("CACHE_TTL", "3600"))
    MAX_RESULTS_PER_QUERY: int = int(os.getenv("MAX_RESULTS_PER_QUERY", "100"))

    # Data directory
    DATA_DIR: Path = Path(os.getenv("DATA_DIR", "./data"))

    @classmethod
    def validate_ebay(cls) -> bool:
        """Check if eBay credentials are configured."""
        return bool(cls.EBAY_APP_ID and cls.EBAY_CERT_ID and cls.EBAY_DEV_ID)

    @classmethod
    def validate_amazon(cls) -> bool:
        """Check if Amazon credentials are configured."""
        return bool(cls.AMAZON_ACCESS_KEY and cls.AMAZON_SECRET_KEY and cls.AMAZON_PARTNER_TAG)

    @classmethod
    def validate_etsy(cls) -> bool:
        """Check if Etsy credentials are configured."""
        return bool(cls.ETSY_API_KEY and cls.ETSY_SHARED_SECRET)

    @classmethod
    def get_configured_marketplaces(cls) -> list[str]:
        """Return list of marketplaces with valid credentials."""
        marketplaces = []
        if cls.validate_ebay():
            marketplaces.append("ebay")
        if cls.validate_amazon():
            marketplaces.append("amazon")
        if cls.validate_etsy():
            marketplaces.append("etsy")
        return marketplaces


config = Config()
