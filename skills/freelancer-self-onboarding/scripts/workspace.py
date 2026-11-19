"""Create a client workspace, recall connector choices, and launch an isolated CLI."""

import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

from catalog import database, inventory, remember
from model import configurations, plan, slug

IMAGE = "freelancer-self-onboarding:1"
SKILL = Path(__file__).resolve().parents[1]
CONTEXT = "CLIENT_CONTEXT.json"
GUEST_SKILL = "/opt/freelancer-self-onboarding"
INSTRUCTIONS = """Read /client/CLIENT_CONTEXT.json before using a connection.
Verify the active principal, tenant and requested access for this client.
Record checks and pending steps in /work/CONNECTIONS.md.
Keep credentials in the private runtime home. Use this client's tools only.
"""


def base_path(path: Path) -> Path:
    """Resolve an operator-controlled portfolio outside client workspaces."""
    base = path.expanduser().absolute()
    if base != base.resolve() or any(
        (p / CONTEXT).exists() for p in [base, *base.parents]
    ):
        raise ValueError(
            "Choose a real portfolio directory outside any client workspace."
        )
    if base == Path.home() or base == Path("/") or base.is_relative_to(SKILL):
        raise ValueError("Choose a dedicated portfolio directory.")
    base.mkdir(mode=0o700, parents=True, exist_ok=True)
    if base.stat().st_uid != os.getuid() or base.stat().st_mode & 0o022:
        raise ValueError(
            "The portfolio must be owned by you and protected from other writers."
        )
    return base


def populate(stage: Path, spec: dict[str, Any]) -> None:
    """Write a complete workspace before exposing it at its final location."""
    home = stage / "private-home"
    work = stage / "work"
    for path in [home / ".codex", home / ".claude", home / ".tokens", work]:
        path.mkdir(mode=0o700, parents=True, exist_ok=True)
    (stage / CONTEXT).write_text(json.dumps(spec, indent=2) + "\n")
    (stage / ".gitignore").write_text("*\n")
    codex, claude = configurations(spec)
    (home / ".codex" / "config.toml").write_text(codex)
    (work / ".mcp.json").write_text(claude)
    (work / "AGENTS.md").write_text(INSTRUCTIONS)
    (work / "CLAUDE.md").write_text(INSTRUCTIONS)
    (work / ".gitignore").write_text(
        "/.mcp.json\n/.connector-names.json\n/CONNECTIONS.md\n/.claude/\n/.agents/\n"
    )
    for harness in [".agents", ".claude"]:
        skills = work / harness / "skills"
        skills.mkdir(parents=True)
        (skills / "freelancer-self-onboarding").symlink_to(GUEST_SKILL)
    rows = ["# Connections", "", "Check each selected harness separately.", ""]
    next_step = {
        "oauth": "Registered. Complete client OAuth consent, then verify identity and target.",
        "bearer": "Registered. Enter a client-scoped token privately, then verify identity and target.",
        "plugin": "Pending. Identify and install the approved plugin, then verify the account and target.",
        "manual": "Pending. Confirm the client-approved access route and verify the account and target.",
    }
    for item in spec["surfaces"]:
        harnesses = (
            ["codex", "claude"] if item["harness"] == "both" else [item["harness"]]
        )
        rows.extend(
            f"- {item['id']} ({h}) — {next_step[item['method']]}" for h in harnesses
        )
    (work / "CONNECTIONS.md").write_text("\n".join(rows) + "\n")


def initialize(base: Path, key: str, spec: dict[str, Any]) -> Path:
    """Create or resume one workspace and remember explicitly portable labels."""
    root = base / slug(key)
    with database(base) as db:
        if root.is_symlink() or (root / CONTEXT).is_symlink():
            raise ValueError("Workspace and context must be real paths.")
        if (root / CONTEXT).exists():
            registered = db.execute(
                "SELECT 1 FROM roots WHERE slug = ?", (key,)
            ).fetchone()
            if not registered or json.loads((root / CONTEXT).read_text()) != spec:
                raise ValueError("This workspace is already bound to another intake.")
        else:
            with tempfile.TemporaryDirectory(dir=base, prefix=".setup-") as temp:
                stage = Path(temp) / "new"
                stage.mkdir(mode=0o700)
                populate(stage, spec)
                # rename may replace an empty directory. A nonempty target survives.
                stage.rename(root)
        db.execute("INSERT OR IGNORE INTO roots VALUES (?)", (key,))
        for item in spec["surfaces"]:
            if "connector" in item:
                remember(db, item["connector"], item["connector_harness"])
    return root


