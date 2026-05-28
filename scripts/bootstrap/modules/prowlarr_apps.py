from ..core.http import ApiClient
from ..core.registry import Module
from .arr_setup import _fill_fields
from .servarr import _api_key

PROWLARR_URL = "http://prowlarr:9696"
APPS = [
    {"impl": "Radarr", "arr": "radarr", "base_url": "http://radarr:7878"},
    {"impl": "Sonarr", "arr": "sonarr", "base_url": "http://sonarr:8989"},
]


class ProwlarrApps(Module):
    """Register Radarr & Sonarr as Prowlarr applications so indexers sync to
    them automatically (fullSync). Idempotent."""

    name = "prowlarr-apps"
    depends = ("prowlarr", "radarr", "sonarr")

    def _client(self, ctx):
        base = ctx.config.service_url("prowlarr")
        return ApiClient(base, headers={"X-Api-Key": _api_key("prowlarr")})

    def _existing(self, client):
        return {a.get("implementation") for a in client.get("/api/v1/applications").json()}

    def is_done(self, ctx):
        try:
            client = self._client(ctx)
            client.wait_until_up("/api/v1/system/status", timeout=10)
        except (RuntimeError, TimeoutError):
            return False
        return all(app["impl"] in self._existing(client) for app in APPS)

    def run(self, ctx):
        client = self._client(ctx)
        client.wait_until_up("/api/v1/system/status")
        existing = self._existing(client)
        schemas = {
            s["implementation"]: s
            for s in client.get("/api/v1/applications/schema").json()
        }

        for app in APPS:
            if app["impl"] in existing:
                ctx.log.info(f"  {app['impl']} application already present")
                continue
            schema = schemas[app["impl"]]
            _fill_fields(
                schema,
                {
                    "prowlarrUrl": PROWLARR_URL,
                    "baseUrl": app["base_url"],
                    "apiKey": _api_key(app["arr"]),
                },
            )
            schema.update(
                {"enable": True, "syncLevel": "fullSync", "name": app["impl"]}
            )
            resp = client.post("/api/v1/applications", json=schema)
            if resp.status_code not in (200, 201):
                raise RuntimeError(
                    f"add {app['impl']} application failed: "
                    f"HTTP {resp.status_code} {resp.text[:200]}"
                )
            ctx.log.info(f"  {app['impl']} application added (fullSync)")


MODULE = ProwlarrApps()
