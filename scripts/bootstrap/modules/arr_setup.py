from ..core.http import ApiClient
from ..core.registry import Module
from .servarr import _api_key

QBITTORRENT_HOST = "qbittorrent"
QBITTORRENT_PORT = 8080


def _fill_fields(schema, values):
    for field in schema["fields"]:
        if field["name"] in values:
            field["value"] = values[field["name"]]
    return schema


class ArrSetupModule(Module):
    """Wire a Radarr/Sonarr instance to qBittorrent: add the download client
    and the media root folder. Both steps are idempotent."""

    def __init__(self, arr, category_field, category_value, root_path):
        self.arr = arr
        self.category_field = category_field
        self.category_value = category_value
        self.root_path = root_path
        self.name = f"{arr}-setup"
        self.depends = (arr, "qbittorrent")

    def _client(self, ctx):
        base = ctx.config.service_url(self.arr)
        return ApiClient(base, headers={"X-Api-Key": _api_key(self.arr)})

    def is_done(self, ctx):
        try:
            client = self._client(ctx)
            client.wait_until_up("/api/v3/system/status", timeout=10)
            clients = client.get("/api/v3/downloadclient")
            folders = client.get("/api/v3/rootfolder")
        except (RuntimeError, TimeoutError):
            return False
        if not (clients.ok and folders.ok):
            return False
        has_client = any(c.get("implementation") == "QBittorrent" for c in clients.json())
        has_folder = any(f.get("path") == self.root_path for f in folders.json())
        return has_client and has_folder

    def run(self, ctx):
        client = self._client(ctx)
        client.wait_until_up("/api/v3/system/status")
        self._ensure_download_client(ctx, client)
        self._ensure_root_folder(ctx, client)

    def _ensure_download_client(self, ctx, client):
        if any(
            c.get("implementation") == "QBittorrent"
            for c in client.get("/api/v3/downloadclient").json()
        ):
            ctx.log.info("  download client already present")
            return

        qb = ctx.secrets.get("qbittorrent")
        if not qb:
            raise RuntimeError("qbittorrent credentials missing — run its module first")

        schema = next(
            s
            for s in client.get("/api/v3/downloadclient/schema").json()
            if s.get("implementation") == "QBittorrent"
        )
        _fill_fields(
            schema,
            {
                "host": QBITTORRENT_HOST,
                "port": QBITTORRENT_PORT,
                "username": qb["username"],
                "password": qb["password"],
                self.category_field: self.category_value,
            },
        )
        schema.update({"enable": True, "name": "qBittorrent"})
        resp = client.post("/api/v3/downloadclient", json=schema)
        if resp.status_code not in (200, 201):
            raise RuntimeError(
                f"add download client failed: HTTP {resp.status_code} {resp.text[:200]}"
            )
        ctx.log.info("  qBittorrent download client added")

    def _ensure_root_folder(self, ctx, client):
        if any(
            f.get("path") == self.root_path
            for f in client.get("/api/v3/rootfolder").json()
        ):
            ctx.log.info("  root folder already present")
            return
        resp = client.post("/api/v3/rootfolder", json={"path": self.root_path})
        if resp.status_code not in (200, 201):
            raise RuntimeError(
                f"add root folder failed: HTTP {resp.status_code} {resp.text[:200]}"
            )
        ctx.log.info(f"  root folder {self.root_path} added")


RADARR_SETUP = ArrSetupModule("radarr", "movieCategory", "radarr", "/data/media/movies")
SONARR_SETUP = ArrSetupModule("sonarr", "tvCategory", "sonarr", "/data/media/tv")
