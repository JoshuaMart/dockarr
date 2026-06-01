# Dockarr — management commands
# Usage: `make <target>` (run `make help` to list everything)

COMPOSE := docker compose
VENV := .venv
PYTHON := $(VENV)/bin/python
BOOTSTRAP_REQS := scripts/bootstrap/requirements.txt

# Values read from .env (with fallbacks) — used to align host folder ownership
# with the PUID:PGID the LinuxServer.io containers run as.
PUID       := $(or $(shell grep -E '^PUID=' .env 2>/dev/null | tail -1 | cut -d= -f2),1000)
PGID       := $(or $(shell grep -E '^PGID=' .env 2>/dev/null | tail -1 | cut -d= -f2),1000)
DATA_DIR   := $(or $(shell grep -E '^DOCKARR_DATA=' .env 2>/dev/null | tail -1 | cut -d= -f2),./data)
CONFIG_DIR := $(or $(shell grep -E '^DOCKARR_CONFIG=' .env 2>/dev/null | tail -1 | cut -d= -f2),./config)

.DEFAULT_GOAL := help

.PHONY: help install up down restart pull update logs ps config prune bootstrap creds reset fix-perms

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2}'

install: ## First-time setup: create .env, data folders, start the stack, provision
	@test -f .env || (cp .env.example .env; echo "Created .env, edit it then re-run 'make install'"; exit 1)
	@mkdir -p "$(DATA_DIR)"/torrents/movies "$(DATA_DIR)"/torrents/tv "$(DATA_DIR)"/torrents/books \
		"$(DATA_DIR)"/media/movies "$(DATA_DIR)"/media/tv \
		"$(DATA_DIR)"/media/books/manga "$(DATA_DIR)"/media/books/comics "$(DATA_DIR)"/media/books/bd \
		"$(DATA_DIR)"/media/books/livres
	$(MAKE) fix-perms
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

fix-perms: ## Align host data/config ownership with PUID:PGID (Linux bind mounts)
	@if [ "$$(uname)" = "Linux" ]; then \
		mkdir -p "$(DATA_DIR)" "$(CONFIG_DIR)"; \
		echo "Aligning $(DATA_DIR) + $(CONFIG_DIR) ownership to $(PUID):$(PGID)…"; \
		chown -R $(PUID):$(PGID) "$(DATA_DIR)" "$(CONFIG_DIR)" 2>/dev/null \
			|| sudo chown -R $(PUID):$(PGID) "$(DATA_DIR)" "$(CONFIG_DIR)" \
			|| echo "  ⚠ Could not chown — run: sudo chown -R $(PUID):$(PGID) $(DATA_DIR) $(CONFIG_DIR)"; \
	else \
		echo "Skipping chown (non-Linux host: Docker Desktop virtualises bind-mount ownership)."; \
	fi

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
