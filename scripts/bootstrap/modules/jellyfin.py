import time
from urllib.parse import quote

from ..core.http import ApiClient
from ..core.registry import Module

# language -> (UICulture, MetadataCountryCode, PreferredMetadataLanguage)
LOCALES = {
    "en": ("en-US", "US", "en"),
    "fr": ("fr-FR", "FR", "fr"),
}

# (display name, Jellyfin collectionType, in-container path)
LIBRARIES = [
    ("Movies", "movies", "/media/movies"),
    ("TV Shows", "tvshows", "/media/tv"),
]


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
        return all(path in paths for _, _, path in LIBRARIES)

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

    def _create_admin(self, client, username, password):
        # On a fresh boot the first user is initialised asynchronously, so
        # /Startup/User can briefly 404 until it exists.
        resp = None
        for _ in range(5):
            resp = client.post(
                "/Startup/User", json={"Name": username, "Password": password}
            )
            if resp.status_code != 404:
                return resp
            time.sleep(2)
        return resp

    def _ensure_libraries(self, ctx, token):
        client = _client(ctx, token)
        existing = self._library_paths(ctx, token)
        for name, collection_type, path in LIBRARIES:
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
