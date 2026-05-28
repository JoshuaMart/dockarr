from ..core.http import ApiClient
from ..core.registry import Module
from .servarr import _api_key

# Internal docker hostnames (Seerr reaches these on the dockarr network).
JELLYFIN_HOST = "jellyfin"
JELLYFIN_PORT = 8096

# This profile is provided by the Profilarr French database and only exists in
# Radarr/Sonarr AFTER you import + sync it in Profilarr. Until then the Seerr
# module skips the DVR (with a warning) and self-heals on the next bootstrap.
DEFAULT_PROFILE = "1080p Quality FR"
RADARR = {"host": "radarr", "port": 7878, "root": "/data/media/movies"}
SONARR = {"host": "sonarr", "port": 8989, "root": "/data/media/tv"}


def _pick(items, key, value):
    for item in items:
        if item.get(key) == value:
            return item
    return None


class Seerr(Module):
    """Initialise Seerr headlessly: authenticate against Jellyfin (creating the
    Seerr admin), then register Radarr & Sonarr as default servers using the
    chosen quality profile. If that profile isn't in Radarr/Sonarr yet (Profilarr
    sync not done), the DVR is skipped with a warning and added on a later run."""

    name = "seerr"
    depends = ("jellyfin", "radarr", "sonarr")

    def _client(self, ctx):
        return ApiClient(ctx.config.service_url("seerr"))

    def _auth(self, ctx, client):
        jf = ctx.secrets.get("jellyfin")
        if not jf:
            return False
        # First run bootstraps the admin from the Jellyfin server (needs the
        # full server details); afterwards it's a plain login (sending the
        # server details again returns 500).
        if self._initialized(client):
            body = {"username": jf["username"], "password": jf["password"]}
        else:
            body = {
                "username": jf["username"],
                "password": jf["password"],
                "hostname": JELLYFIN_HOST,
                "port": JELLYFIN_PORT,
                "useSsl": False,
                "urlBase": "",
                "serverType": 2,
            }
        resp = client.post("/api/v1/auth/jellyfin", json=body)
        return resp.status_code in (200, 201)

    def _initialized(self, client):
        resp = client.get("/api/v1/settings/public")
        return resp.ok and resp.json().get("initialized") is True

    def _server(self, client, kind, hostname):
        resp = client.get(f"/api/v1/settings/{kind}")
        if not resp.ok:
            return None
        for server in resp.json():
            if server.get("hostname") == hostname and not server.get("is4k"):
                return server
        return None

    def is_done(self, ctx):
        try:
            client = self._client(ctx)
            client.wait_until_up("/api/v1/status", timeout=10)
        except (RuntimeError, TimeoutError):
            return False
        if not self._initialized(client):
            return False
        if not self._auth(ctx, client):
            return False
        radarr = self._server(client, "radarr", RADARR["host"])
        sonarr = self._server(client, "sonarr", SONARR["host"])
        return bool(
            radarr and radarr.get("activeProfileName") == DEFAULT_PROFILE
            and sonarr and sonarr.get("activeProfileName") == DEFAULT_PROFILE
        )

    def run(self, ctx):
        client = self._client(ctx)
        client.wait_until_up("/api/v1/status")

        jf = ctx.secrets.get("jellyfin")
        if not jf or not self._auth(ctx, client):
            raise RuntimeError("Seerr Jellyfin auth failed — is Jellyfin set up?")
        ctx.log.info(f"  linked to Jellyfin account '{jf['username']}'")

        self._ensure_dvr(ctx, client, "radarr", "Radarr", RADARR,
                         {"minimumAvailability": "released"})
        self._ensure_dvr(ctx, client, "sonarr", "Sonarr", SONARR,
                         {"seriesType": "standard", "animeSeriesType": "standard",
                          "enableSeasonFolders": True, "monitorNewItems": "all"})

        if not self._initialized(client):
            init = client.post("/api/v1/settings/initialize")
            if init.status_code not in (200, 201):
                raise RuntimeError(f"Seerr initialize failed: HTTP {init.status_code}")
            ctx.log.info("  Seerr initialized")

    def _ensure_dvr(self, ctx, client, kind, name, target, extra):
        api_key = _api_key(target["host"])
        test = client.post(
            f"/api/v1/settings/{kind}/test",
            json={"hostname": target["host"], "port": target["port"],
                  "apiKey": api_key, "useSsl": False, "baseUrl": ""},
        )
        if test.status_code != 200:
            raise RuntimeError(f"{name} test failed: HTTP {test.status_code} {test.text[:200]}")
        data = test.json()

        profile = _pick(data.get("profiles", []), "name", DEFAULT_PROFILE)
        existing = self._server(client, kind, target["host"])
        if profile is None:
            ctx.log.info(
                f"  WARNING: profile '{DEFAULT_PROFILE}' not in {name} yet — "
                f"import+sync it in Profilarr, then re-run 'make bootstrap m=seerr' "
                f"({name} left unconfigured)"
            )
            return

        if existing and existing.get("activeProfileName") == profile["name"]:
            ctx.log.info(f"  {name} already set ('{profile['name']}')")
            return

        root = _pick(data.get("rootFolders", []), "path", target["root"])
        root_path = root["path"] if root else target["root"]
        body = {
            "name": name, "hostname": target["host"], "port": target["port"],
            "apiKey": api_key, "useSsl": False, "baseUrl": "",
            "activeProfileId": profile["id"], "activeProfileName": profile["name"],
            "activeDirectory": root_path, "is4k": False, "isDefault": True,
            "tags": [], "syncEnabled": True, "preventSearch": False,
            "tagRequests": False, "externalUrl": "",
        }
        body.update(extra)

        if existing:
            resp = client.put(f"/api/v1/settings/{kind}/{existing['id']}", json=body)
            action = "updated"
        else:
            resp = client.post(f"/api/v1/settings/{kind}", json=body)
            action = "added"
        if resp.status_code not in (200, 201):
            raise RuntimeError(f"{action} {name} failed: HTTP {resp.status_code} {resp.text[:200]}")
        ctx.log.info(f"  {name} {action} (profile '{profile['name']}', root {root_path})")


MODULE = Seerr()
