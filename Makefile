
# Makefile for py2max project

.PHONY: help all build test test-verbose coverage lint \
		typecheck quality docs docs-clean docs-serve install \
		dev clean reset ci format

help: ## Show this help message
	@echo "Available commands:"
	@awk 'BEGIN {FS = ":.*##"; printf "\033[36m%-12s\033[0m %s\n", "Command", "Description"} /^[a-zA-Z_-]+:.*?##/ { printf "\033[36m%-12s\033[0m %s\n", $$1, $$2 }' $(MAKEFILE_LIST)

all: quality test docs ## Run all checks and build everything

build: ## Build wheel
	@uv build

test: ## Run tests
	@uv run pytest

test-verbose: ## Run tests with verbose output
	@uv run pytest -v

coverage: ## Generate coverage report
	@mkdir -p outputs
	@uv run pytest --cov-report html:outputs/_covhtml --cov=py2max tests

lint: ## Run code linting
	@uv run ruff check py2max --fix

format: ## Run code formatting
	@uv run ruff format .

typecheck: ## Run type checking
	@uv run mypy py2max

quality: ## Run all quality checks (lint + formatcheck + typecheck)
	@uv run ruff check py2max
	@uv run ruff format --check
	@uv run mypy py2max

docs: ## Build documentation
	@cd docs && uv run sphinx-build -b html source build

docs-clean: ## Clean documentation build
	@rm -rf docs/build

docs-serve: docs ## Build and serve documentation locally
	@echo "Documentation built. Open docs/build/index.html in your browser"
	@echo "Or run: python -m http.server 8000 --directory docs/build"

install: ## Install package in development mode
	@uv sync

dev: install ## Set up development environment
	@echo "Development environment ready!"
	@echo "Activate with: source .venv/bin/activate"

clean: ## Clean build artifacts
	@rm -rf build/
	@rm -rf dist/
	@rm -rf *.egg-info/
	@rm -rf .pytest_cache/
	@rm -rf .mypy_cache/
	@rm -rf __pycache__/
	@find . -name "*.pyc" -delete
	@find . -name "__pycache__" -type d -exec rm -rf {} +
	@rm -rf docs/build
	@rm -rf outputs/

reset: clean ## Reset development environment
	@rm -rf .venv

ci: ## Run CI-like checks locally
	@uv run pytest --cov=py2max
	@uv run mypy py2max
	@uv run ruff check py2max
	@cd docs && uv run sphinx-build -b html source build
