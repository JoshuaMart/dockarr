# Configuration

Une fois la stack démarrée, reliez les services entre eux, dans cet ordre.

## 1. qBittorrent

- Identifiant par défaut `admin` / mot de passe temporaire affiché dans les
  logs : `make logs s=qbittorrent`.
- Définissez le dossier de téléchargement sur `/data/torrents`.
- Vous pouvez le piloter depuis **QUI** (`:7476`) pour une interface
  multi-instances plus agréable.

## 2. Prowlarr (indexeurs)

- Ajoutez vos indexeurs/trackers.
- Dans **Settings → Apps**, ajoutez Radarr et Sonarr pour que les indexeurs s'y
  synchronisent automatiquement. Utilisez les hôtes internes
  `http://radarr:7878` et `http://sonarr:8989` avec la clé API de chaque app.

## 3. Radarr & Sonarr

- Ajoutez un **client de téléchargement** → qBittorrent sur
  `http://qbittorrent:8080`.
- Définissez le **dossier racine** sur `/data/media/movies` (Radarr) et
  `/data/media/tv` (Sonarr).

## 4. Profilarr (profils de qualité)

- Pointez Profilarr (`:6868`) vers Radarr/Sonarr pour importer et synchroniser
  des profils de qualité et custom formats maintenus à jour.

## 5. Seerr (demandes)

- Connectez-le à Jellyfin et à Radarr/Sonarr (`http://radarr:7878`,
  `http://sonarr:8989`) pour que les demandes des utilisateurs soient envoyées
  à la bonne app.

## 6. Jellyfin & Kavita

- **Jellyfin** (`:8096`) : ajoutez des bibliothèques depuis `/media/movies` et
  `/media/tv`.
- **Kavita** (`:5000`) : ajoutez une bibliothèque depuis `/books`.

## Reverse proxy (Caddy)

Les services communiquent entre eux via le réseau Docker interne `dockarr` par
nom de conteneur : utilisez donc toujours `http://<service>:<port>` dans les
réglages ci-dessus — jamais `localhost`.

Pour les exposer publiquement en HTTPS :

1. Créez un enregistrement DNS wildcard `*.votredomaine` → IP de l'hôte.
2. Renseignez `DOCKARR_DOMAIN` et `CADDY_EMAIL` dans `.env`.
3. `make restart`.

Caddy sert alors `radarr.votredomaine`, `jellyfin.votredomaine`, etc. avec des
certificats automatiques. Éditez `caddy/Caddyfile` pour ajouter ou retirer des
routes.
