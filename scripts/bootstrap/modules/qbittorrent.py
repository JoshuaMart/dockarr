import json
import re
import subprocess

from ..core.http import ApiClient
from ..core.registry import Module

CONTAINER = "qbittorrent"
TEMP_PASSWORD_RE = re.compile(
    r"temporary password is provided for this session:\s*(\S+)"
)


def _client(ctx):
    base = ctx.config.service_url("qbittorrent")
    # qBittorrent's CSRF/host-header checks reject requests without a matching
    # Referer/Origin, so we set them to the WebUI base URL.
    return ApiClient(base, headers={"Referer": base, "Origin": base})


def _login(client, username, password):
    # Clear any prior session so a stale cookie can't mask a failed login.
    client.session.cookies.clear()
    resp = client.post(
        "/api/v2/auth/login",
        data={"username": username, "password": password},
    )
    # qBittorrent returns 200 ("Ok.") on older builds, 204 on v5+, 401 on failure.
    return resp.status_code in (200, 204)


def _temp_password():
    result = subprocess.run(
        ["docker", "logs", CONTAINER],
        capture_output=True,
        text=True,
    )
    logs = result.stdout + result.stderr
    matches = TEMP_PASSWORD_RE.findall(logs)
    if not matches:
        raise RuntimeError(
            "no temporary password found in 'docker logs qbittorrent' — "
            "is the container running?"
        )
    return matches[-1]  # most recent container start


class QBittorrent(Module):
    name = "qbittorrent"
    depends = ()

    def is_done(self, ctx):
        creds = ctx.secrets.get("qbittorrent")
        if not creds:
            return False
        client = _client(ctx)
        try:
            client.wait_until_up("/", timeout=10)
        except TimeoutError:
            return False
        return _login(client, creds["username"], creds["password"])

    def run(self, ctx):
        client = _client(ctx)
        client.wait_until_up("/")

        if not _login(client, "admin", _temp_password()):
            raise RuntimeError(
                "login with the temporary password failed "
                "(was it already changed manually?)"
            )

        username, password = ctx.secrets.create("qbittorrent")
        prefs = {"web_ui_username": username, "web_ui_password": password}
        resp = client.post(
            "/api/v2/app/setPreferences",
            data={"json": json.dumps(prefs)},
        )
        if resp.status_code != 200:
            raise RuntimeError(f"setPreferences failed: HTTP {resp.status_code}")

        # Changing the credentials invalidates the session — verify the new ones.
        if not _login(client, username, password):
            raise RuntimeError("could not log in with the new credentials")

        ctx.log.info(
            f"  account '{username}' set (password in secrets/credentials.json)"
        )


MODULE = QBittorrent()
