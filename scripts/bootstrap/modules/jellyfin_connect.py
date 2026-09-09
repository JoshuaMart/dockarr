from ..core.http import ApiClient
from ..core.registry import Module
from .jellyfin import _authenticate, _client as _jellyfin_client
from .servarr import _api_key

API_KEY_APP = "Dockarr"
NOTIFICATION_NAME = "Jellyfin"
JELLYFIN_HOST = "jellyfin"
JELLYFIN_PORT = 8096

# Jellyfin ships TheMovieDb as its only metadata provider and reads external
# ids written as "[tmdbid-…]". Profilarr's curated media-management pushes the
# Plex convention ("{tmdb-…}" / "{tvdb-…}"), which Jellyfin cannot parse: it
# falls back to a fuzzy title search and matches the wrong entry (a French
# "The Target" became "High Value Target: The Hunt for Saddam"). Overriding the
# *folder* format is enough — Jellyfin identifies a library item from its
# folder, not from the movie/episode file name.
FOLDER_FORMATS = {
    "radarr": ("movieFolderFormat",
               "{Movie CleanTitle} ({Release Year}) [tmdbid-{TmdbId}]"),
    "sonarr": ("seriesFolderFormat", "{Series TitleYear} [tmdbid-{TmdbId}]"),
}
FOLDER_ID_MARKER = "[tmdbid-"

# Events that make Jellyfin rescan. Without them it only picks new files up on
# its periodic scan, so a fresh import surfaces as a series with zero episodes
# ("Impossible de trouver une source multimédia valide à lire").
NOTIFY_EVENTS = {
    "radarr": ("onDownload", "onUpgrade", "onRename", "onMovieDelete",
               "onMovieFileDelete", "onMovieFileDeleteForUpgrade"),
    "sonarr": ("onImportComplete", "onUpgrade", "onRename", "onSeriesDelete",
               "onEpisodeFileDelete", "onEpisodeFileDeleteForUpgrade"),
}

# Per-arr bits of the otherwise identical library layout.
ARRS = {
    "radarr": {"items": "/api/v3/movie", "editor": "/api/v3/movie/editor",
               "ids": "movieIds", "root": "/data/media/movies"},
    "sonarr": {"items": "/api/v3/series", "editor": "/api/v3/series/editor",
               "ids": "seriesIds", "root": "/data/media/tv"},
}


def _fill_fields(schema, values):
    for field in schema["fields"]:
        if field["name"] in values:
            field["value"] = values[field["name"]]
    return schema


def _field(notification, name):
    for field in notification.get("fields", []):
        if field["name"] == name:
            return field.get("value")
    return None


def _api_key_ok(notification, api_key):
    # Radarr/Sonarr return secret fields masked ("********") on read, so a
    # stored key can only be compared when the arr hands back the real value.
    value = _field(notification, "apiKey")
    if not value:
        return False
    if set(str(value)) == {"*"}:
        return True
    return value == api_key


