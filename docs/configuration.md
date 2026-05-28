# Configuration

Once the stack is running, wire the services together. Do it in this order.

## 1. qBittorrent

- Default login is `admin` / a temporary password printed in the logs:
  `make logs s=qbittorrent`.
- Set the download path to `/data/torrents`.
- Optionally manage it from **QUI** (`:7476`) for a nicer multi-instance UI.

## 2. Prowlarr (indexers)

- Add your indexers/trackers.
- Under **Settings → Apps**, add Radarr and Sonarr so indexers sync to them
  automatically. Use the internal hostnames `http://radarr:7878` and
  `http://sonarr:8989` and each app's API key.

## 3. Radarr & Sonarr

- Add a **download client** → qBittorrent at `http://qbittorrent:8080`.
- Set the **root folder** to `/data/media/movies` (Radarr) and
  `/data/media/tv` (Sonarr).

## 4. Profilarr (quality profiles)

- Point Profilarr (`:6868`) at Radarr/Sonarr to import and keep curated
  quality profiles and custom formats in sync.

## 5. Seerr (requests)

- Connect it to Jellyfin and to Radarr/Sonarr (`http://radarr:7878`,
  `http://sonarr:8989`) so user requests are sent to the right app.

## 6. Jellyfin & Kavita

- **Jellyfin** (`:8096`): add libraries from `/media/movies` and `/media/tv`.
- **Kavita** (`:5000`): add a library from `/books`.

## Reverse proxy (Caddy)

Services talk to each other over the internal `dockarr` Docker network by
container name, so always use `http://<service>:<port>` in the settings above —
never `localhost`.

To expose them publicly with HTTPS:

1. Create a wildcard DNS record `*.yourdomain` → your host IP.
2. Set `DOCKARR_DOMAIN` and `CADDY_EMAIL` in `.env`.
3. `make restart`.

Caddy then serves `radarr.yourdomain`, `jellyfin.yourdomain`, etc. with
automatic certificates. Edit `caddy/Caddyfile` to add or remove routes.
