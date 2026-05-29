# VPN (Gluetun)

You can route **qBittorrent** through a VPN so all torrent traffic is tunnelled.
Dockarr uses [Gluetun](https://github.com/qdm12/gluetun) for this.

!!! warning "Gluetun requires a VPN subscription"
    Gluetun connects to a VPN provider (WireGuard or OpenVPN). Without
    credentials it can't establish a tunnel, and its kill-switch blocks all of
    qBittorrent's traffic. Only enable this once you have a VPN subscription.

## Enable it

Answer **yes** to the VPN prompt at `make install`, or run it later:

```bash
make bootstrap m=vpn
```

The bootstrap asks for your provider and WireGuard credentials, then wires
everything up:

- it stores the credentials in the `VPN_*` / `WIREGUARD_*` variables of `.env`;
- it sets `COMPOSE_FILE=docker-compose.yml:docker-compose.vpn.yml` in `.env`, so
  the [VPN overlay](https://github.com/qdm12/gluetun-wiki) is layered on every
  `docker compose` command;
- it recreates qBittorrent with `network_mode: "service:gluetun"`, moving its
  ports onto Gluetun.

See the [Gluetun wiki](https://github.com/qdm12/gluetun-wiki) for your
provider's exact variables; adjust the `VPN_*` values in `.env` afterwards if
needed (then `make up` to apply).

qBittorrent keeps the internal name `qbittorrent:8080` (Gluetun carries that
network alias), so Caddy and the *arr apps reach it unchanged.

## Disable it

Re-run the bootstrap and answer **no** (clear the `_vpn` flag), then:

```bash
make bootstrap m=vpn
```

It removes Gluetun, clears `COMPOSE_FILE`, and brings qBittorrent back standalone.

## Verify the tunnel

```bash
docker exec gluetun wget -qO- https://ipinfo.io/ip   # should show the VPN IP
docker exec qbittorrent curl -s https://ipinfo.io/ip # same VPN IP
```

If Gluetun is down, qBittorrent has **no** internet access; that is the
kill-switch working as intended. Note that if Gluetun restarts, qBittorrent
(which shares its network) loses connectivity until it restarts too.
