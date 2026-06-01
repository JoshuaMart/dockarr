# Configuration

`make install` a déjà relié la stack via l'étape **bootstrap** : les comptes
sont créés, les services connectés et les bibliothèques existent. Cette page
liste ce qui a été configuré automatiquement, l'unique étape qui vous reste, et
comment tout exposer en HTTPS.

!!! info "Identifiants"
    Tous les services partagent l'identifiant et le mot de passe choisis au
    premier lancement. Affichez-les avec `make creds` (stockés dans
    `secrets/credentials.json`).

## Ce que le bootstrap configure

| Service | Fait automatiquement |
| --- | --- |
| **qBittorrent** | Compte, dossier `/data/torrents`, Automatic TMM, catégories `radarr`/`sonarr`. |
| **QUI** | Compte admin, instance qBittorrent enregistrée. |
| **Radarr / Sonarr** | Compte + auth par formulaire, client de téléchargement qBittorrent, dossier racine (`/data/media/movies`, `/data/media/tv`). |
| **Prowlarr** | Compte + auth par formulaire, Radarr & Sonarr enregistrés comme applications (les indexeurs s'y synchronisent automatiquement). |
| **Profilarr** | Compte, Radarr/Sonarr enregistrés comme cibles de sync. En option, la base FR + un profil de qualité (voir plus bas). |
| **Seerr** | Lié à Jellyfin, Radarr & Sonarr ajoutés comme serveurs par défaut. |
| **Jellyfin** | Admin + assistant de configuration, bibliothèques films et séries (`Films` / `Séries` en français, ou `Movies` / `TV Shows` en anglais). |
| **Kavita** | Admin, bibliothèques `Manga` / `Comics` / `BD` / `Livres` (sauf si désactivé au premier lancement). |

Re-jouez un service avec `make bootstrap m=<service>` ; c'est idempotent.

## La seule étape manuelle : les indexeurs

Le bootstrap connecte Prowlarr à Radarr/Sonarr mais n'ajoute **pas** les
indexeurs à votre place (ils sont propres à vos trackers). Pour terminer :

1. Ouvrez **Prowlarr** (`http://IP_SERVEUR:9696` ou `prowlarr.votredomaine`),
   connectez-vous avec `make creds`.
2. **Settings → Indexers → Add indexer** et ajoutez vos trackers.

Comme Radarr et Sonarr sont déjà enregistrés comme applications Prowlarr
(`fullSync`), chaque indexeur ajouté leur est poussé automatiquement, sans rien
d'autre à configurer.

## Profils de qualité (Profilarr FR)

Si vous avez accepté **Profilarr FR** au premier lancement, une base FR curatée
est clonée et son profil de qualité choisi (plus custom formats, nommage et
delay profiles) est synchronisé vers Radarr et Sonarr, et Seerr l'utilise par
défaut. Sinon, Radarr/Sonarr gardent leur profil intégré `Any` et vous pouvez
curer vos profils vous-même dans Profilarr (`:6868`).

## Réseau interne

Les services communiquent entre eux via le réseau Docker interne `dockarr` par
nom de conteneur. Si vous câblez quelque chose à la main, utilisez toujours
`http://<service>:<port>` (ex. `http://radarr:7878`), jamais `localhost`.

## Reverse proxy (Caddy)

[Caddy](https://caddyserver.com/) place chaque service sur un sous-domaine
dédié de `DOCKARR_DOMAIN` :

| Service | URL |
| --- | --- |
| Dashboard | `dashboard.votredomaine` |
| qBittorrent | `qbittorrent.votredomaine` |
| QUI | `qui.votredomaine` |
| Prowlarr | `prowlarr.votredomaine` |
| Radarr | `radarr.votredomaine` |
| Sonarr | `sonarr.votredomaine` |
| Profilarr | `profilarr.votredomaine` |
| Seerr | `seerr.votredomaine` |
| Jellyfin | `jellyfin.votredomaine` |
| Kavita | `kavita.votredomaine` |

Pour exposer la stack avec HTTPS automatique :

1. Pointez un **enregistrement DNS wildcard** `*.votredomaine` vers l'IP
   publique de l'hôte.
2. Renseignez `DOCKARR_DOMAIN` (ex. `media.example.com`) et `CADDY_EMAIL` dans
   `.env`.
3. `make restart`.

Caddy obtient et renouvelle alors les certificats Let's Encrypt tout seul, et
sert chaque service en HTTPS.

!!! note "Usage local"
    Avec la valeur par défaut `DOCKARR_DOMAIN=dockarr.local`, Caddy émet un
    certificat auto-signé : le navigateur affiche donc un avertissement, normal
    pour un usage purement local. Acceptez l'avertissement, ou utilisez
    simplement l'accès direct par port (`http://IP_SERVEUR:<port>`).

Ajoutez ou retirez des routes en éditant `caddy/Caddyfile`, puis `make restart`.
