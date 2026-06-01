# Configuration

`make install` already wired the stack together through the **bootstrap** step:
accounts are created, services are connected and the media libraries exist.
This page lists what was set up automatically, the single step left to you, and
how to expose everything behind HTTPS.

!!! info "Credentials"
    All services share the username and password chosen at first run. Print
    them with `make creds` (stored in `secrets/credentials.json`).

## What bootstrap configures

| Service | Done automatically |
| --- | --- |
| **qBittorrent** | Account, save path `/data/torrents`, Automatic TMM, `radarr`/`sonarr` categories. |
| **QUI** | Admin account, qBittorrent instance registered. |
| **Radarr / Sonarr** | Account + forms auth, qBittorrent download client, root folder (`/data/media/movies`, `/data/media/tv`). |
| **Prowlarr** | Account + forms auth, Radarr & Sonarr registered as applications (indexers sync to them automatically). |
| **Profilarr** | Account, Radarr/Sonarr registered as sync targets. Optionally the French database + a quality profile (see below). |
| **Seerr** | Linked to Jellyfin, Radarr & Sonarr added as default servers. |
| **Jellyfin** | Admin + setup wizard, movie and TV libraries (`Movies` / `TV Shows`, or `Films` / `Séries` when French is selected). |
| **Kavita** | Admin, `Manga` / `Comics` / `BD` / `Livres` libraries (unless disabled at first run). |

Re-run any single service with `make bootstrap m=<service>`; it is idempotent.

## The one manual step: indexers

Bootstrap connects Prowlarr to Radarr/Sonarr but it does **not** add indexers
for you (those are personal to your trackers). To finish:

1. Open **Prowlarr** (`http://SERVER_IP:9696` or `prowlarr.yourdomain`), log in
   with `make creds`.
2. **Settings → Indexers → Add indexer** and add your trackers.

Because Radarr and Sonarr are already registered as Prowlarr applications
(`fullSync`), every indexer you add is pushed to them automatically, with nothing
else to configure.

## Quality profiles (Profilarr FR)

If you accepted **Profilarr FR** at first run, a curated French database is
cloned and its chosen quality profile (plus custom formats, naming and delay
profiles) is synced to Radarr and Sonarr, and Seerr defaults to it. Otherwise
Radarr/Sonarr keep their built-in `Any` profile and you can curate profiles
yourself in Profilarr (`:6868`).

## Internal networking

Services reach each other over the internal `dockarr` Docker network by
container name. If you wire anything by hand, always use `http://<service>:<port>`
(e.g. `http://radarr:7878`), never `localhost`.

## Reverse proxy (Caddy)

[Caddy](https://caddyserver.com/) fronts every service on a dedicated
subdomain of `DOCKARR_DOMAIN`:

| Service | URL |
| --- | --- |
| Dashboard | `dashboard.yourdomain` |
| qBittorrent | `qbittorrent.yourdomain` |
| QUI | `qui.yourdomain` |
| Prowlarr | `prowlarr.yourdomain` |
| Radarr | `radarr.yourdomain` |
| Sonarr | `sonarr.yourdomain` |
| Profilarr | `profilarr.yourdomain` |
| Seerr | `seerr.yourdomain` |
| Jellyfin | `jellyfin.yourdomain` |
| Kavita | `kavita.yourdomain` |

To expose the stack with automatic HTTPS:

1. Point a **wildcard DNS record** `*.yourdomain` at your host's public IP.
2. Set `DOCKARR_DOMAIN` (e.g. `media.example.com`) and `CADDY_EMAIL` in `.env`.
3. `make restart`.

Caddy then obtains and renews Let's Encrypt certificates on its own, and serves
each service over HTTPS.

!!! note "Local use"
    With the default `DOCKARR_DOMAIN=dockarr.local` Caddy issues a self-signed
    certificate, so browsers warn about it; that is expected for local-only
    use. Either accept the warning, or just use direct port access
    (`http://SERVER_IP:<port>`).

Add or remove routes by editing `caddy/Caddyfile`, then `make restart`.
