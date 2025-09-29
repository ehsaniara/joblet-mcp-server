# Joblet MCP Server Makefile

.PHONY: install dev-install test lint format type-check clean run help

# Default Python interpreter
PYTHON ?= python3

help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install package and dependencies
	$(PYTHON) -m pip install -e .

dev-install: ## Install package with development dependencies
	$(PYTHON) -m pip install -e ".[dev]"

test: ## Run tests
	$(PYTHON) -m pytest tests/ -v

test-coverage: ## Run tests with coverage
	$(PYTHON) -m pytest tests/ -v --cov=joblet_mcp_server --cov-report=term-missing

lint: ## Run linting
	$(PYTHON) -m flake8 joblet_mcp_server/ --max-line-length=120 --extend-ignore=E203,W503
	$(PYTHON) -m flake8 tests/ --max-line-length=120 --extend-ignore=E203,W503,E501

format: ## Format code
	$(PYTHON) -m black joblet_mcp_server/ tests/ examples/
	$(PYTHON) -m isort joblet_mcp_server/ tests/ examples/

format-check: ## Check code formatting
	$(PYTHON) -m black --check joblet_mcp_server/ tests/ examples/
	$(PYTHON) -m isort --check-only joblet_mcp_server/ tests/ examples/

type-check: ## Run type checking
	$(PYTHON) -m mypy joblet_mcp_server/

check: format-check lint type-check test ## Run all checks

clean: ## Clean build artifacts
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete

run: ## Run the MCP server (SDK-based, default)
	joblet-mcp-server

run-cli: ## Run the CLI-based MCP server
	joblet-mcp-server-cli

run-debug: ## Run the MCP server with debug logging
	joblet-mcp-server --debug

build: ## Build distribution packages
	$(PYTHON) -m build

upload: build ## Upload to PyPI (requires authentication)
	$(PYTHON) -m twine upload dist/*

test-upload: build ## Upload to Test PyPI
	$(PYTHON) -m twine upload --repository testpypi dist/*

# Development utilities
docs: ## Generate documentation (if implemented)
	@echo "Documentation generation not implemented yet"

validate-config: ## Validate sample configuration
	$(PYTHON) -c "import yaml; yaml.safe_load(open('sample_config.yaml'))"

# Installation verification
verify-install: ## Verify installation works
	$(PYTHON) -c "import joblet_mcp_server; print('✓ Package imported successfully')"
	$(PYTHON) -c "from joblet_mcp_server.server import JobletMCPServer; print('✓ CLI server class imported successfully')"
	$(PYTHON) -c "from joblet_mcp_server.server_sdk import JobletMCPServerSDK; print('✓ SDK server class imported successfully')"
	joblet-mcp-server --help > /dev/null && echo "✓ Default SDK entry point works"
	joblet-mcp-server-cli --help > /dev/null && echo "✓ CLI entry point works"

# Quick development setup
setup: dev-install verify-install ## Complete development setup
	@echo "✓ Development environment setup complete"
	@echo ""
	@echo "Next steps:"
	@echo "  1. Configure your Joblet connection (see sample_config.yaml)"
	@echo "  2. Run tests: make test"
	@echo "  3. Start the server: make run"

# CI/CD targets
ci: format-check lint type-check test ## Run all CI checks