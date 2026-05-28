from ..core.registry import Module
from .profilarr import _client, _login
from .servarr import _api_key

TARGETS = [
    {"name": "Radarr", "type": "radarr", "url": "http://radarr:7878", "arr": "radarr"},
    {"name": "Sonarr", "type": "sonarr", "url": "http://sonarr:8989", "arr": "sonarr"},
]


class ProfilarrTargets(Module):
    """Register Radarr & Sonarr as Arr connections in Profilarr so it can push
    profiles/custom formats/naming to them. The actual sync content stays
    curated in the Profilarr UI; this only wires the targets. Idempotent."""

    name = "profilarr-targets"
    depends = ("profilarr", "radarr", "sonarr")

    def _authed_client(self, ctx):
        creds = ctx.secrets.get("profilarr")
        if not creds:
            return None
        client = _client(ctx)
        client.wait_until_up("/api/v1/health", timeout=10)
        # Form actions (/arr/new) require the session cookie, not X-Api-Key.
        if not _login(client, creds["username"], creds["password"]):
            return None
        return client

    def _existing_urls(self, client):
        resp = client.get("/api/v1/arr")
        if not resp.ok:
            return set()
        return {item.get("url", "").rstrip("/") for item in resp.json()}

    def is_done(self, ctx):
        try:
            client = self._authed_client(ctx)
        except TimeoutError:
            return False
        if client is None:
            return False
        urls = self._existing_urls(client)
        return all(t["url"] in urls for t in TARGETS)

    def run(self, ctx):
        client = self._authed_client(ctx)
        if client is None:
            raise RuntimeError("profilarr login failed — run its account module first")

        existing = self._existing_urls(client)
        for target in TARGETS:
            if target["url"] in existing:
                ctx.log.info(f"  {target['name']} already a target")
                continue
            resp = client.post(
                "/arr/new",
                data={
                    "name": target["name"],
                    "type": target["type"],
                    "url": target["url"],
                    "api_key": _api_key(target["arr"]),
                },
            )
            if target["url"] not in self._existing_urls(client):
                raise RuntimeError(
                    f"registering {target['name']} target failed: "
                    f"HTTP {resp.status_code} {resp.text[:200]}"
                )
            ctx.log.info(f"  {target['name']} registered as sync target")


MODULE = ProfilarrTargets()
