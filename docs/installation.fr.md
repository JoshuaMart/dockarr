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
3. Démarre tous les services en arrière-plan.

## Configurer `.env`

| Variable | Description |
| --- | --- |
| `PUID` / `PGID` | Utilisateur/groupe propriétaire des configs & médias. `id` pour les trouver. |
| `TZ` | Fuseau horaire, ex. `Europe/Paris`. |
| `DOCKARR_CONFIG` | Où sont stockées les configs (défaut `./config`). |
| `DOCKARR_DATA` | Arbre partagé téléchargements + médias (défaut `./data`). |
| `DOCKARR_DOMAIN` | Domaine de base pour le reverse proxy. |
| `CADDY_EMAIL` | Email pour les certificats Let's Encrypt. |

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
make update    # git pull + docker compose pull + up -d
```

## Accès

L'accès direct par port (ex. `http://IP_SERVEUR:7878` pour Radarr) fonctionne
immédiatement. Pour de belles URLs HTTPS (`radarr.votredomaine`), pointez un
enregistrement DNS wildcard vers l'hôte et renseignez `DOCKARR_DOMAIN` — voir
[Configuration](configuration.md).
