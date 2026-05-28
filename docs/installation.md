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
3. Starts every service in the background.

## Configure `.env`

| Variable | Description |
| --- | --- |
| `PUID` / `PGID` | User/group that own config & media. Run `id` to find yours. |
| `TZ` | Timezone, e.g. `Europe/Paris`. |
| `DOCKARR_CONFIG` | Where service config is stored (default `./config`). |
| `DOCKARR_DATA` | Shared downloads + media tree (default `./data`). |
| `DOCKARR_DOMAIN` | Base domain for the reverse proxy. |
| `CADDY_EMAIL` | Email for Let's Encrypt certificates. |

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
make update    # git pull + docker compose pull + up -d
```

## Access

Direct access by port (e.g. `http://SERVER_IP:7878` for Radarr) works out of
the box. For nice HTTPS URLs (`radarr.yourdomain`) point a wildcard DNS record
at the host and set `DOCKARR_DOMAIN` — see [Configuration](configuration.md).
