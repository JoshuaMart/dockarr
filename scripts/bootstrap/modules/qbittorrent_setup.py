import json

from ..core.registry import Module
from .qbittorrent import _client, _login

# TRaSH-style layout: everything under the single /data volume so Radarr/Sonarr
# can hardlink + atomic-move from torrents into the media library.
SAVE_PATH = "/data/torrents"
CATEGORIES = {
    "radarr": "/data/torrents/movies",
    "sonarr": "/data/torrents/tv",
    # Book categories. Radarr/Sonarr don't manage these, so ON_COMPLETE_PROGRAM
    # hardlinks finished downloads into the matching Kavita library; the torrent
    # keeps seeding from here. Names match the case in qbittorrent/on-complete.sh.
    "bd": "/data/torrents/books/bd",
    "comics": "/data/torrents/books/comics",
    "manga": "/data/torrents/books/manga",
    "livres": "/data/torrents/books/livres",
}
# Cap concurrent downloads; keep uploads/active torrents unlimited so seeding
# is never throttled (good for private-tracker ratio). Edit to taste.
MAX_ACTIVE_DOWNLOADS = 3

# Run on torrent completion. The script (mounted at /scripts by compose) ignores
# every category except the book ones, so movies/TV are untouched.
ON_COMPLETE_PROGRAM = '/bin/sh /scripts/on-complete.sh "%F" "%L"'

# Automatic TMM is what actually routes downloads into the category subfolders;
# the relocate flags keep existing torrents in sync when paths change.
PREFERENCES = {
    "save_path": SAVE_PATH,
    "auto_tmm_enabled": True,
    "torrent_changed_tmm_enabled": True,
    "save_path_changed_tmm_enabled": True,
    "category_changed_tmm_enabled": True,
    "queueing_enabled": True,
    "max_active_downloads": MAX_ACTIVE_DOWNLOADS,
    "max_active_uploads": -1,
    "max_active_torrents": -1,
    "autorun_enabled": True,
    "autorun_program": ON_COMPLETE_PROGRAM,
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
        if any(prefs.get(key) != value for key, value in PREFERENCES.items()):
            return False
        categories = client.get("/api/v2/torrents/categories").json()
        return all(name in categories for name in CATEGORIES)

    def run(self, ctx):
        client = self._authed_client(ctx)
        if client is None:
            raise RuntimeError("qbittorrent login failed — run its account module first")

        client.post(
            "/api/v2/app/setPreferences",
            data={"json": json.dumps(PREFERENCES)},
        )
        ctx.log.info(f"  save path {SAVE_PATH} + Automatic TMM enabled")

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
