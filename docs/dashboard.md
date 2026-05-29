# Dashboard

A lightweight landing page that lists every service with a live **up / down**
status and a link to its interface. It is served at
`dashboard.${DOCKARR_DOMAIN}` (and on host port `8081` for direct access).

![Dashboard](assets/banner.png)

## How it works

- **Stack**: vanilla PHP (`php:8.5-apache`) + [Pico.css](https://picocss.com)
  (vendored, no CDN) + a little vanilla JavaScript. No build step.
- **Status = reachability only**: a small server-side probe (`api/status.php`)
  hits each service's internal health endpoint, the same ones the bootstrap
  uses (e.g. `/api/v3/system/status` for Radarr/Sonarr, `/api/health` for
  Kavita). Any HTTP response below `500` counts as **online** (a `401` still
  means the server answered); a connection error or `5xx` means **offline**.
- **No secrets, no API keys**: the dashboard never mounts `.env` or `secrets/`.
  It only receives the non-sensitive `COMPOSE_PROFILES` and `COMPOSE_FILE`
  values as environment variables to know which optional services are on
  (Kavita, VPN), plus `DOCKARR_LANG` to render in the right language.
- **Auto-refresh** every ~20 seconds, with a manual *Refresh* button.

## Status legend

| Indicator | Meaning |
| --- | --- |
| green dot + latency | Online (reachable), with response time in ms |
| red dot + "offline" | Offline (connection refused, timeout or 5xx) |
| hollow dot + "disabled" | Optional service turned off at `make install` |

## Customising

The list of services, their colours, descriptions and health endpoints live in
`dashboard/config.php`. UI strings (FR/EN) are in `dashboard/lib.php`. Edit those
to add a tile or change wording.

!!! note "VPN badge"
    The VPN badge reflects whether the VPN overlay is enabled (`COMPOSE_FILE`),
    not a live tunnel check. Exposing Gluetun's control API would allow showing
    the real public IP later.
