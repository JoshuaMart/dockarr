# VPN (Gluetun)

Vous pouvez faire passer **qBittorrent** par un VPN pour que tout le trafic
torrent soit tunnelisé. Dockarr utilise [Gluetun](https://github.com/qdm12/gluetun)
pour cela.

!!! warning "Gluetun nécessite un abonnement VPN"
    Gluetun se connecte à un fournisseur VPN (WireGuard ou OpenVPN). Sans
    identifiants, aucun tunnel n'est établi et son kill-switch bloque tout le
    trafic de qBittorrent. N'activez cette option qu'une fois votre abonnement
    VPN en main.

## Activer

Répondez **oui** à la question VPN au `make install`, ou lancez-la plus tard :

```bash
make bootstrap m=vpn
```

Le bootstrap demande votre fournisseur et vos identifiants WireGuard, puis câble
tout :

- il enregistre les identifiants dans les variables `VPN_*` / `WIREGUARD_*` de
  `.env` ;
- il pose `COMPOSE_FILE=docker-compose.yml:docker-compose.vpn.yml` dans `.env`,
  pour que l'overlay VPN s'empile sur chaque commande `docker compose` ;
- il recrée qBittorrent en `network_mode: "service:gluetun"`, ses ports passant
  sur Gluetun.

Voir le [wiki Gluetun](https://github.com/qdm12/gluetun-wiki) pour les variables
exactes de votre fournisseur ; ajustez ensuite les `VPN_*` dans `.env` si besoin
(puis `make up` pour appliquer).

qBittorrent garde le nom interne `qbittorrent:8080` (Gluetun porte cet alias
réseau), donc Caddy et les apps *arr le joignent sans changement.

## Désactiver

Relancez le bootstrap en répondant **non** (réinitialise le flag `_vpn`), puis :

```bash
make bootstrap m=vpn
```

Gluetun est supprimé, `COMPOSE_FILE` est effacé et qBittorrent revient en mode
autonome.

## Vérifier le tunnel

```bash
docker exec gluetun wget -qO- https://ipinfo.io/ip   # doit afficher l'IP du VPN
docker exec qbittorrent curl -s https://ipinfo.io/ip # même IP VPN
```

Si Gluetun est arrêté, qBittorrent n'a **aucun** accès internet ; c'est le
kill-switch qui fonctionne comme prévu. Notez que si Gluetun redémarre,
qBittorrent (qui partage son réseau) perd la connectivité jusqu'à son propre
redémarrage.
