import logging

from .config import Config
from .secrets import SecretStore


class Context:
    def __init__(self):
        self.config = Config()
        self.secrets = SecretStore()
        self.log = logging.getLogger("dockarr")


def build_context():
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    return Context()
