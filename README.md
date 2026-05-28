# Dockarr

> Deploy, auto-configure and keep up to date a complete self-hosted **\*arr** media stack with Docker Compose.

📖 [Documentation](https://JoshuaMart.github.io/dockarr/) · 🇫🇷 [Lire en français](README.fr.md)

Dockarr brings up the whole *arr ecosystem — torrent client, indexers, movies,
TV, books, requests and media servers — behind a single reverse proxy, and
**wires every service together for you**. A single `make install` provisions
every account, connects the apps (download client, Prowlarr ↔ Radarr/Sonarr,
Profilarr, Seerr) and creates the media libraries. The only manual step is
adding your own indexers in Prowlarr.

Updates follow a **GitOps** flow — image versions are pinned in
`docker-compose.yml`, [Renovate](https://JoshuaMart.github.io/dockarr/updates/)
proposes bumps as pull requests, and the server applies merged changes with a
single `make update`.

## Stack

| Service | Role | Port |
| --- | --- | --- |
| [qBittorrent](https://www.qbittorrent.org/) | Torrent client | 8080 |
| [QUI](https://github.com/autobrr/qui) | Modern web UI for qBittorrent | 7476 |
| [Prowlarr](https://wiki.servarr.com/prowlarr) | Indexer manager | 9696 |
| [Radarr](https://wiki.servarr.com/radarr) | Movies | 7878 |
| [Sonarr](https://wiki.servarr.com/sonarr) | TV shows | 8989 |
| [Profilarr](https://github.com/Dictionarry-Hub/profilarr) | Quality profiles & custom formats sync | 6868 |
| [Seerr](https://github.com/seerr-team/seerr) | Media requests & discovery | 5055 |
| [Jellyfin](https://jellyfin.org/) | Media server (video) | 8096 |
| [Kavita](https://www.kavitareader.com/) | Media server (books / comics / manga) | 5000 |

A [Caddy](https://caddyserver.com/) reverse proxy fronts every service with
automatic HTTPS under `<service>.yourdomain`.

## Features

- **Automated setup** — `make install` provisions and connects every service
  headlessly: credentials, download clients, root folders, Prowlarr ↔
  Radarr/Sonarr app sync and media libraries.
- **Interactive & bilingual** — choose English or French on first run; the
  chosen language is applied to each service UI.
- **Optional French profiles** — opt in to wipe the Profilarr database, clone a
  curated French one and push its quality profiles to Radarr/Sonarr and Seerr.
- **Automatic HTTPS** — Caddy serves each service at `<service>.yourdomain` with
  Let's Encrypt certificates.
- **Hardlink-friendly layout** — downloads and media share one tree, so imports
  are instant and use no extra space.
- **GitOps updates** — pinned versions, Renovate pull requests, one-command
  deploy, and instant rollback with `git revert`.

## Quick start

Requirements: a Linux host with [Docker Engine](https://docs.docker.com/engine/install/)
and the Compose plugin, plus `git` and `make`.

```bash
git clone https://github.com/JoshuaMart/dockarr.git
cd dockarr
make install
```

`make install` creates `.env` (edit it, then re-run the command), builds the
media folder tree, starts the stack and runs the interactive bootstrap that
configures every service. Generated credentials are saved to
`secrets/credentials.json` — print them with `make creds`.

## Common commands

```bash
make up        # start everything
make down      # stop everything
make ps        # status
make logs      # tail all logs  (make logs s=radarr for one service)
make update    # GitOps update: git pull + compose pull + up
make creds     # show generated service credentials
make reset     # wipe config + secrets for a clean reinstall (keeps media)
```

Run `make help` for the full list, or `make bootstrap m=<service>` to
re-provision a single service.

## Documentation

Full guides live at **<https://JoshuaMart.github.io/dockarr/>**:

- [Installation](https://JoshuaMart.github.io/dockarr/installation/) — requirements and first run
- [Configuration](https://JoshuaMart.github.io/dockarr/configuration/) — services, reverse proxy and HTTPS
- [Updates](https://JoshuaMart.github.io/dockarr/updates/) — the GitOps / Renovate workflow
- [VPN](https://JoshuaMart.github.io/dockarr/vpn/) — routing qBittorrent through Gluetun
