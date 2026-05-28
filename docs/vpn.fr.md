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

1. Renseignez les variables VPN dans `.env` (décommentez-les d'abord) :

   ```bash
   VPN_SERVICE_PROVIDER=mullvad        # votre fournisseur
   VPN_TYPE=wireguard
   WIREGUARD_PRIVATE_KEY=...
   WIREGUARD_ADDRESSES=10.x.x.x/32
   SERVER_COUNTRIES=Switzerland
   ```

   Voir le [wiki Gluetun](https://github.com/qdm12/gluetun-wiki) pour les
   variables exactes de votre fournisseur.

2. Dans `docker-compose.yml`, **décommentez le service `gluetun`** en bas.

3. Modifiez le service `qbittorrent` pour qu'il partage le réseau de Gluetun :

   ```yaml
   qbittorrent:
     image: lscr.io/linuxserver/qbittorrent:5.2.1
     container_name: qbittorrent
     network_mode: "service:gluetun"   # <- ajouter
     # supprimer le bloc `ports:` (déplacé vers gluetun)
     # supprimer le bloc `networks:` (hérité de gluetun)
     depends_on:
       - gluetun
     environment:
       PUID: ${PUID:-1000}
       PGID: ${PGID:-1000}
       TZ: ${TZ:-Etc/UTC}
       WEBUI_PORT: ${QBITTORRENT_WEBUI_PORT:-8080}
     volumes:
       - ${DOCKARR_CONFIG}/qbittorrent:/config
       - ${DOCKARR_DATA}:/data
   ```

   Les ports de qBittorrent sont déjà déclarés sur le service `gluetun`, donc
   son WebUI reste joignable sur le même port, mais désormais via le tunnel.

4. Appliquez :

   ```bash
   make up
   ```

## Vérifier le tunnel

```bash
docker exec gluetun wget -qO- https://ipinfo.io/ip   # doit afficher l'IP du VPN
docker exec qbittorrent curl -s https://ipinfo.io/ip # même IP VPN
```

Si Gluetun est arrêté, qBittorrent n'a **aucun** accès internet ; c'est le
kill-switch qui fonctionne comme prévu.
