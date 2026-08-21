.PHONY: install start wait smoke api graphql contracts integration database messaging resilience lint format typecheck test report gate stop clean

install:
	python -m pip install -e ".[dev,messaging,postgres]"

start:
	docker compose up -d --build

wait:
	python scripts/wait_for_services.py

smoke:
	pytest -m smoke

api:
	pytest -m api

graphql:
	pytest -m graphql

contracts:
	pytest -m contract

integration:
	pytest -m integration

database:
	pytest -m database

messaging:
	pytest -m messaging

resilience:
	pytest -m resilience

lint:
	ruff check .

format:
	ruff format .

typecheck:
	mypy .

test:
	pytest -n auto --junitxml=reports/junit.xml --html=reports/report.html --self-contained-html

report: test

gate:
	quality-gate --junit reports/junit.xml

stop:
	docker compose down -v

clean:
	python scripts/clean_results.py

