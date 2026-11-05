from ..core.http import ApiClient
from ..core.registry import Module
from .servarr import _api_key

ARRS = ("radarr", "sonarr")
PROFILES = "/api/v3/qualityprofile"


class ArrNoUpgrades(Module):
    """Turn off upgrades on every Radarr/Sonarr quality profile. Profilarr's
    profiles allow them (with a huge custom-format cutoff), so an imported
    release keeps being replaced by a bigger one — a 10 GB WEB-DL became a
    25 GB Bluray TrueHD — and the superseded torrent lingers in qBittorrent.
    Runs after profilarr-fr, whose quality-profile sync would re-enable them."""

    name = "arr-no-upgrades"
    depends = ("radarr", "sonarr", "profilarr-fr")

    def _client(self, ctx, arr):
        return ApiClient(
            ctx.config.service_url(arr), headers={"X-Api-Key": _api_key(arr)}
        )

    def _upgradable(self, client):
        resp = client.get(PROFILES)
        if not resp.ok:
            raise RuntimeError(
                f"list quality profiles failed: HTTP {resp.status_code} {resp.text[:200]}"
            )
        return [p for p in resp.json() if p.get("upgradeAllowed")]

    def is_done(self, ctx):
        try:
            for arr in ARRS:
                client = self._client(ctx, arr)
                client.wait_until_up("/api/v3/system/status", timeout=10)
                if self._upgradable(client):
                    return False
        except (RuntimeError, TimeoutError):
            return False
        return True

    def run(self, ctx):
        for arr in ARRS:
            client = self._client(ctx, arr)
            client.wait_until_up("/api/v3/system/status")
            profiles = self._upgradable(client)
            for profile in profiles:
                profile["upgradeAllowed"] = False
                resp = client.put(f"{PROFILES}/{profile['id']}", json=profile)
                if resp.status_code not in (200, 202):
                    raise RuntimeError(
                        f"{arr} profile '{profile['name']}' update failed: "
                        f"HTTP {resp.status_code} {resp.text[:200]}"
                    )
                ctx.log.info(f"  {arr}: upgrades disabled on '{profile['name']}'")
            if not profiles:
                ctx.log.info(f"  {arr}: upgrades already disabled")


MODULE = ArrNoUpgrades()
