from ..core.http import ApiClient
from ..core.registry import Module


def _client(ctx):
    base = ctx.config.service_url("profilarr")
    # Profilarr uses SvelteKit form actions: form-encoded body + the
    # x-sveltekit-action header, with an Origin matching the app (CSRF).
    return ApiClient(base, headers={"x-sveltekit-action": "true", "Origin": base})


def _logged_in(client):
    return "session" in client.session.cookies.get_dict()


def _login(client, username, password):
    client.session.cookies.clear()
    client.post("/auth/login", data={"username": username, "password": password})
    return _logged_in(client)


class Profilarr(Module):
    name = "profilarr"
    depends = ()

    def is_done(self, ctx):
        creds = ctx.secrets.get("profilarr")
        if not creds:
            return False
        client = _client(ctx)
        try:
            client.wait_until_up("/api/v1/health", timeout=10)
        except TimeoutError:
            return False
        return _login(client, creds["username"], creds["password"])

    def run(self, ctx):
        client = _client(ctx)
        client.wait_until_up("/api/v1/health")

        username, password = ctx.secrets.create("profilarr")
        client.session.cookies.clear()
        client.post(
            "/auth/setup",
            data={
                "username": username,
                "password": password,
                "confirmPassword": password,
            },
        )
        # Success sets a `session` cookie. If setup didn't auto-login, a fresh
        # login with the new credentials confirms the account was created.
        if _logged_in(client) or _login(client, username, password):
            ctx.log.info(f"  account '{username}' created")
            return
        raise RuntimeError(
            "profilarr setup failed or already provisioned with unknown "
            "credentials — run 'make reset' to start clean"
        )


MODULE = Profilarr()
