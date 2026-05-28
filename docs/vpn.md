# VPN (Gluetun)

You can route **qBittorrent** through a VPN so all torrent traffic is tunnelled.
Dockarr uses [Gluetun](https://github.com/qdm12/gluetun) for this.

!!! warning "Gluetun needs a real VPN provider"
    Gluetun **is a VPN client** — there is no "transparent / no-VPN" mode. It
    must connect to a provider (WireGuard or OpenVPN). Without credentials it
    will not establish a tunnel, and its kill-switch will block qBittorrent's
    traffic. Only enable this once you have a VPN subscription.

## Enable it

1. Fill the VPN variables in `.env` (uncomment them first):

   ```bash
   VPN_SERVICE_PROVIDER=mullvad        # your provider
   VPN_TYPE=wireguard
   WIREGUARD_PRIVATE_KEY=...
   WIREGUARD_ADDRESSES=10.x.x.x/32
   SERVER_COUNTRIES=Switzerland
   ```

   See the [Gluetun wiki](https://github.com/qdm12/gluetun-wiki) for your
   provider's exact variables.

2. In `docker-compose.yml`, **uncomment the `gluetun` service** at the bottom.

3. Change the `qbittorrent` service so it shares Gluetun's network:

   ```yaml
   qbittorrent:
     image: lscr.io/linuxserver/qbittorrent:5.2.1
     container_name: qbittorrent
     network_mode: "service:gluetun"   # <- add this
     # remove the `ports:` block (moved to gluetun)
     # remove the `networks:` block (inherited from gluetun)
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

   qBittorrent's ports are already declared on the `gluetun` service, so its
   WebUI stays reachable on the same port — but now through the tunnel.

4. Apply:

   ```bash
   make up
   ```

## Verify the tunnel

```bash
docker exec gluetun wget -qO- https://ipinfo.io/ip   # should show the VPN IP
docker exec qbittorrent curl -s https://ipinfo.io/ip # same VPN IP
```

If Gluetun is down, qBittorrent has **no** internet access — that is the
kill-switch working as intended.
