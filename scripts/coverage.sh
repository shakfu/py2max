mkdir -p outputs
uv run pytest --cov-report html:outputs/_covhtml \
	--cov=py2max \
	--cov-report term-missing \
	--cov-fail-under 95 tests
