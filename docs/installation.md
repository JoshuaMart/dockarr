# Installation

## Requirements

- A Linux host (VPS or home server) with [Docker Engine](https://docs.docker.com/engine/install/)
  and the Docker Compose plugin.
- `git` and `make`.

## Quick start

```bash
git clone https://github.com/JoshuaMart/dockarr.git
cd dockarr
make install
```

`make install`:

1. Creates `.env` from `.env.example` (edit it, then re-run the command).
2. Creates the media folder tree under `data/`.
3. Starts every service in the background (`make up`).
4. Runs the **bootstrap** (`make bootstrap`), which provisions and wires every
   service for you — see [Configuration](configuration.md) for the details.

## First-run prompts

The first bootstrap is interactive and asks a few questions (answers are stored
and never asked again):

| Prompt | Choice |
| --- | --- |
| **Language / Langue** | UI language applied to every service: English or Français. |
| **Service username** | A shared username for all services (blank = random). |
| **Password mode** | One shared random password, or a different one per service. |
| **Kavita** | Keep the books/comics/manga server, or stop it. |
| **Profilarr FR** | Optionally wipe the Profilarr database, clone a curated French one and push a quality profile to Radarr/Sonarr. |

On a non-interactive run (no TTY) the safe defaults are used: English, a random
username, a per-service password, Kavita enabled, Profilarr FR disabled.

## Credentials

Bootstrap generates the credentials and stores them in `secrets/credentials.json`
(gitignored, `chmod 600`). Print them anytime:

```bash
make creds
```

## Configure `.env`

| Variable | Description |
| --- | --- |
| `PUID` / `PGID` | User/group that own config & media. Run `id` to find yours. |
| `TZ` | Timezone, e.g. `Europe/Paris`. |
| `DOCKARR_CONFIG` | Where service config is stored (default `./config`). |
| `DOCKARR_DATA` | Shared downloads + media tree (default `./data`). |
| `DOCKARR_DOMAIN` | Base domain for the reverse proxy. |
| `CADDY_EMAIL` | Email for Let's Encrypt certificates. |
| `KAVITA_PORT` | Host port for Kavita (use `5001` on macOS — AirPlay grabs `:5000`). |

!!! tip "Hardlinks"
    Keep downloads and media under the **same** `DOCKARR_DATA` tree
    (`/data/torrents` and `/data/media`). This lets Radarr/Sonarr move files
    by hardlink instead of copying — instant and space-free.

## Daily commands

```bash
make up        # start everything
make down      # stop everything
make ps        # status
make logs      # tail all logs  (make logs s=radarr for one service)
make creds     # print stored service credentials
make update    # git pull + docker compose pull + up -d
make reset     # wipe config + secrets for a clean reinstall (keeps media)
```

Re-provision a single service with `make bootstrap m=<service>` (e.g.
`make bootstrap m=radarr`); the bootstrap is idempotent and skips anything
already configured.

## Access

Direct access by port (e.g. `http://SERVER_IP:7878` for Radarr) works out of
the box. For nice HTTPS URLs (`radarr.yourdomain`) point a wildcard DNS record
at the host and set `DOCKARR_DOMAIN` — see [Configuration](configuration.md).
