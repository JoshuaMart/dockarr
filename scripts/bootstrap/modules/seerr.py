from ..core.http import ApiClient
from ..core.registry import Module
from .servarr import _api_key

# Internal docker hostnames (Seerr reaches these on the dockarr network).
JELLYFIN_HOST = "jellyfin"
JELLYFIN_PORT = 8096

DEFAULT_PROFILE = "1080p Quality FR"
RADARR = {"host": "radarr", "port": 7878, "root": "/data/media/movies"}
SONARR = {"host": "sonarr", "port": 8989, "root": "/data/media/tv"}


def _pick(items, key, value, fallback=None):
    for item in items:
        if item.get(key) == value:
            return item
    return fallback


class Seerr(Module):
    """Initialise Seerr headlessly: authenticate against Jellyfin (which creates
    the Seerr admin), then register Radarr & Sonarr as default servers with the
    chosen quality profile and root folder. Idempotent via settings.initialized."""

    name = "seerr"
    depends = ("jellyfin", "radarr", "sonarr")

    def _client(self, ctx):
        return ApiClient(ctx.config.service_url("seerr"))

    def is_done(self, ctx):
        try:
            client = self._client(ctx)
            client.wait_until_up("/api/v1/status", timeout=10)
            resp = client.get("/api/v1/settings/public")
        except (RuntimeError, TimeoutError):
            return False
        return resp.ok and resp.json().get("initialized") is True

    def run(self, ctx):
        client = self._client(ctx)
        client.wait_until_up("/api/v1/status")

        jf = ctx.secrets.get("jellyfin")
        if not jf:
            raise RuntimeError("jellyfin credentials missing — run its module first")

        # Authenticating against Jellyfin creates the Seerr admin and sets the
        # session cookie reused by the subsequent settings calls.
        resp = client.post(
            "/api/v1/auth/jellyfin",
            json={
                "username": jf["username"],
                "password": jf["password"],
                "hostname": JELLYFIN_HOST,
                "port": JELLYFIN_PORT,
                "useSsl": False,
                "urlBase": "",
                "serverType": 2,
            },
        )
        if resp.status_code not in (200, 201):
            raise RuntimeError(
                f"Seerr Jellyfin auth failed: HTTP {resp.status_code} {resp.text[:200]}"
            )
        ctx.log.info(f"  admin linked to Jellyfin account '{jf['username']}'")

        self._add_dvr(ctx, client, "radarr", "Radarr", RADARR, extra={"minimumAvailability": "released"})
        self._add_dvr(
            ctx,
            client,
            "sonarr",
            "Sonarr",
            SONARR,
            extra={
                "seriesType": "standard",
                "animeSeriesType": "standard",
                "enableSeasonFolders": True,
                "monitorNewItems": "all",
            },
        )

        init = client.post("/api/v1/settings/initialize")
        if init.status_code not in (200, 201):
            raise RuntimeError(f"Seerr initialize failed: HTTP {init.status_code}")
        ctx.log.info("  Seerr initialized")

    def _add_dvr(self, ctx, client, kind, name, target, extra):
        api_key = _api_key(target["host"])
        test_body = {
            "hostname": target["host"],
            "port": target["port"],
            "apiKey": api_key,
            "useSsl": False,
            "baseUrl": "",
        }
        test = client.post(f"/api/v1/settings/{kind}/test", json=test_body)
        if test.status_code != 200:
            raise RuntimeError(
                f"{name} test failed: HTTP {test.status_code} {test.text[:200]}"
            )
        data = test.json()

        profile = _pick(data.get("profiles", []), "name", DEFAULT_PROFILE)
        if profile is None:
            raise RuntimeError(f"profile '{DEFAULT_PROFILE}' not found on {name}")
        root = _pick(data.get("rootFolders", []), "path", target["root"])
        root_path = root["path"] if root else target["root"]

        body = {
            "name": name,
            "hostname": target["host"],
            "port": target["port"],
            "apiKey": api_key,
            "useSsl": False,
            "baseUrl": "",
            "activeProfileId": profile["id"],
            "activeProfileName": profile["name"],
            "activeDirectory": root_path,
            "is4k": False,
            "isDefault": True,
            "tags": [],
            "syncEnabled": True,
            "preventSearch": False,
            "tagRequests": False,
            "externalUrl": "",
        }
        body.update(extra)

        resp = client.post(f"/api/v1/settings/{kind}", json=body)
        if resp.status_code not in (200, 201):
            raise RuntimeError(
                f"add {name} failed: HTTP {resp.status_code} {resp.text[:200]}"
            )
        ctx.log.info(f"  {name} added (profile '{profile['name']}', root {root_path})")


MODULE = Seerr()
