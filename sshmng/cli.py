"""Console script for sshmng."""
import sys
import click
import pickle
import subprocess
from pathlib import Path
from pprint import pprint
from typing import Dict


class Repo(object):
    """File Repository Class
    have path for home directory, data path
    get hosts, and save hosts with get_hosts(), save_hosts()
    """
    def __init__(self, debug=False):
        self.home = Path.home() / ".sshmng"
        self._db = self.home / "hosts.pkl"
        self.debug = debug

    @property
    def home(self):
        return self._home

    @home.setter
    def home(self, path: Path):
        path.mkdir(exist_ok=True)
        self._home = path

    def load_hosts(self):
        if not self._db.exists():
            return {}

        with self._db.open("rb") as f:
            hosts = pickle.load(f)
        return hosts

    def save_hosts(self, hosts: Dict[str, str]):
        with self._db.open("wb") as f:
            pickle.dump(hosts, f)


@click.group()
@click.option("--debug/--nodebug", default=False, envvar="SSHMNG_DEBUG")
@click.pass_context
def main(ctx, debug):
    ctx.obj = Repo(debug)


@main.command()
@click.pass_obj
def list(repo: Repo):
    hosts = repo.load_hosts()

    # TODO: print host info more pretty (+ colors)
    pprint(hosts)


@main.command()
@click.argument("name")
@click.pass_obj
def add(repo: Repo, name):
    hosts = repo.load_hosts()
    if hosts.get(name):
        replace = input(f"The connection for {name} already exists.\nDo you want to replace? [y/N] ")
        if replace.lower() != "y":
            print("Canceled add host")
            return

    print(f"Saving {name}...")

    # TODO: check input is empty
    username = input("Enter user name: ")
    address = input("Enter server address: ")
    port = int(input("Enter ssh port[22]: ") or 22)

    # TODO: add ssh-copy-id logic
    # TODO: check add pem file instead

    hosts[name] = {"username": username, "host": address, "port": port}
    repo.save_hosts(hosts)

    print(f"Saved {name}")


@main.command()
@click.argument("name")
@click.pass_obj
def connect(repo: Repo, name):
    host = repo.load_hosts().get(name)
    if host is None:
        print(f"connection for '{name}' not exists")
        return sys.exit(1)

    # TODO: check if pem file exists
    subprocess.call(f"ssh -p {host['port']} {host['username']}@{host['host']}", shell=True)


@main.command()
@click.argument("name")
@click.pass_obj
def delete(repo: Repo, name):
    hosts = repo.load_hosts()
    if hosts.get(name) is None:
        print(f"connection for '{name}' not exists")
        return sys.exit(1)

    replace = input(f"connection for '{name}' permenantly deleted. Are you sure? [y/N] ")
    if replace.lower() != "y":
        return

    del hosts[name]
    repo.save_hosts(hosts)
    print(f"Delete '{name}' Complete")


@main.command()
@click.argument("name")
@click.argument("command", nargs=-1)
@click.pass_obj
def exec(repo: Repo, name, command):
    host = repo.load_hosts().get(name)
    if host is None:
        print(f"connection for '{name}' not exists")
        return sys.exit(1)

    subprocess.call(f"ssh -p {host['port']} {host['username']}@{host['host']} '{' '.join(command)}'", shell=True)

if __name__ == "__main__":
    sys.exit(main())  # pragma: no cover
