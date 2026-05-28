import json
import os
import secrets as secretslib
import string
from pathlib import Path

PASSWORD_LENGTH = 20
USERNAME_LENGTH = 10
STORE_PATH = Path("secrets/credentials.json")


def gen_password(length=PASSWORD_LENGTH):
    alphabet = string.ascii_letters + string.digits
    return "".join(secretslib.choice(alphabet) for _ in range(length))


def gen_username(length=USERNAME_LENGTH):
    return "".join(secretslib.choice(string.ascii_lowercase) for _ in range(length))


class SecretStore:
    """Persists generated credentials and the credential policy to a
    gitignored JSON file so later modules can reuse them."""

    def __init__(self, path=STORE_PATH):
        self.path = Path(path)
        self.data = {}
        if self.path.exists():
            self.data = json.loads(self.path.read_text())

    @property
    def policy(self):
        return self.data.get("_policy")

    @property
    def language(self):
        return self.data.get("_language")

    def set_language(self, language):
        self.data["_language"] = language
        self.save()

    @property
    def profilarr_fr(self):
        return self.data.get("_profilarr_fr")

    def set_profilarr_fr(self, enabled, profile=None):
        self.data["_profilarr_fr"] = {"enabled": enabled, "profile": profile}
        self.save()

    def set_policy(self, username, password_mode, shared_password=None):
        self.data["_policy"] = {
            "username": username,
            "password_mode": password_mode,  # "shared" | "per_service"
            "shared_password": shared_password,
        }
        self.save()

    def get(self, service):
        return self.data.get("services", {}).get(service)

    def set(self, service, **fields):
        self.data.setdefault("services", {})[service] = fields
        self.save()

    def create(self, service):
        """Allocate credentials for a service according to the policy."""
        policy = self.policy
        username = policy["username"]
        if policy["password_mode"] == "shared":
            password = policy["shared_password"]
        else:
            password = gen_password()
        self.set(service, username=username, password=password)
        return username, password

    def save(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self.data, indent=2) + "\n")
        os.chmod(self.path, 0o600)
