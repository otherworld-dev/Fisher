from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="fisher",
    version="0.1.0",
    author="Fisher Dev Team",
    description="Marketplace product analysis tool for eBay, Amazon, and Etsy",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.9",
    install_requires=[
        "requests>=2.31.0",
        "python-dotenv>=1.0.0",
        "pydantic>=2.5.0",
        "pandas>=2.1.0",
        "numpy>=1.24.0",
        "ebaysdk>=2.2.0",
        "click>=8.1.0",
        "rich>=13.7.0",
        "python-dateutil>=2.8.2",
        "aiohttp>=3.9.0",
    ],
    entry_points={
        "console_scripts": [
            "fisher=fisher.main:cli",
        ],
    },
)
