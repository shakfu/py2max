
.PHONY: all build test coverage mypy clean reset

all: build

build:
	@uv build

test:
	@uv run pytest

coverage:
	@mkdir -p outputs
	@uv run pytest --cov-report html:outputs/_covhtml --cov=py2max tests

mypy:
	@uv run mypy py2max

lint:
	@uv run ruff check .
	@uv run ruff format .

clean:
	@rm -rf outputs
	@rm -rf .*_cache
	@find . -name __pycache__ -type d -exec rm -rf {} +

reset: clean
	@rm -rf .venv
