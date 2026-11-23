.PHONY: up down logs test migrate api

up:
	docker compose up --build

down:
	docker compose down

logs:
	docker compose logs -f api

test:
	cd backend && pytest -q

migrate:
	cd backend && alembic upgrade head

api:
	cd backend && uvicorn app.main:app --reload
