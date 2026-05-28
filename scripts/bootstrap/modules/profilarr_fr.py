import json
import time

from ..core.http import ApiClient
from ..core.registry import Module
from .profilarr import _client, _login
from .servarr import _api_key

REPO_URL = "https://github.com/Jojont54/Profilarr-database-french-regex"
BRANCH = "develop"
DB_NAME = "French DB"

# Profilarr "arr" connection name -> the matching servarr module / host.
ARRS = [
    {"name": "Radarr", "key": "radarr", "url": "http://radarr:7878"},
    {"name": "Sonarr", "key": "sonarr", "url": "http://sonarr:8989"},
]

# SvelteKit form actions reject a body-less POST (415), so send an empty
# url-encoded body with an explicit content type.
_FORM_CT = {"Content-Type": "application/x-www-form-urlencoded"}


class ProfilarrFr(Module):
    """Optional French auto-config: wipe Profilarr's database, clone the French
    regex DB and push the chosen quality profile to Radarr & Sonarr. No-op when
    the user declined the prompt. Runs before Seerr so the profile exists when
    Seerr wires its default servers."""

    name = "profilarr-fr"
    depends = ("profilarr-targets", "radarr", "sonarr")

    def _profile(self, ctx):
        cfg = ctx.secrets.profilarr_fr or {}
        return cfg.get("profile") if cfg.get("enabled") else None

    def _arr_client(self, ctx, key):
        return ApiClient(
            ctx.config.service_url(key), headers={"X-Api-Key": _api_key(key)}
        )

    def _arr_has_profile(self, ctx, key, profile):
        resp = self._arr_client(ctx, key).get("/api/v3/qualityprofile")
        return resp.ok and any(p.get("name") == profile for p in resp.json())

    def is_done(self, ctx):
        profile = self._profile(ctx)
        if profile is None:
            return True  # disabled — nothing to provision
        try:
            return all(self._arr_has_profile(ctx, a["key"], profile) for a in ARRS)
        except (RuntimeError, TimeoutError):
            return False

    def run(self, ctx):
        profile = self._profile(ctx)
        if profile is None:
            ctx.log.info("  Profilarr FR auto-config disabled — skipping")
            return

        creds = ctx.secrets.get("profilarr")
        if not creds:
            raise RuntimeError("profilarr not provisioned — run its module first")
        client = _client(ctx)
        client.wait_until_up("/api/v1/health")
        if not _login(client, creds["username"], creds["password"]):
            raise RuntimeError("profilarr login failed")

        db_id = self._ensure_database(ctx, client)
        for arr in ARRS:
            self._configure_arr(ctx, client, arr, db_id, profile)

    def _ensure_database(self, ctx, client):
        existing = client.get("/api/v1/databases").json()
        french = next(
            (d for d in existing if d.get("repository_url", "").rstrip("/") == REPO_URL),
            None,
        )
        for db in existing:
            if db is french:
                continue
            client.delete(f"/api/v1/databases/{db['id']}")
            ctx.log.info(f"  removed database '{db.get('name')}'")

        if french:
            ctx.log.info(f"  French DB already present (id {french['id']})")
            return french["id"]

        resp = client.post(
            "/api/v1/databases",
            json={"name": DB_NAME, "repository_url": REPO_URL, "branch": BRANCH},
        )
        if resp.status_code not in (200, 201):
            raise RuntimeError(
                f"add French DB failed: HTTP {resp.status_code} {resp.text[:200]}"
            )
        ctx.log.info(f"  French DB cloned (branch {BRANCH})")
        return resp.json()["id"]

    def _arr_id(self, client, url):
        for arr in client.get("/api/v1/arr").json():
            if arr.get("url", "").rstrip("/") == url:
                return arr["id"]
        return None

    def _form(self, client, arr_id, action, data=None):
        # A profile sync only succeeds once media management + delay profiles
        # are already pushed, so the caller drives the three sections in order.
        if data is None:
            resp = client.post(
                f"/arr/{arr_id}/sync?/{action}", data="", headers=_FORM_CT
            )
        else:
            resp = client.post(f"/arr/{arr_id}/sync?/{action}", data=data)
        if resp.json().get("type") != "success":
            raise RuntimeError(f"{action} failed: HTTP {resp.status_code} {resp.text[:200]}")

    def _configure_arr(self, ctx, client, arr, db_id, profile):
        arr_id = self._arr_id(client, arr["url"])
        if arr_id is None:
            raise RuntimeError(f"{arr['name']} is not registered as a Profilarr target")

        # Config and delay-profile names mirror the instance name in the French DB.
        cfg = arr["name"]

        self._form(client, arr_id, "saveMediaManagement", {
            "namingConfigName": cfg, "namingDatabaseId": db_id,
            "qualityDefinitionsConfigName": cfg, "qualityDefinitionsDatabaseId": db_id,
            "mediaSettingsConfigName": cfg, "mediaSettingsDatabaseId": db_id,
            "trigger": "manual",
        })
        self._form(client, arr_id, "syncMediaManagement")

        self._form(client, arr_id, "saveDelayProfiles", {
            "databaseId": db_id, "profileName": cfg, "trigger": "manual",
        })
        self._form(client, arr_id, "syncDelayProfiles")

        # Custom formats are pulled in automatically with the quality profile.
        selections = json.dumps([{"databaseId": db_id, "profileName": profile}])
        self._form(client, arr_id, "saveQualityProfiles",
                   {"selections": selections, "trigger": "manual"})
        self._form(client, arr_id, "syncQualityProfiles")

        self._wait_for_profile(ctx, arr, profile)
        ctx.log.info(
            f"  {arr['name']} configured (media mgmt + delay + profile '{profile}')"
        )

    def _wait_for_profile(self, ctx, arr, profile, timeout=30):
        deadline = time.time() + timeout
        while time.time() < deadline:
            if self._arr_has_profile(ctx, arr["key"], profile):
                return
            time.sleep(2)
        raise RuntimeError(
            f"profile '{profile}' did not appear in {arr['name']} within "
            f"{timeout}s — does it exist in the French DB?"
        )


MODULE = ProfilarrFr()
