from ..core.registry import Module
from .qui import _client, _login
from .servarr import _api_key

TARGETS = [
    {"type": "radarr", "name": "Radarr", "base_url": "http://radarr:7878", "arr": "radarr"},
    {"type": "sonarr", "name": "Sonarr", "base_url": "http://sonarr:8989", "arr": "sonarr"},
]


class QuiArr(Module):
    """Register Radarr & Sonarr in qui's ARR Integrations so it can use their
    external IDs for enhanced cross-seed searches. Idempotent."""

    name = "qui-arr"
    depends = ("qui", "radarr", "sonarr")

    def _authed_client(self, ctx):
        creds = ctx.secrets.get("qui")
        if not creds:
            return None
        client = _client(ctx)
        client.wait_until_up("/", timeout=10)
        if not _login(client, creds["username"], creds["password"]):
            return None
        return client

    def _existing_urls(self, client):
        resp = client.get("/api/arr/instances")
        if not resp.ok:
            return set()
        return {item.get("base_url", "").rstrip("/") for item in resp.json()}

    def is_done(self, ctx):
        try:
            client = self._authed_client(ctx)
        except TimeoutError:
            return False
        if client is None:
            return False
        urls = self._existing_urls(client)
        return all(t["base_url"] in urls for t in TARGETS)

    def run(self, ctx):
        client = self._authed_client(ctx)
        if client is None:
            raise RuntimeError("qui login failed — run its account module first")

        existing = self._existing_urls(client)
        for target in TARGETS:
            if target["base_url"] in existing:
                ctx.log.info(f"  {target['name']} already integrated")
                continue
            resp = client.post(
                "/api/arr/instances",
                json={
                    "type": target["type"],
                    "name": target["name"],
                    "base_url": target["base_url"],
                    "api_key": _api_key(target["arr"]),
                    "enabled": True,
                    "priority": 0,
                    "timeout_seconds": 15,
                },
            )
            if resp.status_code not in (200, 201):
                raise RuntimeError(
                    f"adding {target['name']} to qui failed: "
                    f"HTTP {resp.status_code} {resp.text[:200]}"
                )
            ctx.log.info(f"  {target['name']} integrated for cross-seed")


MODULE = QuiArr()
