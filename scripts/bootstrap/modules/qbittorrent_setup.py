import json

from ..core.registry import Module
from .qbittorrent import _client, _login

# TRaSH-style layout: everything under the single /data volume so Radarr/Sonarr
# can hardlink + atomic-move from torrents into the media library.
SAVE_PATH = "/data/torrents"
CATEGORIES = {
    "radarr": "/data/torrents/movies",
    "sonarr": "/data/torrents/tv",
}


class QbittorrentSetup(Module):
    name = "qbittorrent-setup"
    depends = ("qbittorrent",)

    def _authed_client(self, ctx):
        client = _client(ctx)
        client.wait_until_up("/", timeout=10)
        creds = ctx.secrets.get("qbittorrent")
        if not creds or not _login(client, creds["username"], creds["password"]):
            return None
        return client

    def is_done(self, ctx):
        try:
            client = self._authed_client(ctx)
        except TimeoutError:
            return False
        if client is None:
            return False
        prefs = client.get("/api/v2/app/preferences").json()
        if prefs.get("save_path") != SAVE_PATH:
            return False
        categories = client.get("/api/v2/torrents/categories").json()
        return all(name in categories for name in CATEGORIES)

    def run(self, ctx):
        client = self._authed_client(ctx)
        if client is None:
            raise RuntimeError("qbittorrent login failed — run its account module first")

        client.post(
            "/api/v2/app/setPreferences",
            data={"json": json.dumps({"save_path": SAVE_PATH})},
        )
        ctx.log.info(f"  default save path set to {SAVE_PATH}")

        existing = client.get("/api/v2/torrents/categories").json()
        for name, path in CATEGORIES.items():
            endpoint = "editCategory" if name in existing else "createCategory"
            resp = client.post(
                f"/api/v2/torrents/{endpoint}",
                data={"category": name, "savePath": path},
            )
            if resp.status_code not in (200, 409):
                raise RuntimeError(
                    f"category '{name}' {endpoint} failed: HTTP {resp.status_code}"
                )
            ctx.log.info(f"  category '{name}' -> {path}")


MODULE = QbittorrentSetup()
