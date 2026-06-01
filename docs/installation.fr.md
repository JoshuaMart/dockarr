# Installation

## Prérequis

- Un hôte Linux (VPS ou serveur maison) avec [Docker Engine](https://docs.docker.com/engine/install/)
  et le plugin Docker Compose.
- `git` et `make`.
- Python 3.9+ avec le module `venv` (sur Debian/Ubuntu : `apt install python3-venv`)
  (`make install` construit un virtualenv isolé pour lancer le bootstrap).

## Démarrage rapide

```bash
git clone https://github.com/JoshuaMart/dockarr.git
cd dockarr
cp .env.example .env
# éditez .env (par défaut, seulement DOCKARR_DOMAIN et CADDY_EMAIL), puis :
make install
```

`make install` enchaîne ensuite :

1. Crée l'arborescence des médias sous `data/`.
2. Démarre tous les services en arrière-plan (`make up`).
3. Lance le **bootstrap** (`make bootstrap`), qui provisionne et relie tous les
   services pour vous. Voir [Configuration](configuration.md) pour le détail.

(Si vous sautez l'étape `cp`, le premier `make install` crée seulement `.env`
puis s'arrête pour que vous l'éditiez ; relancez `make install` ensuite.)

## Questions au premier lancement

Le premier bootstrap est interactif et pose quelques questions (les réponses
sont mémorisées et ne sont plus redemandées) :

| Question | Choix |
| --- | --- |
| **Language / Langue** | Langue d'UI appliquée à chaque service : English ou Français. |
| **Identifiant** | Un nom d'utilisateur partagé par tous les services (vide = aléatoire). |
| **Mode mot de passe** | Un mot de passe aléatoire partagé, ou un différent par service. |
| **Kavita** | Garder le serveur livres/BD/mangas, ou l'arrêter. Un Kavita désactivé le reste après `make up` et `make update` (le choix est mémorisé automatiquement). |
| **VPN (Gluetun)** | Router qBittorrent à travers un VPN WireGuard. Si activé, le provider et les identifiants WireGuard sont demandés. Voir [VPN](vpn.md). |
| **Profilarr FR** | Optionnel : remplace la base Profilarr par une base FR curatée et pousse un profil de qualité vers Radarr/Sonarr. |

En exécution non interactive (sans TTY), les valeurs par défaut sont utilisées :
anglais, identifiant aléatoire, mot de passe par service, Kavita activé, VPN
désactivé, Profilarr FR désactivé.

## Identifiants

Le bootstrap génère les identifiants et les stocke dans
`secrets/credentials.json` (gitignoré, `chmod 600`). Affichez-les à tout moment :

```bash
make creds
```

## Configurer `.env`

!!! tip "Ce qu'il faut éditer de base"
    Les valeurs par défaut conviennent telles quelles pour une installation
    locale. Pour exposer la stack sur votre propre domaine avec HTTPS, les deux
    seules variables à renseigner sont **`DOCKARR_DOMAIN`** et **`CADDY_EMAIL`**.
    Tout le reste peut garder sa valeur par défaut.

| Variable | Description |
| --- | --- |
| `PUID` / `PGID` | Utilisateur/groupe propriétaire des configs & médias. `id` pour les trouver. |
| `TZ` | Fuseau horaire, ex. `Europe/Paris`. |
| `DOCKARR_CONFIG` | Où sont stockées les configs (défaut `./config`). |
| `DOCKARR_DATA` | Arbre partagé téléchargements + médias (défaut `./data`). |
| `DOCKARR_DOMAIN` | Domaine de base pour le reverse proxy. |
| `CADDY_EMAIL` | Email pour les certificats Let's Encrypt. |
| `KAVITA_PORT` | Port hôte de Kavita (mettez `5001` sur macOS, où AirPlay occupe `:5000`). |
| `VPN_*` / `WIREGUARD_*` | Identifiants VPN, utilisés seulement quand le VPN est activé (voir [VPN](vpn.md)). |

!!! note "`COMPOSE_PROFILES` / `COMPOSE_FILE`"
    Le bootstrap gère ces deux variables pour vous, selon vos réponses au `make
    install` (Kavita activé/désactivé, VPN activé/désactivé). Le choix
    activé/désactivé se fait à la question d'installation, pas dans ce fichier —
    ne les éditez pas à la main.

!!! tip "Hardlinks"
    Gardez téléchargements et médias sous le **même** arbre `DOCKARR_DATA`
    (`/data/torrents` et `/data/media`). Radarr/Sonarr peuvent ainsi déplacer
    les fichiers par hardlink au lieu de les copier : instantané et sans
    espace disque supplémentaire.

!!! note "Propriété des fichiers (`PUID` / `PGID`)"
    Les services tournent sous le `PUID:PGID` défini dans `.env` (défaut
    `1000:1000`). Sous Linux, `make install` aligne automatiquement la propriété
    de `DOCKARR_DATA` et `DOCKARR_CONFIG` pour que les conteneurs puissent y
    écrire. Si vous avez créé les dossiers sous un autre utilisateur (ex.
    `root`) et rencontrez une erreur *« not writable by user 'abc' »*,
    corrigez-la avec :
    ```bash
    make fix-perms
    # ou manuellement :
    sudo chown -R 1000:1000 ./data ./config
    ```
    Sous macOS cette étape est ignorée : Docker Desktop virtualise la propriété
    des bind mounts, le problème ne se pose donc jamais.

## Commandes du quotidien

```bash
make up        # tout démarrer
make down      # tout arrêter
make ps        # statut
make logs      # suivre tous les logs  (make logs s=radarr pour un service)
make creds     # afficher les identifiants stockés
make update    # git pull + docker compose pull + up -d
make reset     # effacer config + secrets pour une réinstallation propre (garde les médias)
```

Re-provisionnez un seul service avec `make bootstrap m=<service>` (ex.
`make bootstrap m=radarr`) ; le bootstrap est idempotent et saute ce qui est
déjà configuré.

## Accès

L'accès direct par port (ex. `http://IP_SERVEUR:7878` pour Radarr) fonctionne
immédiatement. Pour de belles URLs HTTPS (`radarr.votredomaine`), pointez un
enregistrement DNS wildcard vers l'hôte et renseignez `DOCKARR_DOMAIN` ; voir
[Configuration](configuration.md).
