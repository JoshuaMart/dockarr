# Installation

## Prérequis

- Un hôte Linux (VPS ou serveur maison) avec [Docker Engine](https://docs.docker.com/engine/install/)
  et le plugin Docker Compose.
- `git` et `make`.

## Démarrage rapide

```bash
git clone https://github.com/JoshuaMart/dockarr.git
cd dockarr
make install
```

`make install` :

1. Crée `.env` à partir de `.env.example` (éditez-le, puis relancez la commande).
2. Crée l'arborescence des médias sous `data/`.
3. Démarre tous les services en arrière-plan (`make up`).
4. Lance le **bootstrap** (`make bootstrap`), qui provisionne et relie tous les
   services pour vous — voir [Configuration](configuration.md) pour le détail.

## Questions au premier lancement

Le premier bootstrap est interactif et pose quelques questions (les réponses
sont mémorisées et ne sont plus redemandées) :

| Question | Choix |
| --- | --- |
| **Language / Langue** | Langue d'UI appliquée à chaque service : English ou Français. |
| **Identifiant** | Un nom d'utilisateur partagé par tous les services (vide = aléatoire). |
| **Mode mot de passe** | Un mot de passe aléatoire partagé, ou un différent par service. |
| **Kavita** | Garder le serveur livres/BD/mangas, ou l'arrêter. |
| **Profilarr FR** | Optionnel : remplace la base Profilarr par une base FR curatée et pousse un profil de qualité vers Radarr/Sonarr. |

En exécution non interactive (sans TTY), les valeurs par défaut sont utilisées :
anglais, identifiant aléatoire, mot de passe par service, Kavita activé,
Profilarr FR désactivé.

## Identifiants

Le bootstrap génère les identifiants et les stocke dans
`secrets/credentials.json` (gitignoré, `chmod 600`). Affichez-les à tout moment :

```bash
make creds
```

## Configurer `.env`

| Variable | Description |
| --- | --- |
| `PUID` / `PGID` | Utilisateur/groupe propriétaire des configs & médias. `id` pour les trouver. |
| `TZ` | Fuseau horaire, ex. `Europe/Paris`. |
| `DOCKARR_CONFIG` | Où sont stockées les configs (défaut `./config`). |
| `DOCKARR_DATA` | Arbre partagé téléchargements + médias (défaut `./data`). |
| `DOCKARR_DOMAIN` | Domaine de base pour le reverse proxy. |
| `CADDY_EMAIL` | Email pour les certificats Let's Encrypt. |
| `KAVITA_PORT` | Port hôte de Kavita (mettez `5001` sur macOS — AirPlay occupe `:5000`). |

!!! tip "Hardlinks"
    Gardez téléchargements et médias sous le **même** arbre `DOCKARR_DATA`
    (`/data/torrents` et `/data/media`). Radarr/Sonarr peuvent ainsi déplacer
    les fichiers par hardlink au lieu de les copier — instantané et sans
    espace disque supplémentaire.

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
enregistrement DNS wildcard vers l'hôte et renseignez `DOCKARR_DOMAIN` — voir
[Configuration](configuration.md).
