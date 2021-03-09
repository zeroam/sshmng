import pickle
import subprocess
from pathlib import Path
from typing import Dict


class Repo(object):
    """File Repository Class
    have path for home directory, data path
    get hosts, and save hosts with get_hosts(), save_hosts()
    """
    def __init__(self, debug=False):
        self.home = Path.home() / ".sshmng"
        self._db = self.home / "hosts.pkl"
        self.private_key = self.home / "id_ed25519"
        self.public_key = self.home / "id_ed25519.pub"
        self.debug = debug

    @property
    def home(self):
        return self._home

    @home.setter
    def home(self, path: Path):
        path.mkdir(exist_ok=True)
        self._home = path

    @property
    def private_key(self):
        return self._private_key

    @private_key.setter
    def private_key(self, path: Path):
        if not path.exists():
            # make ssh key pairs
            subprocess.call(f"ssh-keygen -t ed25519 -q -f \"{path.absolute()}\" -N \"\"", shell=True)
        self._private_key = path

    def load_hosts(self):
        if not self._db.exists():
            return {}

        with self._db.open("rb") as f:
            hosts = pickle.load(f)
        return hosts

    def save_hosts(self, hosts: Dict[str, str]):
        with self._db.open("wb") as f:
            pickle.dump(hosts, f)
