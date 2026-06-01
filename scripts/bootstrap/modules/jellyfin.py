import time
from urllib.parse import quote

from ..core.http import ApiClient
from ..core.registry import Module

# language -> (UICulture, MetadataCountryCode, PreferredMetadataLanguage)
LOCALES = {
    "en": ("en-US", "US", "en"),
    "fr": ("fr-FR", "FR", "fr"),
}

# (display name, Jellyfin collectionType, in-container path). Only the display
# name is localised; collectionType and path stay stable across languages so a
# library is matched by path (see _library_paths) and stays idempotent.
LIBRARIES_BY_LANG = {
    "en": [
        ("Movies", "movies", "/media/movies"),
        ("TV Shows", "tvshows", "/media/tv"),
    ],
    "fr": [
        ("Films", "movies", "/media/movies"),
        ("Séries", "tvshows", "/media/tv"),
    ],
}


def _libraries(ctx):
    return LIBRARIES_BY_LANG.get(ctx.secrets.language or "en", LIBRARIES_BY_LANG["en"])


def _auth_header(token=None):
    header = (
        'MediaBrowser Client="Dockarr", Device="bootstrap", '
        'DeviceId="dockarr-bootstrap", Version="1.0.0"'
    )
    if token:
        header += f', Token="{token}"'
    return header


def _client(ctx, token=None):
    base = ctx.config.service_url("jellyfin")
    return ApiClient(base, headers={"Authorization": _auth_header(token)})


def _authenticate(ctx, username, password):
    resp = _client(ctx).post(
        "/Users/AuthenticateByName", json={"Username": username, "Pw": password}
    )
    if resp.status_code != 200:
        return None
    return resp.json().get("AccessToken")


class Jellyfin(Module):
    name = "jellyfin"
    depends = ()

    def _library_paths(self, ctx, token):
        resp = _client(ctx, token).get("/Library/VirtualFolders")
        if not resp.ok:
            return set()
        return {loc for vf in resp.json() for loc in vf.get("Locations", [])}

    def is_done(self, ctx):
        creds = ctx.secrets.get("jellyfin")
        if not creds:
            return False
        try:
            _client(ctx).wait_until_up("/System/Info/Public", timeout=10)
        except TimeoutError:
            return False
        token = _authenticate(ctx, creds["username"], creds["password"])
        if not token:
            return False
        paths = self._library_paths(ctx, token)
        if not all(path in paths for _, _, path in _libraries(ctx)):
            return False
        return self._network_ok(ctx, token)

    def run(self, ctx):
        client = _client(ctx)
        client.wait_until_up("/System/Info/Public")

        info = client.get("/System/Info/Public").json()
        if not info.get("StartupWizardCompleted"):
            username, password = ctx.secrets.create("jellyfin")
            resp = self._create_admin(client, username, password)
            if resp.status_code not in (200, 204):
                raise RuntimeError(f"create admin failed: HTTP {resp.status_code}")
            ui_culture, country, metadata_lang = LOCALES.get(
                ctx.secrets.language or "en", LOCALES["en"]
            )
            client.post(
                "/Startup/Configuration",
                json={
                    "UICulture": ui_culture,
                    "MetadataCountryCode": country,
                    "PreferredMetadataLanguage": metadata_lang,
                },
            )
            client.post("/Startup/Complete")
            ctx.log.info(f"  admin '{username}' created, wizard completed ({ui_culture})")
        elif not ctx.secrets.get("jellyfin"):
            raise RuntimeError(
                "Jellyfin already set up but credentials unknown — run 'make reset'"
            )

        creds = ctx.secrets.get("jellyfin")
        token = _authenticate(ctx, creds["username"], creds["password"])
        if not token:
            raise RuntimeError("Jellyfin authentication failed after setup")

        self._ensure_libraries(ctx, token)
        self._ensure_network(ctx, token)

    def _network_ok(self, ctx, token):
        resp = _client(ctx, token).get("/System/Configuration/network")
        return resp.ok and not resp.json().get("LocalNetworkAddresses")

    def _ensure_network(self, ctx, token):
        # Jellyfin defaults LocalNetworkAddresses to "::", which filters out the
        # container's real interface: NetworkManager then falls back to the
        # loopback for every request and spams the log with
        # "Only loopback ::1 returned, using that as bind address". Clearing it
        # lets Jellyfin bind to all interfaces normally (refreshes live).
        client = _client(ctx, token)
        resp = client.get("/System/Configuration/network")
        if not resp.ok or not resp.json().get("LocalNetworkAddresses"):
            return
        config = resp.json()
        config["LocalNetworkAddresses"] = []
        updated = client.post("/System/Configuration/network", json=config)
        if updated.status_code not in (200, 204):
            raise RuntimeError(
                f"network config update failed: HTTP {updated.status_code} {updated.text[:200]}"
            )
        ctx.log.info("  cleared LocalNetworkAddresses bind override")

    def _create_admin(self, client, username, password):
        # Jellyfin 10.11 no longer auto-creates the first user on boot. The
        # default admin row is provisioned lazily by GET /Startup/User; without
        # it POST /Startup/User has nothing to update and returns 404.
        for _ in range(5):
            if client.get("/Startup/User").ok:
                break
            time.sleep(2)
        return client.post(
            "/Startup/User", json={"Name": username, "Password": password}
        )

    def _ensure_libraries(self, ctx, token):
        client = _client(ctx, token)
        existing = self._library_paths(ctx, token)
        for name, collection_type, path in _libraries(ctx):
            if path in existing:
                ctx.log.info(f"  library '{name}' already present")
                continue
            resp = client.post(
                f"/Library/VirtualFolders?name={quote(name)}"
                f"&collectionType={collection_type}&refreshLibrary=true",
                json={"LibraryOptions": {"PathInfos": [{"Path": path}]}},
            )
            if resp.status_code not in (200, 204):
                raise RuntimeError(
                    f"create library '{name}' failed: HTTP {resp.status_code} {resp.text[:200]}"
                )
            ctx.log.info(f"  library '{name}' -> {path}")


MODULE = Jellyfin()
