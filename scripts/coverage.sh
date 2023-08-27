mkdir -p outputs
pytest --cov-report html:outputs/_covhtml \
	--cov=py2max \
	--cov-report term-missing \
	--cov-fail-under 95 tests
