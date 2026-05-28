import os
from pathlib import Path

# Default host ports each service is published on (see docker-compose.yml).
DEFAULT_PORTS = {
    "qbittorrent": 8080,
    "qui": 7476,
    "prowlarr": 9696,
    "radarr": 7878,
    "sonarr": 8989,
    "profilarr": 6868,
    "seerr": 5055,
    "jellyfin": 8096,
    "kavita": 5000,
}


def _load_dotenv(path=".env"):
    p = Path(path)
    if not p.exists():
        return
    for line in p.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())


class Config:
    def __init__(self):
        _load_dotenv()
        # When the stack runs on a remote host, point the bootstrap there.
        self.host = os.environ.get("DOCKARR_BOOTSTRAP_HOST", "localhost")
        self.ports = dict(DEFAULT_PORTS)
        # Per-service host-port override, e.g. KAVITA_PORT=5001 (avoids the
        # macOS AirPlay conflict on :5000).
        for svc in self.ports:
            override = os.environ.get(f"{svc.upper()}_PORT")
            if override and override.isdigit():
                self.ports[svc] = int(override)
        webui = os.environ.get("QBITTORRENT_WEBUI_PORT")
        if webui and webui.isdigit():
            self.ports["qbittorrent"] = int(webui)

    def service_url(self, name):
        return f"http://{self.host}:{self.ports[name]}"
