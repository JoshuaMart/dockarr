from ..core.http import ApiClient
from ..core.registry import Module

QBITTORRENT_HOST = "http://qbittorrent:8080"


class Qui(Module):
    name = "qui"
    depends = ("qbittorrent",)

    def _client(self, ctx):
        return ApiClient(ctx.config.service_url("qui"))

    def _login(self, client, username, password):
        client.session.cookies.clear()
        resp = client.post(
            "/api/auth/login",
            json={"username": username, "password": password, "remember_me": True},
        )
        return resp.status_code == 200

    def is_done(self, ctx):
        creds = ctx.secrets.get("qui")
        if not creds:
            return False
        client = self._client(ctx)
        try:
            client.wait_until_up("/", timeout=10)
        except TimeoutError:
            return False
        return self._login(client, creds["username"], creds["password"])

    def run(self, ctx):
        client = self._client(ctx)
        client.wait_until_up("/")

        username, password = ctx.secrets.create("qui")
        resp = client.post(
            "/api/auth/setup", json={"username": username, "password": password}
        )
        if resp.status_code == 201:
            ctx.log.info(f"  admin account '{username}' created")
        elif resp.status_code == 400 and "already" in resp.text.lower():
            if not self._login(client, username, password):
                raise RuntimeError(
                    "qui already set up but stored credentials are unknown — "
                    "run 'make reset' to start clean"
                )
        else:
            raise RuntimeError(f"qui setup failed: HTTP {resp.status_code} {resp.text[:200]}")

        self._register_qbittorrent(ctx, client)

    def _register_qbittorrent(self, ctx, client):
        qb = ctx.secrets.get("qbittorrent")
        if not qb:
            raise RuntimeError("qbittorrent credentials missing — run its module first")

        existing = client.get("/api/instances")
        if existing.ok and any(
            i.get("host", "").rstrip("/") == QBITTORRENT_HOST
            for i in existing.json()
        ):
            ctx.log.info("  qBittorrent instance already registered")
            return

        resp = client.post(
            "/api/instances",
            json={
                "name": "qbittorrent",
                "host": QBITTORRENT_HOST,
                "username": qb["username"],
                "password": qb["password"],
                "tlsSkipVerify": False,
            },
        )
        if resp.status_code not in (200, 201):
            raise RuntimeError(
                f"registering qBittorrent in qui failed: HTTP {resp.status_code} {resp.text[:200]}"
            )
        ctx.log.info("  qBittorrent instance registered")


MODULE = Qui()
