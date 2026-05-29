# Services

| Service | Image | URL interne | Port hôte |
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
| Dashboard | `php:8.3-apache` | `http://dashboard:80` | 8081 |
| Caddy | `caddy` | — | 80 / 443 |

## Organisation du stockage

```text
${DOCKARR_DATA}/
├── torrents/              # dossier de téléchargement qBittorrent (movies/ tv/ books/)
└── media/
    ├── movies/            # Radarr  → Jellyfin
    ├── tv/                # Sonarr  → Jellyfin
    └── books/             # Kavita
        ├── manga/         #   bibliothèque « Manga »
        ├── comics/        #   bibliothèque « Comics »
        ├── bd/            #   bibliothèque « BD »
        └── livres/        #   bibliothèque « Livres »

${DOCKARR_CONFIG}/
├── qbittorrent/  qui/  prowlarr/  radarr/  sonarr/
└── profilarr/  seerr/  jellyfin/  kavita/
```

Chaque service monte son propre dossier `${DOCKARR_CONFIG}/<service>` sur
`/config` : tout l'état est persisté sur l'hôte et survit à la recréation des
conteneurs.

## Rôle de chaque service

- **qBittorrent** télécharge les torrents dans `/data/torrents`.
- **QUI** est une interface web moderne alternative pour gérer une ou plusieurs
  instances qBittorrent.
- **Prowlarr** centralise les indexeurs et les pousse vers Radarr/Sonarr.
- **Radarr** / **Sonarr** récupèrent films / épisodes et les importent dans la
  bibliothèque par hardlink.
- **Profilarr** construit et synchronise les profils de qualité & custom
  formats.
- **Seerr** permet de parcourir et demander du contenu ; les demandes
  approuvées partent vers Radarr/Sonarr.
- **Jellyfin** diffuse la bibliothèque vidéo.
- **Kavita** sert les livres, BD et mangas.
- **Dashboard** est la page d'accueil qui liste tous les services avec un statut
  en ligne / hors ligne en direct. Voir [Dashboard](dashboard.md).
