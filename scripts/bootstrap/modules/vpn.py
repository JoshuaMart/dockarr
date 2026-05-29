import subprocess

from ..core import dotenv
from ..core.registry import Module

CONTAINER = "gluetun"
# When enabled, .env points Compose at the base file plus the VPN overlay so that
# every `docker compose` command (make up / update / logs) routes qBittorrent
# through gluetun. See docker-compose.vpn.yml.
COMPOSE_FILE_VPN = "docker-compose.yml:docker-compose.vpn.yml"

# Credentials captured by the first-run prompt that gluetun reads from .env.
VPN_ENV_KEYS = [
    "VPN_SERVICE_PROVIDER",
    "VPN_TYPE",
    "WIREGUARD_PRIVATE_KEY",
    "WIREGUARD_ADDRESSES",
    "SERVER_COUNTRIES",
]


def _gluetun_running():
    result = subprocess.run(
        ["docker", "inspect", "-f", "{{.State.Running}}", CONTAINER],
        capture_output=True,
        text=True,
    )
    return result.returncode == 0 and result.stdout.strip() == "true"


def _vpn_active():
    """Whether .env currently selects the VPN overlay."""
    return dotenv.get_var("COMPOSE_FILE") == COMPOSE_FILE_VPN


class Vpn(Module):
    name = "vpn"
    depends = ()

    def _enabled(self, ctx):
        cfg = ctx.secrets.vpn
        return bool(cfg and cfg.get("enabled"))

    def is_done(self, ctx):
        if self._enabled(ctx):
            # Overlay selected and gluetun actually up.
            return _vpn_active() and _gluetun_running()
        return not _vpn_active()

    def run(self, ctx):
        if not self._enabled(ctx):
            if _vpn_active():
                # qBittorrent shares gluetun's netns, so remove it first; then
                # drop the overlay so it comes back standalone from the base file.
                subprocess.run(
                    ["docker", "compose", "rm", "-sf", "qbittorrent", CONTAINER],
                    capture_output=True,
                )
                dotenv.unset_var("COMPOSE_FILE")
                ctx.log.info("  VPN disabled, COMPOSE_FILE cleared")
            subprocess.run(
                ["docker", "compose", "up", "-d", "qbittorrent"], capture_output=True
            )
            ctx.log.info("  qBittorrent running standalone")
            return

        # Mirror the credentials into .env (gluetun reads them via ${...}). Blank
        # values are left for the user to fill in .env.
        cfg = ctx.secrets.vpn
        for key in VPN_ENV_KEYS:
            value = cfg.get(key)
            if value:
                dotenv.set_var(key, value)
        if dotenv.set_var("COMPOSE_FILE", COMPOSE_FILE_VPN):
            ctx.log.info(f"  COMPOSE_FILE set to {COMPOSE_FILE_VPN}")
        # Recreate qBittorrent (and start gluetun via depends_on) so it routes
        # through the VPN.
        subprocess.run(
            ["docker", "compose", "up", "-d", "qbittorrent"], capture_output=True
        )
        ctx.log.info("  gluetun up, qBittorrent routed through the VPN")


MODULE = Vpn()
