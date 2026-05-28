import time

import requests


class ApiClient:
    def __init__(self, base_url, headers=None, timeout=15):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()
        if headers:
            self.session.headers.update(headers)

    def _url(self, path):
        return f"{self.base_url}{path}"

    def get(self, path, **kwargs):
        kwargs.setdefault("timeout", self.timeout)
        return self.session.get(self._url(path), **kwargs)

    def post(self, path, **kwargs):
        kwargs.setdefault("timeout", self.timeout)
        return self.session.post(self._url(path), **kwargs)

    def put(self, path, **kwargs):
        kwargs.setdefault("timeout", self.timeout)
        return self.session.put(self._url(path), **kwargs)

    def delete(self, path, **kwargs):
        kwargs.setdefault("timeout", self.timeout)
        return self.session.delete(self._url(path), **kwargs)

    def wait_until_up(self, path="/", timeout=180, interval=2):
        """Block until the endpoint answers with a non-5xx status."""
        deadline = time.time() + timeout
        last = None
        while time.time() < deadline:
            try:
                resp = self.session.get(self._url(path), timeout=self.timeout)
                if resp.status_code < 500:
                    return True
                last = resp.status_code
            except requests.RequestException as exc:
                last = exc
            time.sleep(interval)
        raise TimeoutError(f"{self.base_url}{path} not reachable (last={last})")
