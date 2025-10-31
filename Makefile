.PHONY: backend-install frontend-install test lint

backend-install:
cd backend && pip install -e .[dev]

frontend-install:
cd frontend && npm install

lint:
cd backend && ruff check src
cd backend && black --check src
cd backend && pytest



test:
	cd backend && pytest
