"""Synthetic connector identity gate used by the isolated GEM pilot.

The binding is non-secret identity metadata. Client sources remain unread until
principal, tenant, target, workspace ID, and intended root all match.
"""

from __future__ import annotations

import json
import os
import stat
import subprocess
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any


class GuardDenied(RuntimeError):
    """A stable fail-closed denial raised before client source access."""


@dataclass(frozen=True)
class VerifiedBinding:
    root: Path
    workspace_id: str
    sources: tuple[str, ...]


def _regular_bytes(root: Path, relative: str, maximum: int) -> bytes:
    parts = PurePosixPath(relative).parts
    if not parts or PurePosixPath(relative).is_absolute() or ".." in parts:
        raise GuardDenied("unsafe relative path")
    candidate = root.joinpath(*parts)
    descriptor = -1
    try:
        resolved = candidate.resolve(strict=True)
        resolved.relative_to(root)
        flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
        descriptor = os.open(candidate, flags)
        info = os.fstat(descriptor)
        if not stat.S_ISREG(info.st_mode) or info.st_size > maximum:
            raise GuardDenied("unsafe or oversized file")
        data = os.read(descriptor, maximum + 1)
        if len(data) > maximum:
            raise GuardDenied("oversized file")
        return data
    except GuardDenied:
        raise
    except (OSError, ValueError) as exc:
        raise GuardDenied(f"unreadable file: {exc}") from exc
    finally:
        if descriptor >= 0:
            os.close(descriptor)


def verify(
    root: Path,
    intended_root: Path,
    expected_workspace_id: str,
    attestation: dict[str, Any],
) -> VerifiedBinding:
    """Verify synthetic connector scope without reading client source files."""
    try:
        actual = root.resolve(strict=True)
        intended = intended_root.resolve(strict=True)
    except OSError as exc:
        raise GuardDenied(f"workspace root unavailable: {exc}") from exc
    if root.is_symlink() or intended_root.is_symlink() or actual != intended:
        raise GuardDenied("wrong workspace root")
    if not isinstance(attestation, dict):
        raise GuardDenied("connector attestation must be an object")
    try:
        binding = json.loads(_regular_bytes(actual, "binding.json", 16 * 1024))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise GuardDenied(f"invalid binding: {exc}") from exc
    if (
        not isinstance(binding, dict)
        or binding.get("workspace_id") != expected_workspace_id
    ):
        raise GuardDenied("wrong workspace identity")
    for field in ("principal", "tenant", "target"):
        expected = binding.get(field)
        observed = attestation.get(field)
        if (
            not isinstance(expected, str)
            or not expected.strip()
            or observed != expected
        ):
            raise GuardDenied(f"connector {field} mismatch")
    sources = binding.get("authorized_sources")
    if (
        not isinstance(sources, list)
        or not sources
        or not all(isinstance(item, str) for item in sources)
    ):
        raise GuardDenied("invalid authorized source inventory")
    try:
        workspace = json.loads(_regular_bytes(actual, ".gem/workspace.json", 64 * 1024))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise GuardDenied(f"invalid GEM workspace inventory: {exc}") from exc
    enrolled = workspace.get("sources") if isinstance(workspace, dict) else None
    gem_workspace_id = (
        workspace.get("workspace_id") if isinstance(workspace, dict) else None
    )
    if (
        gem_workspace_id != expected_workspace_id
        or not isinstance(enrolled, list)
        or not all(isinstance(item, str) for item in enrolled)
        or sorted(enrolled) != sorted(sources)
    ):
        raise GuardDenied("GEM source inventory exceeds or differs from client binding")
    return VerifiedBinding(actual, expected_workspace_id, tuple(sources))


def read_verified_sources(
    binding: VerifiedBinding,
    reader: Callable[[Path, str], str] | None = None,
) -> dict[str, str]:
    """Read only sources authorized by a previously verified binding."""
    if reader is None:
        reader = lambda root, relative: _regular_bytes(
            root, relative, 64 * 1024
        ).decode("utf-8")
    return {relative: reader(binding.root, relative) for relative in binding.sources}


def guarded_handoff(
    root: Path,
    intended_root: Path,
    expected_workspace_id: str,
    attestation: dict[str, Any],
    operation: str,
    key: str,
    request: Path | None = None,
    next_step: str | None = None,
    executable: str = "graph-engineering-magic",
) -> dict[str, Any]:
    """Re-verify identity, then invoke the installed GEM CLI."""
    verify(root, intended_root, expected_workspace_id, attestation)
    if operation not in {"save", "resume"}:
        raise GuardDenied("unsupported handoff operation")
    command = [
        executable,
        "--workspace",
        str(root),
        "--workspace-id",
        expected_workspace_id,
        "handoff",
        operation,
        "--key",
        key,
    ]
    if operation == "save":
        if request is None or next_step is None:
            raise GuardDenied("save requires request and next_step")
        command.extend(["--request", str(request), "--next-step", next_step])
    completed = subprocess.run(
        command,
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode:
        raise GuardDenied(f"GEM refused the handoff (exit {completed.returncode})")
    try:
        result = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise GuardDenied("GEM returned invalid JSON") from exc
    if not isinstance(result, dict):
        raise GuardDenied("GEM returned a non-object result")
    return result
