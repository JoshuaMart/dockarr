import re
import subprocess

from ..core.http import ApiClient
from ..core.registry import Module

API_KEY_RE = re.compile(r"<ApiKey>([^<]+)</ApiKey>")


def _api_key(container):
    result = subprocess.run(
        ["docker", "exec", container, "cat", "/config/config.xml"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"cannot read {container} config.xml: {result.stderr.strip()}"
        )
    match = API_KEY_RE.search(result.stdout)
    if not match:
        raise RuntimeError(f"no ApiKey found in {container} config.xml")
    return match.group(1)


class ServarrModule(Module):
    """Radarr / Sonarr / Prowlarr share the same *arr config API: the API key
    is generated in config.xml, and Forms authentication is enabled via
    PUT /api/{version}/config/host (the API key bypasses Forms login, so
    inter-app wiring keeps working)."""

    def __init__(self, name, api_version):
        self.name = name
        self.api_version = api_version
        self.depends = ()

    def _client(self, ctx):
        base = ctx.config.service_url(self.name)
        return ApiClient(base, headers={"X-Api-Key": _api_key(self.name)})

    def _host_path(self):
        return f"/api/{self.api_version}/config/host"

    def is_done(self, ctx):
        if not ctx.secrets.get(self.name):
            return False
        try:
            client = self._client(ctx)
            client.wait_until_up(f"/api/{self.api_version}/system/status", timeout=10)
            resp = client.get(self._host_path())
        except (RuntimeError, TimeoutError):
            return False
        return resp.ok and resp.json().get("authenticationMethod", "none") != "none"

    def run(self, ctx):
        client = self._client(ctx)
        client.wait_until_up(f"/api/{self.api_version}/system/status")

        resp = client.get(self._host_path())
        if resp.status_code != 200:
            raise RuntimeError(f"GET config/host failed: HTTP {resp.status_code}")
        host = resp.json()

        username, password = ctx.secrets.create(self.name)
        host.update(
            {
                "authenticationMethod": "forms",
                "authenticationRequired": "enabled",
                "username": username,
                "password": password,
                "passwordConfirmation": password,
            }
        )
        put = client.put(self._host_path(), json=host)
        if put.status_code not in (200, 202):
            raise RuntimeError(
                f"PUT config/host failed: HTTP {put.status_code} {put.text[:200]}"
            )
        ctx.log.info(f"  Forms auth enabled for '{username}'")


RADARR = ServarrModule("radarr", "v3")
SONARR = ServarrModule("sonarr", "v3")
PROWLARR = ServarrModule("prowlarr", "v1")
