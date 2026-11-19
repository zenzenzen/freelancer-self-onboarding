"""Handle credentials and connector suggestions inside a single client container."""

import argparse
import fcntl
import getpass
import json
import os
import subprocess
import tomllib
import sys
import tempfile
from pathlib import Path
from typing import Any

from catalog import RECEIPT, entry, read_receipt
from model import env_name, slug

WORK = Path("/work")
CONTEXT = Path("/client/CLIENT_CONTEXT.json")
HOME_DIR = Path("/home/operator")


def write_private(path: Path, data: str) -> None:
    """Replace one file atomically with private permissions."""
    with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as temp:
        name = temp.name
        temp.write(data.encode())
    try:
        os.replace(name, path)
    finally:
        Path(name).unlink(missing_ok=True)


def suggest(name: str, harness: str) -> None:
    """Offer only a connector name to the freelancer's host-side catalog."""
    addition = entry(name, harness)
    with (HOME_DIR / ".connector-lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        # read_receipt expects a parent with a work/ child. Inside the guest it is /.
        items = sorted(set(read_receipt(WORK.parent)) | {addition})
        if len(items) > 64:
            raise ValueError("This workspace already has 64 suggestions.")
        data = [{"name": n, "harness": h} for n, h in items]
        write_private(WORK / RECEIPT, json.dumps(data, indent=2) + "\n")


def sync(spec: dict[str, Any]) -> None:
    """Export product labels from MCP and plugin configuration after a session."""
    names = {s["id"]: s.get("connector", s["id"]) for s in spec["surfaces"]}
    files = [
        (WORK / ".mcp.json", "claude"),
        (HOME_DIR / ".claude" / ".claude.json", "claude"),
        (HOME_DIR / ".claude.json", "claude"),
        (HOME_DIR / ".claude" / "settings.json", "claude"),
        (WORK / ".claude" / "settings.local.json", "claude"),
        (HOME_DIR / ".codex" / "config.toml", "codex"),
    ]
    additions = set()
    for path, harness in files:
        if not path.is_file() or path.is_symlink() or path.stat().st_size > 2**21:
            continue
        try:
            raw = path.read_text()
            data = tomllib.loads(raw) if path.suffix == ".toml" else json.loads(raw)
            project = data.get("projects", {}).get("/work", {})
            ids = set(data.get("mcp_servers", {})) | set(data.get("mcpServers", {}))
            ids.update(project.get("mcpServers", {}))
            plugins = (
                data.get("plugins", {})
                if harness == "codex"
                else data.get("enabledPlugins", {})
            )
            ids.update(k.split("@")[0] for k, v in plugins.items() if v)
            for key in ids:
                try:
                    additions.add(entry(names.get(key, key), harness))
                except ValueError:
                    continue
        except (AttributeError, OSError, TypeError, ValueError):
            continue
    for name, harness in sorted(additions):
        suggest(name, harness)


def token_store(provider: str, allowed: set[str]) -> None:
    """Take a selected provider's token at a private terminal prompt."""
    if provider not in allowed or not sys.stdin.isatty():
        raise ValueError("Use a terminal and select a configured bearer provider.")
    token = getpass.getpass("Client access token (hidden): ")
    if not token.strip() or not token.isprintable():
        raise ValueError("Expected a nonempty, single-line token.")
    write_private(HOME_DIR / ".tokens" / slug(provider), token)


def main() -> None:
    """Dispatch private setup commands or start the selected CLI inside the guest."""
    os.umask(0o077)
    spec = json.loads(CONTEXT.read_text())
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="action", required=True)
    sub.add_parser("sync")
    token = sub.add_parser("token")
    token.add_argument("provider")
    learn = sub.add_parser("suggest")
    learn.add_argument("name")
    learn.add_argument("harness", choices=["codex", "claude", "both"])
    run = sub.add_parser("exec")
    run.add_argument("program")
    run.add_argument("args", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    bearers = {
        item["id"]
        for item in spec["surfaces"]
        if item["method"] == "bearer"
        and item.get("harness", "both") in {"both", getattr(args, "program", "")}
    }
    if args.action == "sync":
        sync(spec)
        return
    if args.action == "token":
        selected = {
            item["id"] for item in spec["surfaces"] if item["method"] == "bearer"
        }
        token_store(args.provider, selected)
        return
    if args.action == "suggest":
        suggest(args.name, args.harness)
        return
    for name in bearers:
        path = HOME_DIR / ".tokens" / name
        if path.is_file():
            os.environ[env_name(name)] = path.read_text()
    try:
        result = subprocess.run([args.program, *args.args], check=False)
    finally:
        sync(spec)
    sys.exit(result.returncode)


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError) as exc:
        sys.exit(str(exc))