def container_args(root: Path, network: str, interactive: bool) -> list[str]:
    """Build a fixed mount set without forwarding host environment or sockets."""
    mounts = {
        root / "work": "/work",
        root / "private-home": "/home/operator",
        root / CONTEXT: "/client/CLIENT_CONTEXT.json",
    }
    args = [
        "docker",
        "run",
        "--rm",
        "--init",
        "-i",
        "--read-only",
        "--cap-drop=ALL",
        "--security-opt=no-new-privileges",
        "--pids-limit=512",
        "--network",
        network,
        "--user",
        f"{os.getuid()}:{os.getgid()}",
        "--tmpfs",
        "/tmp:rw,nosuid,nodev,mode=1777",
    ]
    if interactive:
        args.append("-t")
    for source, target in mounts.items():
        if not source.exists() or source.resolve() != source or "," in str(source):
            raise ValueError("Invalid client mount path.")
        rule = f"type=bind,source={source},target={target},bind-recursive=disabled"
        if source.name == CONTEXT:
            rule = f"type=bind,source={source},target={target},readonly"
        args.extend(["--mount", rule])
    return [*args, "--workdir", "/work", IMAGE]


def checked_docker_host() -> None:
    """Require a local Unix Docker socket so bind mounts refer to this host."""
    if os.getuid() == 0:
        raise ValueError("Launch as the non-root freelancer account.")
    context = subprocess.check_output(
        ["docker", "context", "inspect", "--format", "{{.Endpoints.docker.Host}}"],
        text=True,
    ).strip()
    if not all(
        v.startswith("unix://") for v in (context, os.getenv("DOCKER_HOST", context))
    ):
        raise ValueError("Select a local Docker context backed by a Unix socket.")


def ensure_network(root: Path) -> str:
    """Create the per-client bridge and check its ownership before joining it."""
    digest = hashlib.sha256(os.fsencode(root)).hexdigest()
    name = "freelance-" + digest[:24]
    label = "freelancer.self-onboarding"
    inspect = [
        "docker",
        "network",
        "inspect",
        "--format",
        '{{.Driver}} {{index .Labels "' + label + '"}}',
        name,
    ]
    result = subprocess.run(inspect, capture_output=True, text=True)
    if result.returncode:
        subprocess.run(
            [
                "docker",
                "network",
                "create",
                "--driver",
                "bridge",
                "--label",
                f"{label}={digest}",
                name,
            ],
            capture_output=True,
        )
        result = subprocess.run(inspect, capture_output=True, text=True)
    if result.returncode or result.stdout.strip() != f"bridge {digest}":
        raise ValueError("Could not verify this client's dedicated Docker network.")
    return name


def launch(base: Path, key: str, command: list[str]) -> int:
    """Start a fresh container against only the selected client's persistent files."""
    root = base / slug(key)
    with database(base) as db:
        if not db.execute("SELECT 1 FROM roots WHERE slug = ?", (key,)).fetchone():
            raise ValueError("Initialize this workspace before launching it.")
    if not command or command[0] not in {
        "codex",
        "claude",
        "sh",
        "token",
        "suggest",
        "sync",
    }:
        raise ValueError("Choose codex, claude, sh, token, suggest or sync.")
    checked_docker_host()
    network = ensure_network(root)
    args = container_args(root, network, sys.stdin.isatty() and sys.stdout.isatty())
    if command[0] in {"codex", "claude", "sh"}:
        command = ["exec", *command]
    return subprocess.run([*args, *command], check=False).returncode


def main() -> int:
    """Run the requested operation on a named portfolio."""
    os.umask(0o077)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", type=Path, required=True)
    sub = parser.add_subparsers(dest="action", required=True)
    init = sub.add_parser("init", help="Read a non-secret JSON intake from stdin.")
    init.add_argument("client_slug")
    sub.add_parser(
        "catalog", help="Show reusable connector names with harness affinity."
    )
    sub.add_parser(
        "review", help="Find new names in registered clients' export receipts."
    )
    recall_parser = sub.add_parser(
        "remember", help="Promote one portable connector name."
    )
    recall_parser.add_argument("name")
    recall_parser.add_argument("harness", choices=["both", "claude", "codex"])
    run = sub.add_parser("run")
    run.add_argument("client_slug")
    run.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    base = base_path(args.base)
    if args.action == "init":
        print(initialize(base, args.client_slug, plan(json.load(sys.stdin))))
    elif args.action == "remember":
        with database(base) as db:
            remember(db, args.name, args.harness)
    elif args.action == "run":
        return launch(base, args.client_slug, args.command)
    else:
        print(json.dumps(inventory(base, review=args.action == "review"), indent=2))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, ValueError, TypeError, subprocess.CalledProcessError) as exc:
        sys.exit(str(exc))
