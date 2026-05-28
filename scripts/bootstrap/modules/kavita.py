from ..core.http import ApiClient
from ..core.registry import Module


class Kavita(Module):
    name = "kavita"
    depends = ()

    def _client(self, ctx):
        return ApiClient(ctx.config.service_url("kavita"))

    def _login(self, client, username, password):
        resp = client.post(
            "/api/Account/login",
            json={"username": username, "password": password},
        )
        return resp.status_code == 200

    def is_done(self, ctx):
        creds = ctx.secrets.get("kavita")
        if not creds:
            return False
        client = self._client(ctx)
        try:
            client.wait_until_up("/api/health", timeout=10)
        except TimeoutError:
            return False
        return self._login(client, creds["username"], creds["password"])

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
            return

        if self._login(client, username, password):
            return
        raise RuntimeError(
            f"kavita register failed: HTTP {resp.status_code} {resp.text[:200]} "
            "(an admin may already exist — run 'make reset' to start clean)"
        )


MODULE = Kavita()
