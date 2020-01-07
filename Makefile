.PHONY: build

build:
	docker build -t edge-validator:latest .

sync:
	python integration.py sync --ignore-data

test:
	pytest tests/

report:
	python integration.py sync report

serve:
	docker run -e FLASK_ENV -p 8000:8000 -it edge-validator:latest

shell:
	docker run -p 8000:8000 -it edge-validator:latest bash
