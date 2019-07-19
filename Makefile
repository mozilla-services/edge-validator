.PHONY: build

build:
	docker build -t edge-validator:latest .

sync:
	pipenv sync --dev
	pipenv run python integration.py sync --ignore-data

test:
	pipenv run python -m pytest tests/

report:
	pipenv run python integration.py sync report

serve:
	docker run -e FLASK_ENV -p 8000:8000 -it edge-validator:latest

shell:
	docker run -p 8000:8000 -it edge-validator:latest pipenv shell
