from pathlib import Path

import yaml

from ..core.http import ApiClient
from ..core.registry import Module
from .servarr import _api_key

CONFIG_FILE = Path("indexers.yml")


class ProwlarrIndexers(Module):
    """Config-driven: add the indexers listed in indexers.yml to Prowlarr.
    An indexer that fails its connectivity test is logged as a warning and
    skipped — it never aborts the rest of the bootstrap."""

    name = "prowlarr-indexers"
    depends = ("prowlarr", "prowlarr-apps")

    def _load(self):
        if not CONFIG_FILE.exists():
            return []
        data = yaml.safe_load(CONFIG_FILE.read_text()) or {}
        return data.get("indexers") or []

    def _client(self, ctx):
        base = ctx.config.service_url("prowlarr")
        return ApiClient(base, headers={"X-Api-Key": _api_key("prowlarr")})

    def _existing_names(self, client):
        return {i.get("name") for i in client.get("/api/v1/indexer").json()}

    def is_done(self, ctx):
        wanted = self._load()
        if not wanted:
            return True
        try:
            client = self._client(ctx)
            client.wait_until_up("/api/v1/system/status", timeout=10)
        except (RuntimeError, TimeoutError):
            return False
        names = self._existing_names(client)
        return all(idx.get("name") in names for idx in wanted)

    def run(self, ctx):
        wanted = self._load()
        if not wanted:
            ctx.log.info(f"  no {CONFIG_FILE} (or empty) — nothing to add")
            return

        client = self._client(ctx)
        client.wait_until_up("/api/v1/system/status")
        schemas = {s["name"]: s for s in client.get("/api/v1/indexer/schema").json()}
        existing = self._existing_names(client)

        for idx in wanted:
            name = idx.get("name")
            if not name:
                ctx.log.info("  WARNING: indexer entry without 'name' — skipped")
                continue
            if name in existing:
                ctx.log.info(f"  '{name}' already present")
                continue
            schema = schemas.get(name)
            if schema is None:
                ctx.log.info(f"  WARNING: no Prowlarr definition named '{name}' — skipped")
                continue

            values = idx.get("fields") or {}
            for field in schema["fields"]:
                if field["name"] in values:
                    field["value"] = values[field["name"]]
            schema["enable"] = idx.get("enable", True)
            schema["appProfileId"] = idx.get("appProfileId", 1)
            if "priority" in idx:
                schema["priority"] = idx["priority"]

            params = {"forceSave": "true"} if idx.get("force") else None
            resp = client.post("/api/v1/indexer", json=schema, params=params)
            if resp.status_code in (200, 201):
                ctx.log.info(f"  '{name}' added")
            else:
                ctx.log.info(
                    f"  WARNING: '{name}' not added (HTTP {resp.status_code}): "
                    f"{resp.text[:160]}"
                )


MODULE = ProwlarrIndexers()
