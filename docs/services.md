# Services

| Service | Image | Internal URL | Host port |
| --- | --- | --- | --- |
| qBittorrent | `lscr.io/linuxserver/qbittorrent` | `http://qbittorrent:8080` | 8080 |
| QUI | `ghcr.io/autobrr/qui` | `http://qui:7476` | 7476 |
| Prowlarr | `lscr.io/linuxserver/prowlarr` | `http://prowlarr:9696` | 9696 |
| Radarr | `lscr.io/linuxserver/radarr` | `http://radarr:7878` | 7878 |
| Sonarr | `lscr.io/linuxserver/sonarr` | `http://sonarr:8989` | 8989 |
| Profilarr | `ghcr.io/dictionarry-hub/profilarr` | `http://profilarr:6868` | 6868 |
| Seerr | `ghcr.io/seerr-team/seerr` | `http://seerr:5055` | 5055 |
| Jellyfin | `lscr.io/linuxserver/jellyfin` | `http://jellyfin:8096` | 8096 |
| Kavita | `lscr.io/linuxserver/kavita` | `http://kavita:5000` | 5000 |
| Dashboard | `php:8.5-apache` | `http://dashboard:80` | 8081 |
| Caddy | `caddy` | — | 80 / 443 |

## Storage layout

```text
${DOCKARR_DATA}/
├── torrents/              # qBittorrent download dir (movies/ tv/ books/)
└── media/
    ├── movies/            # Radarr  → Jellyfin
    ├── tv/                # Sonarr  → Jellyfin
    └── books/             # Kavita
        ├── manga/         #   library "Manga"
        ├── comics/        #   library "Comics"
        ├── bd/            #   library "BD"
        └── livres/        #   library "Livres"

${DOCKARR_CONFIG}/
├── qbittorrent/  qui/  prowlarr/  radarr/  sonarr/
└── profilarr/  seerr/  jellyfin/  kavita/
```

Each service mounts its own `${DOCKARR_CONFIG}/<service>` directory at
`/config`, so all state is persisted on the host and survives container
recreation.

## What each service does

- **qBittorrent** downloads torrents into `/data/torrents`.
- **QUI** is an alternative, modern web UI to manage one or more qBittorrent
  instances.
- **Prowlarr** centralises indexers and pushes them to Radarr/Sonarr.
- **Radarr** / **Sonarr** grab movies / episodes and import them into the
  media library via hardlink.
- **Profilarr** builds and synchronises quality profiles & custom formats.
- **Seerr** lets users browse and request content; approved requests flow to
  Radarr/Sonarr.
- **Jellyfin** streams the video library.
- **Kavita** serves books, comics and manga.
- **Dashboard** is the landing page that lists every service with a live
  up/down status. See [Dashboard](dashboard.md).
