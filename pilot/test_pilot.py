from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from pilot.guard import GuardDenied, guarded_handoff, read_verified_sources, verify

ROOT = Path(__file__).parents[1]
CLIENT_A = ROOT / "fixtures/client-a"
CLIENT_B = ROOT / "fixtures/client-b"
GEM = shutil.which("graph-engineering-magic")

ATTESTATION_A = {
    "principal": "worker-a@example.invalid",
    "tenant": "tenant-a",
    "target": "drive-a",
}
ATTESTATION_B = {
    "principal": "worker-b@example.invalid",
    "tenant": "tenant-b",
    "target": "drive-b",
}


def _copy_client(source: Path, destination: Path) -> Path:
    def ignore(path: str, names: list[str]) -> set[str]:
        return {".local"} if Path(path).name == ".gem" and ".local" in names else set()

    shutil.copytree(source, destination, ignore=ignore)
    return destination


@pytest.fixture
def clients(tmp_path: Path) -> tuple[Path, Path]:
    return (
        _copy_client(CLIENT_A, tmp_path / "client-a"),
        _copy_client(CLIENT_B, tmp_path / "client-b"),
    )


@pytest.mark.parametrize(
    "case",
    [
        "wrong-root",
        "wrong-workspace",
        "wrong-principal",
        "wrong-tenant",
        "wrong-target",
    ],
)
def test_denial_causes_zero_client_source_reads(
    clients: tuple[Path, Path], case: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    client_a, client_b = clients
    root = client_a
    intended = client_a
    workspace = "client-a"
    attestation = dict(ATTESTATION_A)
    if case == "wrong-root":
        intended = client_b
    elif case == "wrong-workspace":
        workspace = "client-b"
    elif case == "wrong-principal":
        attestation["principal"] = "worker-b@example.invalid"
    elif case == "wrong-tenant":
        attestation["tenant"] = "tenant-b"
    else:
        attestation["target"] = "drive-b"

    from pilot import guard

    reads: list[str] = []
    read_file = guard._regular_bytes

    def observed_read(base: Path, relative: str, maximum: int) -> bytes:
        reads.append(relative)
        return read_file(base, relative, maximum)

    def unexpected_launch(*args, **kwargs):
        pytest.fail("identity mismatch reached GEM")

    monkeypatch.setattr(guard, "_regular_bytes", observed_read)
    monkeypatch.setattr(subprocess, "run", unexpected_launch)
    with pytest.raises(GuardDenied):
        guarded_handoff(root, intended, workspace, attestation, "resume", "switch")

    assert set(reads) <= {"binding.json", ".gem/workspace.json"}


def test_guard_refuses_gem_inventory_broader_than_binding(
    clients: tuple[Path, Path],
) -> None:
    client_a, _ = clients
    workspace_path = client_a / ".gem/workspace.json"
    workspace = json.loads(workspace_path.read_text())
    workspace["sources"].append("unbound.md")
    workspace_path.write_text(json.dumps(workspace), encoding="utf-8")

    with pytest.raises(GuardDenied, match="source inventory"):
        verify(client_a, client_a, "client-a", ATTESTATION_A)


def test_switch_a_to_b_reads_only_b_authorized_sources(
    clients: tuple[Path, Path],
) -> None:
    client_a, client_b = clients
    reads: list[tuple[Path, str]] = []

    def observed_reader(root: Path, relative: str) -> str:
        reads.append((root, relative))
        return (root / relative).read_text(encoding="utf-8")

    sources_a = read_verified_sources(
        verify(client_a, client_a, "client-a", ATTESTATION_A), observed_reader
    )
    reads.clear()
    sources_b = read_verified_sources(
        verify(client_b, client_b, "client-b", ATTESTATION_B), observed_reader
    )

    assert "ALPHA-ONLY" in sources_a["brief.md"]
    assert "BRAVO-ONLY" in sources_b["brief.md"]
    assert "ALPHA-ONLY" not in "\n".join(sources_b.values())
    assert reads and all(root == client_b.resolve() for root, _ in reads)
    assert {relative for _, relative in reads} == {"policy.md", "task.md", "brief.md"}


def test_same_key_resumes_the_intended_client_in_a_fresh_process(
    clients: tuple[Path, Path],
) -> None:
    client_a, client_b = clients
    cases = [
        (
            client_a,
            "client-a",
            ATTESTATION_A,
            "Review the synthetic ALPHA status note.",
        ),
        (
            client_b,
            "client-b",
            ATTESTATION_B,
            "Review the synthetic BRAVO status note.",
        ),
    ]
    for root, workspace, identity, note in cases:
        saved = guarded_handoff(
            root,
            root,
            workspace,
            identity,
            "save",
            "switch",
            ROOT / "pilot/requests" / f"{workspace}.json",
            note,
        )
        assert saved["status"] == "saved"

    for root, workspace, identity, note in reversed(cases):
        command = [
            sys.executable,
            "-m",
            "pilot.demo",
            "resume",
            "--workspace",
            str(root),
            "--intended-root",
            str(root),
            "--workspace-id",
            workspace,
            "--principal",
            identity["principal"],
            "--tenant",
            identity["tenant"],
            "--target",
            identity["target"],
            "--key",
            "switch",
        ]
        response = subprocess.run(
            command, cwd=ROOT, capture_output=True, check=True, text=True
        )
        result = json.loads(response.stdout)
        assert result["status"] == "ready"
        assert result["workspace_id"] == workspace
        assert result["next_step"] == note
        assert {item["path"] for item in result["selected"]} == {
            "policy.md",
            "task.md",
            "brief.md",
        }
        assert result["actions_replayed"] is False
        assert result["claims_completed_work"] is False


@pytest.mark.parametrize(
    "client,workspace,request_name",
    [(CLIENT_A, "client-a", "client-a.json"), (CLIENT_B, "client-b", "client-b.json")],
)
def test_installed_cli_validates_and_compiles_each_workspace(
    client: Path, workspace: str, request_name: str
) -> None:
    assert GEM, "install graph-engineering-magic on PATH"
    validated = subprocess.run(
        [GEM, "--workspace", str(client), "--workspace-id", workspace, "validate"],
        check=True,
        capture_output=True,
        text=True,
    )
    compiled = subprocess.run(
        [
            GEM,
            "--workspace",
            str(client),
            "--workspace-id",
            workspace,
            "context",
            "compile",
            "--request",
            str(ROOT / "pilot/requests" / request_name),
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    assert json.loads(validated.stdout)["status"] == "valid"
    result = json.loads(compiled.stdout)
    assert result["status"] == "ready"
    assert {item["path"] for item in result["selected"]} == {
        "policy.md",
        "task.md",
        "brief.md",
    }
