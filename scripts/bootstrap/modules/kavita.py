import subprocess

from ..core import dotenv
from ..core.http import ApiClient
from ..core.registry import Module

CONTAINER = "kavita"
# Compose profile gating the service (see docker-compose.yml). Its presence in
# .env's COMPOSE_PROFILES decides whether `make up` / `make update` start Kavita.
PROFILE = "kavita"

# (display name, Kavita LibraryType enum, in-container folder). Kavita parses
# each library according to its single type, so books are split by content type
# rather than dumped in one mixed library. 0=Manga, 1=Comic, 2=Book.
LIBRARIES = [
    ("Manga", 0, "/books/manga"),
    ("Comics", 1, "/books/comics"),
    # BD (bandes dessinées européennes): no dedicated type, Comic fits the format.
    ("BD", 1, "/books/bd"),
    ("Livres", 2, "/books/livres"),
]
# Archive (cbz/cbr), Epub, Pdf, Images — the permissive default, valid for any
# library type.
FILE_GROUP_TYPES = [1, 2, 3, 4]


def _container_running():
    result = subprocess.run(
        ["docker", "inspect", "-f", "{{.State.Running}}", CONTAINER],
        capture_output=True,
        text=True,
    )
    return result.returncode == 0 and result.stdout.strip() == "true"


def _env_profiles():
    raw = dotenv.get_var("COMPOSE_PROFILES", "")
    return [p.strip() for p in raw.split(",") if p.strip()]


def _env_has_profile():
    """Whether .env's COMPOSE_PROFILES currently lists the kavita profile."""
    return PROFILE in _env_profiles()


def _set_env_profile(enabled):
    """Add or remove the kavita profile in .env's COMPOSE_PROFILES so that a
    plain `docker compose up` (make up / make update) honours the choice without
    a re-bootstrap. Returns True when .env was changed."""
    profiles = _env_profiles()
    if enabled and PROFILE not in profiles:
        profiles.append(PROFILE)
    elif not enabled and PROFILE in profiles:
        profiles = [p for p in profiles if p != PROFILE]
    else:
        return False
    if profiles:
        return dotenv.set_var("COMPOSE_PROFILES", ",".join(profiles))
    return dotenv.unset_var("COMPOSE_PROFILES")


class Kavita(Module):
    name = "kavita"
    depends = ()

    def _enabled(self, ctx):
        cfg = ctx.secrets.kavita
        return True if cfg is None else cfg.get("enabled", True)

    def _client(self, ctx):
        return ApiClient(ctx.config.service_url("kavita"))

    def _authed(self, ctx, token):
        return ApiClient(
            ctx.config.service_url("kavita"),
            headers={"Authorization": f"Bearer {token}"},
        )

    def _token(self, client, username, password):
        resp = client.post(
            "/api/Account/login",
            json={"username": username, "password": password},
        )
        if resp.status_code != 200:
            return None
        return resp.json().get("token")

    def _login(self, client, username, password):
        return self._token(client, username, password) is not None

    def _set_locale(self, ctx, token):
        lang = ctx.secrets.language or "en"
        client = self._authed(ctx, token)
        resp = client.get("/api/Users/get-preferences")
        if not resp.ok:
            return
        prefs = resp.json()
        if prefs.get("locale") == lang:
            return
        prefs["locale"] = lang
        if client.post("/api/Users/update-preferences", json=prefs).ok:
            ctx.log.info(f"  UI language set to {lang}")

    def _library_folders(self, client):
        resp = client.get("/api/Library/libraries")
        if not resp.ok:
            return set()
        return {folder for lib in resp.json() for folder in lib.get("folders", [])}

    def _ensure_libraries(self, ctx, token):
        client = self._authed(ctx, token)
        existing = self._library_folders(client)
        for name, lib_type, folder in LIBRARIES:
            if folder in existing:
                ctx.log.info(f"  library '{name}' already present")
                continue
            resp = client.post(
                "/api/Library/create",
                json={
                    "name": name,
                    "type": lib_type,
                    "folders": [folder],
                    "fileGroupTypes": FILE_GROUP_TYPES,
                    "excludePatterns": [],
                    # Kavita defaults both to false on API-created libraries.
                    # Without enableMetadata it ignores embedded ComicInfo.xml
                    # (authors, summary, genres, even the <Series> grouping);
                    # without includeInDashboard the library is hidden from Home.
                    "enableMetadata": True,
                    "includeInDashboard": True,
                },
            )
            if not resp.ok:
                raise RuntimeError(
                    f"create library '{name}' failed: HTTP {resp.status_code} "
                    f"{resp.text[:200]}"
                )
            ctx.log.info(f"  library '{name}' -> {folder}")

    def is_done(self, ctx):
        enabled = self._enabled(ctx)
        # The .env profile flag must match the choice, otherwise `make up` /
        # `make update` would start (or keep starting) the wrong container.
        if _env_has_profile() != enabled:
            return False
        if not enabled:
            # Disabled: the only remaining "work" is the container being stopped.
            return not _container_running()
        creds = ctx.secrets.get("kavita")
        if not creds:
            return False
        client = self._client(ctx)
        try:
            client.wait_until_up("/api/health", timeout=10)
        except TimeoutError:
            return False
        token = self._token(client, creds["username"], creds["password"])
        if not token:
            return False
        folders = self._library_folders(self._authed(ctx, token))
        return all(folder in folders for _, _, folder in LIBRARIES)

    def run(self, ctx):
        if not self._enabled(ctx):
            # Drop the profile so future `make up` / `make update` skip Kavita.
            if _set_env_profile(False):
                ctx.log.info("  Kavita profile removed from .env")
            if _container_running():
                subprocess.run(
                    ["docker", "compose", "stop", CONTAINER], capture_output=True
                )
                ctx.log.info("  Kavita disabled, container stopped")
            else:
                ctx.log.info("  Kavita disabled, skipping")
            return

        # Keep the profile so future `make up` / `make update` keep Kavita.
        if _set_env_profile(True):
            ctx.log.info("  Kavita profile added to .env")
        # Bring the container up. Naming the service explicitly creates/starts it
        # even when its profile is inactive, so this works on the very first run.
        if not _container_running():
            subprocess.run(
                ["docker", "compose", "up", "-d", CONTAINER], capture_output=True
            )
            ctx.log.info("  Kavita container started")

        client = self._client(ctx)
        client.wait_until_up("/api/health")

        username, password = ctx.secrets.create("kavita")
        # The first registered user is auto-promoted to admin; the endpoint is
        # locked once an admin exists.
        resp = client.post(
            "/api/Account/register",
            json={"username": username, "password": password},
        )
        if resp.status_code == 200:
            ctx.log.info(f"  admin account '{username}' created")
            token = resp.json().get("token") or self._token(client, username, password)
        else:
            token = self._token(client, username, password)
            if not token:
                raise RuntimeError(
                    f"kavita register failed: HTTP {resp.status_code} {resp.text[:200]} "
                    "(an admin may already exist — run 'make reset' to start clean)"
                )

        if not token:
            raise RuntimeError("kavita authentication failed after setup")
        self._set_locale(ctx, token)
        self._ensure_libraries(ctx, token)


MODULE = Kavita()
