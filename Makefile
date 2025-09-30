.PHONY: help install dev test lint clean

# Default target
help:
	@echo "Available commands:"
	@echo "  dev     - Set up development environment"
	@echo "  test    - Run tests with coverage"
	@echo "  lint    - Run all code quality checks"
	@echo "  clean   - Remove build artifacts"

# Development setup
dev:
	pip install -e ".[dev,sdk]"
	pre-commit install

# Testing
test:
	pytest tests/ -v

# Code quality (exactly what CI runs)
lint:
	pre-commit run --all-files

# Cleanup
clean:
	rm -rf build/ dist/ *.egg-info .pytest_cache .mypy_cache .coverage __pycache__
	find . -name "*.pyc" -delete
	find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
