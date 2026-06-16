.PHONY: install bootstrap pipeline evidence serve test docker clean

install:
	pip install -r requirements.txt

bootstrap:
	python scripts/run_pipeline.py --bootstrap

pipeline:
	python scripts/run_pipeline.py

evidence:
	python scripts/generate_evidence.py

serve:
	uvicorn src.api.main:app --reload --port 8000

test:
	pytest tests/ -q

docker:
	docker compose up --build

clean:
	rm -rf data/raw/* data/curated/*
