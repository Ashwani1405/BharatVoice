.PHONY: up down logs migrate shell test-be install dev build clean lint fe-shell

up:
	docker compose up --build -d

down:
	docker compose down

logs:
	docker compose logs -f backend

migrate:
	docker compose exec db psql -U postgres -d bharatvoice -f /migrations/001_initial.sql

shell:
	docker compose exec backend bash

test-be:
	docker compose exec backend pytest tests/ -v

install:
	pnpm install

dev:
	pnpm dev

build:
	pnpm build

clean:
	pnpm clean

lint:
	pnpm lint

fe-shell:
	docker compose exec frontend sh
