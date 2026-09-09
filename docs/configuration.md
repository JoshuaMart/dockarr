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
| **qBittorrent** | Account, save path `/data/torrents`, Automatic TMM, `radarr`/`sonarr` + book (`bd`/`comics`/`manga`/`livres`) categories, run-on-complete script that hardlinks finished book downloads into the matching Kavita library. |
| **QUI** | Admin account, qBittorrent instance registered. |
| **Radarr / Sonarr** | Account + forms auth, qBittorrent download client, root folder (`/data/media/movies`, `/data/media/tv`). |
| **Prowlarr** | Account + forms auth, Radarr & Sonarr registered as applications (indexers sync to them automatically). |
| **Profilarr** | Account, Radarr/Sonarr registered as sync targets. Optionally the French database + a quality profile (see below). |
| **Seerr** | Linked to Jellyfin, Radarr & Sonarr added as default servers. |
| **Jellyfin** | Admin + setup wizard, movie and TV libraries (`Movies` / `TV Shows`, or `Films` / `Séries` when French is selected). |
| **Kavita** | Admin, `Manga` / `Comics` / `BD` / `Livres` libraries with embedded ComicInfo metadata, dashboard inclusion and folder watching enabled (unless disabled at first run). |
| **Radarr/Sonarr → Jellyfin** | A dedicated Jellyfin API key, a library-refresh connection on each arr, and a folder naming format Jellyfin can identify (see below). |

Re-run any single service with `make bootstrap m=<service>`; it is idempotent.

## The one manual step: indexers

Bootstrap connects Prowlarr to Radarr/Sonarr but it does **not** add indexers
for you (those are personal to your trackers). To finish:

1. Open **Prowlarr** (`https://prowlarr.yourdomain`, or `http://localhost:9696`
   from the host), log in with `make creds`.
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

## Jellyfin, media naming and library refresh

Two things have to be true for a finished download to show up correctly in
Jellyfin. The `jellyfin-connect` module handles both.

**1. Jellyfin has to be told to rescan.** Radarr and Sonarr each get a
`Jellyfin` connection (`jellyfin:8096`, *Update Library* on) that fires on
import, upgrade, rename and delete. Without it Jellyfin only notices new files
on its periodic scan, so a freshly imported season shows up as a series with
zero episodes and playback fails with *"No compatible streams are currently
available"*.

**2. Folders have to carry an id Jellyfin can parse.** Jellyfin ships
TheMovieDb as its only metadata provider and reads external ids written as
`[tmdbid-…]`. The Plex convention that the *arr community guides (and the
Profilarr media-management sync) use, `{tmdb-…}` / `{tvdb-…}`, is ignored by
Jellyfin: it falls back to a fuzzy title search and can match the wrong entry
entirely. So bootstrap pins the **folder** format:

| | Format |
| --- | --- |
| Radarr `movieFolderFormat` | `{Movie CleanTitle} ({Release Year}) [tmdbid-{TmdbId}]` |
| Sonarr `seriesFolderFormat` | `{Series TitleYear} [tmdbid-{TmdbId}]` |

Only the folder matters, Jellyfin identifies a library item from it and not
from the file name, so your file naming stays whatever Profilarr or you chose.
Existing libraries are migrated: any item still in an old-style folder is
renamed in place. That is a `rename()` on the same filesystem, so hardlinks
survive and torrents keep seeding.

!!! warning "Profilarr can overwrite the naming"
    The naming config is also owned by Profilarr's **Media Management** sync,
    which pushes the Plex convention. Bootstrap runs after it, so a full
    `make bootstrap` ends up correct. But if you trigger a Media Management
    sync by hand from the Profilarr UI, re-run `make bootstrap m=jellyfin-connect`
    afterwards.

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
    use. Either accept the warning, or reach the services by port from the
    host itself (`http://localhost:<port>`). From another machine that needs
    `DOCKARR_BIND=0.0.0.0` in `.env`, see [Installation](installation.md).

Add or remove routes by editing `caddy/Caddyfile`, then `make restart`.
