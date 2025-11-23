"""Data models for Fisher."""

from enum import Enum
from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class MarketplaceType(str, Enum):
    """Supported marketplace platforms."""
    EBAY = "ebay"
    AMAZON = "amazon"
    ETSY = "etsy"


class ProductMetrics(BaseModel):
    """Popularity and performance metrics for a product."""

    sales_count: Optional[int] = Field(None, description="Number of sales")
    view_count: Optional[int] = Field(None, description="Number of views")
    review_count: Optional[int] = Field(None, description="Number of reviews")
    average_rating: Optional[float] = Field(None, ge=0, le=5, description="Average rating (0-5)")
    favorites_count: Optional[int] = Field(None, description="Number of favorites/watchers")
    search_rank: Optional[int] = Field(None, description="Position in search results")
    listing_age_days: Optional[int] = Field(None, description="Days since listing created")

    # Calculated metrics
    popularity_score: Optional[float] = Field(None, description="Calculated popularity score")
    velocity_score: Optional[float] = Field(None, description="Sales velocity score")


class Product(BaseModel):
    """Product information from a marketplace."""

    # Basic information
    product_id: str = Field(..., description="Unique product ID from marketplace")
    title: str = Field(..., description="Product title")
    description: Optional[str] = Field(None, description="Product description")
    marketplace: MarketplaceType = Field(..., description="Source marketplace")

    # Pricing
    price: Optional[float] = Field(None, ge=0, description="Current price")
    currency: Optional[str] = Field("USD", description="Currency code")
    original_price: Optional[float] = Field(None, ge=0, description="Original/list price")

    # Product details
    category: Optional[str] = Field(None, description="Product category")
    brand: Optional[str] = Field(None, description="Brand name")
    condition: Optional[str] = Field(None, description="Product condition")
    image_url: Optional[str] = Field(None, description="Main product image URL")
    product_url: Optional[str] = Field(None, description="Link to product page")

    # Seller information
    seller_id: Optional[str] = Field(None, description="Seller ID")
    seller_name: Optional[str] = Field(None, description="Seller name")
    seller_rating: Optional[float] = Field(None, ge=0, le=5, description="Seller rating")

    # Metrics
    metrics: ProductMetrics = Field(default_factory=ProductMetrics, description="Product metrics")

    # Metadata
    collected_at: datetime = Field(default_factory=datetime.utcnow, description="When data was collected")
    raw_data: Optional[Dict[str, Any]] = Field(None, description="Original API response data")

    class Config:
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }


class SearchQuery(BaseModel):
    """Search query parameters."""

    keywords: str = Field(..., description="Search keywords")
    marketplaces: list[MarketplaceType] = Field(default_factory=list, description="Target marketplaces")
    category: Optional[str] = Field(None, description="Category filter")
    min_price: Optional[float] = Field(None, ge=0, description="Minimum price")
    max_price: Optional[float] = Field(None, ge=0, description="Maximum price")
    condition: Optional[str] = Field(None, description="Product condition")
    max_results: int = Field(100, ge=1, le=1000, description="Maximum results per marketplace")
    sort_by: Optional[str] = Field("relevance", description="Sort order")

    class Config:
        use_enum_values = True


class AnalysisReport(BaseModel):
    """Analysis report for product research."""

    query: SearchQuery = Field(..., description="Original search query")
    total_products: int = Field(0, description="Total products analyzed")
    top_products: list[Product] = Field(default_factory=list, description="Top performing products")
    insights: Dict[str, Any] = Field(default_factory=dict, description="Analysis insights")
    generated_at: datetime = Field(default_factory=datetime.utcnow, description="Report generation time")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }
