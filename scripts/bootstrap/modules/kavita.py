from ..core.http import ApiClient
from ..core.registry import Module

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


class Kavita(Module):
    name = "kavita"
    depends = ()

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
                },
            )
            if not resp.ok:
                raise RuntimeError(
                    f"create library '{name}' failed: HTTP {resp.status_code} "
                    f"{resp.text[:200]}"
                )
            ctx.log.info(f"  library '{name}' -> {folder}")

    def is_done(self, ctx):
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
