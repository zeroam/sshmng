"""Console script for sshmng."""
import os
import sys
import click
import subprocess
import tempfile
from pathlib import Path
from pprint import pprint

from sshmng.repo import Repo


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
    for name, host in hosts.items():
        print(f"- {name}: {host['username']}@{host['host']}:{host['port']}")


@main.command()
@click.argument("name")
@click.pass_obj
def add(repo: Repo, name):
    hosts = repo.load_hosts()
    if hosts.get(name):
        replace = input(
            f"The connection for {name} already exists.\nDo you want to replace? [y/N] "
        )
        if replace.lower() != "y":
            print("Canceled add host")
            return

    print(f"Saving {name}...")

    # TODO: check input is empty
    username = input("Enter user name: ")
    address = input("Enter server address: ")
    port = int(input("Enter ssh port[22]: ") or 22)
    private_key_path = input(f"Enter private key path[{repo.private_key}]: ")
    if not private_key_path:
        private_key = repo.private_key.read_text()

        # add ssh-copy-id logic
        subprocess.call(
            f'cat {repo.public_key} | ssh -p {port} {username}@{address} "mkdir -p ~/.ssh && chmod 700 ~/.ssh && cat >> ~/.ssh/authorized_keys"',
            shell=True,
        )
    else:
        # check add pem file instead
        private_key = Path(private_key_path).read_text()

    hosts[name] = {
        "username": username,
        "host": address,
        "port": port,
        "private_key": private_key,
    }
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
    with tempfile.NamedTemporaryFile("w") as fp:
        fp.write(host["private_key"])
        fp.flush()

        temppath = os.path.join(tempfile.gettempdir(), fp.name)
        print(temppath)
        subprocess.call(
            f"ssh -i {temppath} -p {host['port']} {host['username']}@{host['host']}",
            shell=True,
        )


@main.command()
@click.argument("name")
@click.pass_obj
def delete(repo: Repo, name):
    hosts = repo.load_hosts()
    if hosts.get(name) is None:
        print(f"connection for '{name}' not exists")
        return sys.exit(1)

    replace = input(
        f"connection for '{name}' permenantly deleted. Are you sure? [y/N] "
    )
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

    with tempfile.NamedTemporaryFile("w") as fp:
        fp.write(host["private_key"])
        fp.flush()

        temppath = os.path.join(tempfile.gettempdir(), fp.name)
        print(temppath)

        subprocess.call(
            f"ssh -i {temppath} -p {host['port']} {host['username']}@{host['host']} '{' '.join(command)}'",
            shell=True,
        )


if __name__ == "__main__":
    sys.exit(main())  # pragma: no cover
