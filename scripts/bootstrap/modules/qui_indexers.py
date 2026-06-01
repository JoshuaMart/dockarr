from ..core.registry import Module
from .qui import _client, _login
from .servarr import _api_key

# qui reaches Prowlarr on the dockarr network; discover reads Prowlarr's
# indexer list and each entry is registered as a Prowlarr-backed Torznab feed.
PROWLARR_URL = "http://prowlarr:9696"


class QuiIndexers(Module):
    """Import every torrent indexer Prowlarr exposes into qui's Torznab search.

    Uses qui's discover endpoint (which reads Prowlarr's indexer list) and
    registers each as a Prowlarr-backed Torznab indexer, matching what the
    "Discover" button in the UI does. Idempotent: indexers already present
    (matched by their Prowlarr indexer id) are skipped. Adds nothing until
    Prowlarr itself has indexers configured."""

    name = "qui-indexers"
    depends = ("qui", "prowlarr")

    def _authed_client(self, ctx):
        creds = ctx.secrets.get("qui")
        if not creds:
            return None
        client = _client(ctx)
        client.wait_until_up("/", timeout=10)
        if not _login(client, creds["username"], creds["password"]):
            return None
        return client

    def _discover(self, client, api_key):
        resp = client.post(
            "/api/torznab/indexers/discover",
            json={"base_url": PROWLARR_URL, "api_key": api_key},
        )
        if not resp.ok:
            raise RuntimeError(
                f"qui discover failed: HTTP {resp.status_code} {resp.text[:200]}"
            )
        return resp.json().get("indexers", [])

    def _existing_ids(self, client):
        resp = client.get("/api/torznab/indexers")
        if not resp.ok:
            return set()
        return {
            i.get("indexer_id")
            for i in resp.json()
            if i.get("backend") == "prowlarr"
        }

    def is_done(self, ctx):
        try:
            client = self._authed_client(ctx)
        except TimeoutError:
            return False
        if client is None:
            return False
        try:
            discovered = self._discover(client, _api_key("prowlarr"))
        except RuntimeError:
            return False
        existing = self._existing_ids(client)
        return all(d.get("id") in existing for d in discovered)

    def run(self, ctx):
        client = self._authed_client(ctx)
        if client is None:
            raise RuntimeError("qui login failed — run its account module first")

        api_key = _api_key("prowlarr")
        discovered = self._discover(client, api_key)
        if not discovered:
            ctx.log.info("  no indexers in Prowlarr yet — nothing to import")
            return

        existing = self._existing_ids(client)
        for idx in discovered:
            name = idx.get("name")
            indexer_id = idx.get("id")
            if indexer_id in existing:
                ctx.log.info(f"  {name} already imported")
                continue
            resp = client.post(
                "/api/torznab/indexers",
                json={
                    "name": name,
                    "base_url": PROWLARR_URL,
                    "api_key": api_key,
                    "backend": "prowlarr",
                    "indexer_id": indexer_id,
                    "categories": idx.get("categories") or [],
                    "enabled": True,
                },
            )
            if resp.status_code not in (200, 201):
                raise RuntimeError(
                    f"importing {name} into qui failed: "
                    f"HTTP {resp.status_code} {resp.text[:200]}"
                )
            ctx.log.info(f"  {name} imported")


MODULE = QuiIndexers()
