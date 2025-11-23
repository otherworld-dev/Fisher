"""
Fisher - Marketplace Product Analysis Tool

A tool for identifying popular products across eBay, Amazon, and Etsy.
"""

__version__ = "0.1.0"
__author__ = "Fisher Dev Team"

from fisher.data.models import Product, MarketplaceType

__all__ = ["Product", "MarketplaceType"]
