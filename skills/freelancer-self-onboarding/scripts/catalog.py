"""Keep a host-owned index of portable connector names, separate from client state."""

import json
import os
import re
import sqlite3
import stat
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

HARNESSES = {"both", "codex", "claude"}
BUILTINS = [("Slack", "both"), ("Google Workspace", "both"), ("MetaMVP", "claude")]
NAME = re.compile(r"[A-Za-z][A-Za-z0-9 _+().-]{0,63}\Z")
RECEIPT = ".connector-names.json"


def entry(name: str, harness: str) -> tuple[str, str]:
    """Accept only a portable product label and its supported harness."""
    if (
        not isinstance(name, str)
        or not NAME.fullmatch(name)
        or harness not in HARNESSES
    ):
        raise ValueError("Use a connector display name and both, codex or claude.")
    return name.strip(), harness


@contextmanager
def database(base: Path) -> Iterator[sqlite3.Connection]:
    """Open the local control-plane index and commit one catalog operation."""
    path = base / ".freelancer-catalog.sqlite3"
    if path.is_symlink() or (path.exists() and not path.is_file()):
        raise ValueError("Invalid catalog path.")
    db = sqlite3.connect(path, timeout=15)
    try:
        with db:
            db.execute("CREATE TABLE IF NOT EXISTS roots (slug TEXT PRIMARY KEY)")
            db.execute(
                "CREATE TABLE IF NOT EXISTS tools (name TEXT COLLATE NOCASE, "
                "harness TEXT, PRIMARY KEY (name, harness))"
            )
            db.executemany("INSERT OR IGNORE INTO tools VALUES (?, ?)", BUILTINS)
            yield db
    finally:
        db.close()


def read_receipt(root: Path) -> list[tuple[str, str]]:
    """Read one bounded file without following links in a client-writable tree."""
    if root.is_symlink() or (root / "work").is_symlink():
        return []
    flags = os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK
    try:
        with os.fdopen(os.open(root / "work" / RECEIPT, flags), "rb") as stream:
            info = os.fstat(stream.fileno())
            if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
                return []
            data = stream.read(8193)
        if len(data) > 8192:
            return []
        items = json.loads(data)
        if not isinstance(items, list) or len(items) > 64:
            return []
        return [
            entry(item["name"], item["harness"])
            for item in items
            if isinstance(item, dict) and set(item) == {"name", "harness"}
        ]
    except (OSError, ValueError, TypeError, KeyError):
        return []


def remember(db: sqlite3.Connection, name: str, harness: str) -> None:
    """Merge overlapping harness choices into one portable suggestion."""
    name, harness = entry(name, harness)
    old = {
        v for (v,) in db.execute("SELECT harness FROM tools WHERE name = ?", (name,))
    }
    choices = old | {harness}
    combined = "both" if "both" in choices or len(choices) > 1 else harness
    if name.casefold() == "metamvp":
        combined = "claude"
    db.execute("DELETE FROM tools WHERE name = ?", (name,))
    db.execute("INSERT INTO tools VALUES (?, ?)", (name, combined))


def inventory(base: Path, review: bool = False) -> list[tuple[str, str]]:
    """List remembered names or unreviewed suggestions from registered workspaces."""
    with database(base) as db:
        known = sorted(db.execute("SELECT name, harness FROM tools"), key=str)
        if not review:
            return known
        suggested: set[tuple[str, str]] = set()
        for (client,) in db.execute("SELECT slug FROM roots"):
            suggested.update(read_receipt(base / client))
    seen = {(name.casefold(), harness) for name, harness in known}
    return sorted(
        item
        for item in suggested
        if (item[0].casefold(), item[1]) not in seen
        and (item[0].casefold(), "both") not in seen
    )
