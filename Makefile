sync:
	pipenv sync --dev
	bash sync.sh

test:
	pipenv run python -m pytest tests/

report:
	pipenv run python report_integration.py