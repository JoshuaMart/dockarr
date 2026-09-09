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
| **qBittorrent** | Compte, dossier `/data/torrents`, Automatic TMM, catégories `radarr`/`sonarr` + livres (`bd`/`comics`/`manga`/`livres`), script exécuté à la fin du téléchargement qui hardlinke les livres terminés dans la bibliothèque Kavita correspondante. |
| **QUI** | Compte admin, instance qBittorrent enregistrée. |
| **Radarr / Sonarr** | Compte + auth par formulaire, client de téléchargement qBittorrent, dossier racine (`/data/media/movies`, `/data/media/tv`). |
| **Prowlarr** | Compte + auth par formulaire, Radarr & Sonarr enregistrés comme applications (les indexeurs s'y synchronisent automatiquement). |
| **Profilarr** | Compte, Radarr/Sonarr enregistrés comme cibles de sync. En option, la base FR + un profil de qualité (voir plus bas). |
| **Seerr** | Lié à Jellyfin, Radarr & Sonarr ajoutés comme serveurs par défaut. |
| **Jellyfin** | Admin + assistant de configuration, bibliothèques films et séries (`Films` / `Séries` en français, ou `Movies` / `TV Shows` en anglais). |
| **Kavita** | Admin, bibliothèques `Manga` / `Comics` / `BD` / `Livres` avec métadonnées ComicInfo, affichage sur l'Accueil et surveillance des dossiers activés (sauf si désactivé au premier lancement). |
| **Radarr/Sonarr → Jellyfin** | Une clé API Jellyfin dédiée, une connexion de rafraîchissement de bibliothèque sur chaque arr, et un format de dossier que Jellyfin sait identifier (voir plus bas). |

Re-jouez un service avec `make bootstrap m=<service>` ; c'est idempotent.

## La seule étape manuelle : les indexeurs

Le bootstrap connecte Prowlarr à Radarr/Sonarr mais n'ajoute **pas** les
indexeurs à votre place (ils sont propres à vos trackers). Pour terminer :

1. Ouvrez **Prowlarr** (`https://prowlarr.votredomaine`, ou
   `http://localhost:9696` depuis l'hôte), connectez-vous avec `make creds`.
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

## Jellyfin, nommage et rafraîchissement des bibliothèques

Deux conditions doivent être réunies pour qu'un téléchargement terminé
apparaisse correctement dans Jellyfin. Le module `jellyfin-connect` s'occupe des
deux.

**1. Il faut prévenir Jellyfin de rescanner.** Radarr et Sonarr reçoivent chacun
une connexion `Jellyfin` (`jellyfin:8096`, *Update Library* activé) déclenchée à
l'import, à l'upgrade, au renommage et à la suppression. Sans elle, Jellyfin ne
découvre les nouveaux fichiers qu'à son scan périodique : une saison fraîchement
importée apparaît alors comme une série à zéro épisode et la lecture échoue avec
*« Impossible de trouver une source multimédia valide à lire »*.

**2. Les dossiers doivent porter un identifiant que Jellyfin sait lire.**
Jellyfin n'embarque que TheMovieDb comme fournisseur de métadonnées et lit les
identifiants externes écrits `[tmdbid-…]`. La convention Plex utilisée par les
guides \*arr (et par le sync media management de Profilarr), `{tmdb-…}` /
`{tvdb-…}`, est ignorée par Jellyfin : il retombe sur une recherche floue par
titre et peut identifier une œuvre totalement différente. Le bootstrap fixe donc
le format de **dossier** :

| | Format |
| --- | --- |
| Radarr `movieFolderFormat` | `{Movie CleanTitle} ({Release Year}) [tmdbid-{TmdbId}]` |
| Sonarr `seriesFolderFormat` | `{Series TitleYear} [tmdbid-{TmdbId}]` |

Seul le dossier compte, Jellyfin identifie une œuvre à partir de lui et non du
nom de fichier : votre nommage de fichiers reste celui choisi par Profilarr ou
par vous. Les bibliothèques existantes sont migrées : toute œuvre encore dans un
dossier à l'ancien format est renommée sur place. C'est un `rename()` sur le même
système de fichiers, les hardlinks survivent et les torrents continuent de
seeder.

!!! warning "Profilarr peut écraser le nommage"
    La configuration de nommage appartient aussi au sync **Media Management** de
    Profilarr, qui pousse la convention Plex. Le bootstrap passe après lui, donc
    un `make bootstrap` complet finit correct. Mais si vous déclenchez un sync
    Media Management à la main depuis l'UI Profilarr, rejouez ensuite
    `make bootstrap m=jellyfin-connect`.

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
    pour un usage purement local. Acceptez l'avertissement, ou joignez les
    services par port depuis l'hôte lui-même (`http://localhost:<port>`) ;
    depuis une autre machine, cela demande `DOCKARR_BIND=0.0.0.0` dans `.env`,
    voir [Installation](installation.md).

Ajoutez ou retirez des routes en éditant `caddy/Caddyfile`, puis `make restart`.
