# Dockarr — management commands
# Usage: `make <target>` (run `make help` to list everything)

COMPOSE := docker compose
VENV := .venv
PYTHON := $(VENV)/bin/python
BOOTSTRAP_REQS := scripts/bootstrap/requirements.txt

.DEFAULT_GOAL := help

.PHONY: help install up down restart pull update logs ps config prune bootstrap creds reset

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2}'

install: ## First-time setup: create .env, data folders, start the stack, provision
	@test -f .env || (cp .env.example .env && echo "Created .env — edit it then re-run 'make install'")
	@mkdir -p data/torrents/movies data/torrents/tv data/torrents/books \
		data/media/movies data/media/tv \
		data/media/books/manga data/media/books/comics data/media/books/bd \
		data/media/books/livres
	$(MAKE) up
	$(MAKE) bootstrap

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

$(VENV)/.installed: $(BOOTSTRAP_REQS)
	python3 -m venv $(VENV)
	$(PYTHON) -m pip install -q --upgrade pip
	$(PYTHON) -m pip install -q -r $(BOOTSTRAP_REQS)
	@touch $@

bootstrap: $(VENV)/.installed ## Provision & wire services (make bootstrap m=qbittorrent for one)
	$(PYTHON) -m scripts.bootstrap $(m)

creds: ## Print stored service credentials
	@test -f secrets/credentials.json && cat secrets/credentials.json || echo "No credentials yet — run 'make bootstrap'"

reset: ## Stop the stack and wipe secrets/ + config/ for a clean re-install (keeps media in data/)
	@printf 'This STOPS the stack and DELETES secrets/ and config/ (service settings).\nMedia in data/ is kept. Continue? [y/N] '; \
	read ans; \
	case "$$ans" in [yY]) ;; *) echo "Aborted."; exit 1;; esac; \
	$(COMPOSE) down; \
	rm -rf secrets config; \
	mkdir -p config; touch config/.gitkeep; \
	echo "Reset done — run 'make install' for a clean setup."
