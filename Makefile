# Dockarr — management commands
# Usage: `make <target>` (run `make help` to list everything)

COMPOSE := docker compose

.DEFAULT_GOAL := help

.PHONY: help install up down restart pull update logs ps config prune

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2}'

install: ## First-time setup: create .env and data folders, then start the stack
	@test -f .env || (cp .env.example .env && echo "Created .env — edit it then re-run 'make install'")
	@mkdir -p data/torrents data/media/movies data/media/tv data/media/books
	$(MAKE) up

up: ## Start (or create) all services in the background
	$(COMPOSE) up -d

down: ## Stop and remove all containers
	$(COMPOSE) down

restart: ## Restart all services
	$(COMPOSE) restart

pull: ## Pull the image versions pinned in docker-compose.yml
	$(COMPOSE) pull

update: ## GitOps update: fetch repo changes, pull pinned images, recreate
	git pull --ff-only
	$(COMPOSE) pull
	$(COMPOSE) up -d
	$(MAKE) prune

logs: ## Tail logs of all services (use `make logs s=radarr` for one)
	$(COMPOSE) logs -f $(s)

ps: ## Show status of all services
	$(COMPOSE) ps

config: ## Validate and render the merged compose configuration
	$(COMPOSE) config

prune: ## Remove dangling images left over after an update
	docker image prune -f
