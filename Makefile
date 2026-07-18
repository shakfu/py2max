
# Makefile for py2max project

.PHONY: help all build test test-verbose test-outputs coverage lint \
		typecheck qa docs docs-clean docs-serve docs-deploy install \
		dev clean reset ci format check-wheel publish-test publish

help: ## Show this help message
	@echo "Available commands:"
	@awk 'BEGIN {FS = ":.*##"; printf "\033[36m%-12s\033[0m %s\n", "Command", "Description"} /^[a-zA-Z_-]+:.*?##/ { printf "\033[36m%-12s\033[0m %s\n", $$1, $$2 }' $(MAKEFILE_LIST)

all: qa docs ## Run all checks and build everything

build: ## Build wheel
	@uv build

test: ## Run tests
	@uv run pytest

test-verbose: ## Run tests with verbose output
	@uv run pytest -v

test-outputs: ## Run tests writing all artifacts flat to build/test-outputs/
	@mkdir -p build
	@PY2MAX_TEST_OUTPUT_FLAT=1 uv run pytest

coverage: ## Generate coverage report
	@mkdir -p build
	@uv run pytest --cov-report html:build/coverage-html --cov=py2max tests

lint: ## Run code linting
	@uv run ruff check py2max --fix

format: ## Run code formatting
	@uv run ruff format py2max/

typecheck: ## Run type checking
	@uv run mypy py2max/

qa: lint test typecheck format 

docs: ## Build documentation
	@uv run --group docs mkdocs build --strict

docs-clean: ## Clean documentation build
	@rm -rf site

docs-serve: ## Build and serve documentation locally (live reload)
	@uv run --group docs mkdocs serve

docs-deploy: ## Build and deploy docs to GitHub Pages (gh-pages branch)
	@uv run --group docs mkdocs gh-deploy --force

gallery: ## Regenerate graph-layout gallery images (docs/assets/imgs)
	@uv run --extra graph python scripts/gen_layout_gallery.py

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
	@rm -rf site
	@rm -rf outputs/

reset: clean ## Reset development environment
	@rm -rf .venv

ci: ## Run CI-like checks locally
	@uv run pytest --cov=py2max
	@uv run mypy py2max
	@uv run ruff check py2max
	@uv run --group docs mkdocs build --strict

check-wheel: build ## Check wheel with twine
	@uv run twine check dist/*

publish-test: check-wheel ## Publish to PyPI Test
	@uv run twine upload --repository testpypi dist/*

publish: check-wheel ## Publish to PyPI
	@uv run twine upload dist/*
