.PHONY: install test clean help

help:
	@echo "Fisher - Marketplace Product Analysis Tool"
	@echo ""
	@echo "Available commands:"
	@echo "  make install    - Install dependencies"
	@echo "  make test       - Run tests"
	@echo "  make clean      - Remove build artifacts"
	@echo "  make status     - Check API configuration"
	@echo "  make example    - Run example search"
	@echo ""

install:
	pip install -r requirements.txt

install-dev:
	pip install -e .

test:
	pytest tests/

clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

status:
	python -m fisher status

example:
	python -m fisher search "vintage watches" --max-results 20
