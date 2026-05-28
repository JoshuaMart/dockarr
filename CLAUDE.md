# CLAUDE.md

Guidance for working in this repository.

## What this is

Dockarr is a self-hosted **\*arr** media stack run with Docker Compose
(`docker-compose.yml`), plus a Python **bootstrap** that headlessly provisions
and wires every service. Image versions are pinned and updated via Renovate +
`make update` (GitOps). User-facing docs live in `docs/` (MkDocs Material).

## Commands

```bash
make install              # first run: .env + folders + up + bootstrap
make up / down / restart  # lifecycle
make ps                   # status
make logs [s=radarr]      # tail logs (all, or one service)
make bootstrap [m=radarr] # (re)provision all services, or a single module
make creds                # print generated credentials
make reset                # wipe config/ + secrets/ for a clean reinstall (keeps data/)
make update               # GitOps: git pull + compose pull + up

.venv/bin/python -m scripts.bootstrap [module]   # what `make bootstrap` runs
.venv/bin/mkdocs build --strict                  # what CI runs for docs
```

There is no automated test suite. Validate bootstrap changes by running
`make bootstrap m=<module>` against the live stack — modules are idempotent, so
re-running is safe and is the normal way to test.

## Bootstrap architecture (`scripts/bootstrap/`)

- `core/registry.py` — `load_modules()` lists every module; `resolve_order()`
  topologically sorts them by their `depends`.
- `core/secrets.py` — `SecretStore` reads/writes `secrets/credentials.json`
  (per-service creds + flags `_language`, `_policy`, `_kavita`, `_profilarr_fr`).
- `core/config.py` — host ports and `service_url(name)`.
- `core/http.py` — `ApiClient` (thin `requests` wrapper: get/post/put/delete,
  `wait_until_up`).
- `core/prompts.py` — interactive first-run prompts (language, credential
  policy, Kavita, Profilarr FR). Non-interactive (no TTY) falls back to defaults.
- `modules/` — one `Module` per provisioning concern.

### Module pattern

Each module subclasses `Module` with `name`, `depends`, `is_done(ctx)` and
`run(ctx)`. `is_done` must reflect the desired end state so a finished module is
skipped; `run` must be **idempotent**. Register new modules in
`core/registry.py` (both the import and the returned list). Raise `RuntimeError`
with the HTTP status + `resp.text[:200]` on failure; report progress with
`ctx.log.info("  …")` (two-space indent).

## Conventions

- **Inter-service URLs** use Docker container names: `http://radarr:7878`, never
  `localhost`. The bootstrap reaches services from the host via
  `ctx.config.service_url()`.
- Some modules shell out to Docker (`docker exec/logs/stop`) for things not in
  an HTTP API (e.g. *arr API keys from `config.xml`, qBittorrent temp password,
  stopping Kavita). Container names match `container_name:` in compose.
- Caddy exposes each service at `<service>.${DOCKARR_DOMAIN}` (`caddy/Caddyfile`).
- **Docs are bilingual**: every `docs/x.md` (English) has a `docs/x.fr.md`
  (French) via `mkdocs-static-i18n`. IMPORTANT: edit both together.
- Commit messages: French, imperative, no prefix, with the
  `Co-Authored-By: Claude …` footer. Group commits by scope.

## Gotchas

- IMPORTANT: `config/`, `secrets/`, `data/` and `caddy/data/` are gitignored
  runtime state — never commit them.
- `secrets/credentials.json` holds real passwords — never print it into commits,
  PRs or docs.
- Kavita's `:5000` clashes with macOS AirPlay Receiver — `KAVITA_PORT=5001`.
- Profilarr v2 exposes a small REST API for databases, but pushing profiles to
  Radarr/Sonarr goes through **SvelteKit form actions** (`/arr/{id}/sync?/…`),
  not REST.