class JellyfinConnect(Module):
    """Wire Radarr & Sonarr to Jellyfin: a dedicated Jellyfin API key, a
    library-refresh connection on each arr, and a folder naming format Jellyfin
    can actually identify. Runs after profilarr-fr, whose media-management sync
    would otherwise overwrite the naming config."""

    name = "jellyfin-connect"
    depends = ("jellyfin", "radarr", "sonarr", "profilarr-fr")

    # --- Jellyfin API key ---------------------------------------------------

    def _token(self, ctx):
        creds = ctx.secrets.get("jellyfin")
        if not creds:
            return None
        return _authenticate(ctx, creds["username"], creds["password"])

    def _ensure_api_key(self, ctx, token):
        client = _jellyfin_client(ctx, token)
        resp = client.get("/Auth/Keys")
        if not resp.ok:
            raise RuntimeError(f"list API keys failed: HTTP {resp.status_code} {resp.text[:200]}")
        for key in resp.json().get("Items", []):
            if key.get("AppName") == API_KEY_APP:
                return key["AccessToken"]

        created = client.post(f"/Auth/Keys?app={API_KEY_APP}")
        if created.status_code not in (200, 204):
            raise RuntimeError(
                f"create API key failed: HTTP {created.status_code} {created.text[:200]}"
            )
        for key in client.get("/Auth/Keys").json().get("Items", []):
            if key.get("AppName") == API_KEY_APP:
                ctx.log.info(f"  Jellyfin API key '{API_KEY_APP}' created")
                return key["AccessToken"]
        raise RuntimeError(f"API key '{API_KEY_APP}' missing after creation")

    def _stored_api_key(self, ctx):
        return (ctx.secrets.get("jellyfin") or {}).get("api_key")

    def _store_api_key(self, ctx, api_key):
        creds = dict(ctx.secrets.get("jellyfin"))
        if creds.get("api_key") == api_key:
            return
        creds["api_key"] = api_key
        ctx.secrets.set("jellyfin", **creds)
        ctx.log.info("  API key stored in secrets/credentials.json")

    # --- arr side -----------------------------------------------------------

    def _client(self, ctx, arr):
        return ApiClient(
            ctx.config.service_url(arr), headers={"X-Api-Key": _api_key(arr)}
        )

    def _notification(self, client):
        resp = client.get("/api/v3/notification")
        if not resp.ok:
            return None
        for item in resp.json():
            if item.get("implementation") == "MediaBrowser":
                return item
        return None

    def _notification_ok(self, notification, arr, api_key):
        if notification is None:
            return False
        if _field(notification, "host") != JELLYFIN_HOST:
            return False
        if not _api_key_ok(notification, api_key):
            return False
        if not _field(notification, "updateLibrary"):
            return False
        return all(notification.get(event) for event in NOTIFY_EVENTS[arr])

    def _ensure_notification(self, ctx, client, arr, api_key):
        existing = self._notification(client)
        if self._notification_ok(existing, arr, api_key):
            ctx.log.info(f"  {arr}: Jellyfin connection already set")
            return

        schema = next(
            s
            for s in client.get("/api/v3/notification/schema").json()
            if s.get("implementation") == "MediaBrowser"
        )
        _fill_fields(schema, {
            "host": JELLYFIN_HOST, "port": JELLYFIN_PORT, "useSsl": False,
            "apiKey": api_key, "updateLibrary": True, "notify": False,
        })
        schema.update({event: True for event in NOTIFY_EVENTS[arr]})
        schema.update({"name": NOTIFICATION_NAME, "tags": []})
        schema.pop("id", None)

        if existing:
            schema["id"] = existing["id"]
            resp = client.put(f"/api/v3/notification/{existing['id']}", json=schema)
            action = "updated"
        else:
            resp = client.post("/api/v3/notification?forceSave=true", json=schema)
            action = "added"
        if resp.status_code not in (200, 201, 202):
            raise RuntimeError(
                f"{action} {arr} Jellyfin connection failed: "
                f"HTTP {resp.status_code} {resp.text[:200]}"
            )
        self._test_notification(client, arr)
        ctx.log.info(f"  {arr}: Jellyfin connection {action} (library refresh on import)")

    def _test_notification(self, client, arr):
        # Test the *saved* record: the arr resolves its masked apiKey field
        # server-side, which a schema-shaped body cannot do.
        saved = self._notification(client)
        resp = client.post("/api/v3/notification/test", json=saved)
        if resp.status_code not in (200, 201, 202):
            raise RuntimeError(
                f"{arr} Jellyfin connection test failed: "
                f"HTTP {resp.status_code} {resp.text[:200]}"
            )

    # --- naming -------------------------------------------------------------

    def _naming_ok(self, client, arr):
        resp = client.get("/api/v3/config/naming")
        key, wanted = FOLDER_FORMATS[arr]
        return resp.ok and resp.json().get(key) == wanted

    def _ensure_naming(self, ctx, client, arr):
        if self._naming_ok(client, arr):
            ctx.log.info(f"  {arr}: folder format already Jellyfin-compatible")
            return
        key, wanted = FOLDER_FORMATS[arr]
        naming = client.get("/api/v3/config/naming").json()
        naming[key] = wanted
        resp = client.put("/api/v3/config/naming", json=naming)
        if resp.status_code not in (200, 201, 202):
            raise RuntimeError(
                f"{arr} naming update failed: HTTP {resp.status_code} {resp.text[:200]}"
            )
        ctx.log.info(f"  {arr}: {key} -> {wanted}")

    def _legacy_ids(self, client, arr):
        """Ids of library items still sitting in a pre-[tmdbid-…] folder."""
        resp = client.get(ARRS[arr]["items"])
        if not resp.ok:
            return []
        return [
            item["id"]
            for item in resp.json()
            if FOLDER_ID_MARKER not in item.get("path", "")
        ]

    def _ensure_folders(self, ctx, client, arr):
        ids = self._legacy_ids(client, arr)
        if not ids:
            return
        spec = ARRS[arr]
        # Re-pinning the root folder with moveFiles recomputes every folder name
        # from the format above. Same filesystem, so it is a rename: hardlinks
        # survive and torrents keep seeding.
        resp = client.put(spec["editor"], json={
            spec["ids"]: ids, "rootFolderPath": spec["root"], "moveFiles": True,
        })
        if resp.status_code not in (200, 202):
            raise RuntimeError(
                f"{arr} folder rename failed: HTTP {resp.status_code} {resp.text[:200]}"
            )
        ctx.log.info(f"  {arr}: {len(ids)} folder(s) queued for rename")

    # --- module -------------------------------------------------------------

    def is_done(self, ctx):
        api_key = self._stored_api_key(ctx)
        if not api_key:
            return False
        try:
            for arr in ARRS:
                client = self._client(ctx, arr)
                client.wait_until_up("/api/v3/system/status", timeout=10)
                if not self._notification_ok(self._notification(client), arr, api_key):
                    return False
                if not self._naming_ok(client, arr):
                    return False
                if self._legacy_ids(client, arr):
                    return False
        except (RuntimeError, TimeoutError):
            return False
        return True

    def run(self, ctx):
        token = self._token(ctx)
        if not token:
            raise RuntimeError("Jellyfin authentication failed — run its module first")
        api_key = self._ensure_api_key(ctx, token)
        self._store_api_key(ctx, api_key)

        for arr in ARRS:
            client = self._client(ctx, arr)
            client.wait_until_up("/api/v3/system/status")
            self._ensure_notification(ctx, client, arr, api_key)
            self._ensure_naming(ctx, client, arr)
            self._ensure_folders(ctx, client, arr)


MODULE = JellyfinConnect()
