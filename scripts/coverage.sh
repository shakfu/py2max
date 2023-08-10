mkdir -p outputs
pytest --cov-report html:outputs/_covhtml --cov=py2max tests
