# Dockarr

> Déployer, auto-configurer et maintenir à jour une stack média **\*arr**
> complète, auto-hébergée, avec Docker Compose.

📖 [Documentation](https://JoshuaMart.github.io/dockarr/) · 🇬🇧 [Read in English](README.md)

Dockarr met en place tout l'écosystème *arr — client torrent, indexeurs, films,
séries, livres, demandes et serveurs multimédias — derrière un unique reverse
proxy, et **relie tous les services entre eux pour vous**. Un seul
`make install` provisionne chaque compte, connecte les apps (client de
téléchargement, Prowlarr ↔ Radarr/Sonarr, Profilarr, Seerr) et crée les
bibliothèques. Seul l'ajout de vos propres indexeurs dans Prowlarr reste manuel.

Les mises à jour suivent un flux **GitOps** — les versions des images sont
épinglées dans `docker-compose.yml`,
[Renovate](https://JoshuaMart.github.io/dockarr/fr/updates/) propose les montées
de version en pull requests, et le serveur applique les changements fusionnés
avec un simple `make update`.

## La stack

| Service | Rôle | Port |
| --- | --- | --- |
| [qBittorrent](https://www.qbittorrent.org/) | Client torrent | 8080 |
| [QUI](https://github.com/autobrr/qui) | Interface web moderne pour qBittorrent | 7476 |
| [Prowlarr](https://wiki.servarr.com/prowlarr) | Gestionnaire d'indexeurs | 9696 |
| [Radarr](https://wiki.servarr.com/radarr) | Films | 7878 |
| [Sonarr](https://wiki.servarr.com/sonarr) | Séries | 8989 |
| [Profilarr](https://github.com/Dictionarry-Hub/profilarr) | Sync des profils de qualité & custom formats | 6868 |
| [Seerr](https://github.com/seerr-team/seerr) | Demandes & découverte de contenu | 5055 |
| [Jellyfin](https://jellyfin.org/) | Serveur multimédia (vidéo) | 8096 |
| [Kavita](https://www.kavitareader.com/) | Serveur multimédia (livres / BD / mangas) | 5000 |

Un reverse proxy [Caddy](https://caddyserver.com/) place chaque service derrière
du HTTPS automatique sous `<service>.votredomaine`.

## Points forts

- **Installation automatisée** — `make install` provisionne et relie chaque
  service sans intervention : identifiants, clients de téléchargement, dossiers
  racines, sync Prowlarr ↔ Radarr/Sonarr et bibliothèques.
- **Interactif & bilingue** — choisissez le français ou l'anglais au premier
  lancement ; la langue choisie est appliquée à l'UI de chaque service.
- **Profils français optionnels** — au choix, remplace la base Profilarr par une
  base FR curatée et pousse ses profils de qualité vers Radarr/Sonarr et Seerr.
- **HTTPS automatique** — Caddy sert chaque service sous `<service>.votredomaine`
  avec des certificats Let's Encrypt.
- **Arborescence compatible hardlinks** — téléchargements et médias partagent un
  seul arbre, donc les imports sont instantanés et ne consomment pas d'espace.
- **Mises à jour GitOps** — versions épinglées, pull requests Renovate, déploiement
  en une commande, et rollback instantané avec `git revert`.

## Démarrage rapide

Prérequis : un hôte Linux avec [Docker Engine](https://docs.docker.com/engine/install/)
et le plugin Compose, ainsi que `git` et `make`.

```bash
git clone https://github.com/JoshuaMart/dockarr.git
cd dockarr
make install
```

`make install` crée `.env` (éditez-le, puis relancez la commande), construit
l'arborescence des médias, démarre la stack et lance le bootstrap interactif qui
configure chaque service. Les identifiants générés sont enregistrés dans
`secrets/credentials.json` — affichez-les avec `make creds`.

## Commandes courantes

```bash
make up        # tout démarrer
make down      # tout arrêter
make ps        # état des services
make logs      # suivre les logs  (make logs s=radarr pour un seul service)
make update    # mise à jour GitOps : git pull + compose pull + up
make creds     # afficher les identifiants générés
make reset     # effacer config + secrets pour une réinstallation propre (garde les médias)
```

Lancez `make help` pour la liste complète, ou `make bootstrap m=<service>` pour
re-provisionner un seul service.

## Documentation

Les guides complets sont sur **<https://JoshuaMart.github.io/dockarr/fr/>** :

- [Installation](https://JoshuaMart.github.io/dockarr/fr/installation/) — prérequis et premier lancement
- [Configuration](https://JoshuaMart.github.io/dockarr/fr/configuration/) — services, reverse proxy et HTTPS
- [Mises à jour](https://JoshuaMart.github.io/dockarr/fr/updates/) — le workflow GitOps / Renovate
- [VPN](https://JoshuaMart.github.io/dockarr/fr/vpn/) — faire passer qBittorrent par Gluetun
