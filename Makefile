.PHONY: dev test seed lint build up down

dev-backend:
	.\.venv\Scripts\uvicorn.exe backend.app.main:app --reload --port 8000

dev-frontend:
	cd frontend && npm run dev

dev:
	@echo "Run 'make dev-backend' and 'make dev-frontend' in separate terminals."

test-backend:
	.\.venv\Scripts\pytest.exe -v backend/app/tests

test: test-backend

seed:
	.\.venv\Scripts\python.exe -m backend.app.db.seed

lint:
	cd frontend && npm run build
	.\.venv\Scripts\python.exe -m compileall backend/app

up:
	docker compose up -d

down:
	docker compose down

