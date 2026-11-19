"""Exercise tenant boundaries and catalog recall using synthetic client identities."""

import json
import os
import subprocess
import sys
import tempfile
import tomllib
import unittest
from typing import Any
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import patch

SKILL = Path(__file__).resolve().parents[1] / "skills" / "freelancer-self-onboarding"
sys.path.insert(0, str(SKILL / "scripts"))
import catalog  # noqa: E402
import guest  # noqa: E402
import model  # noqa: E402
import workspace  # noqa: E402


def intake(name: str) -> dict[str, Any]:
    """Return a normalized synthetic tenant with both shared and Claude-only tools."""
    address = f"op@{name}.example"
    return model.plan(
        {
            "email": address,
            "client": name,
            "surfaces": [
                {
                    "id": "slack",
                    "principal": address,
                    "target": name,
                    "access": "Read",
                    "method": "bearer",
                    "connector": "Slack",
                },
                {
                    "id": "metamvp",
                    "principal": address,
                    "target": name,
                    "access": "Read",
                    "method": "plugin",
                    "connector": "MetaMVP",
                },
                {
                    "id": "crm",
                    "principal": address,
                    "target": name,
                    "access": "Read",
                    "method": "manual",
                    "connector": "Copper",
                    "harness": "claude",
                },
                {
                    "id": "calendar",
                    "principal": address,
                    "target": name,
                    "access": "Read",
                    "method": "oauth",
                    "harness": "claude",
                    "client_id": "public-app-id",
                    "url": "https://calendar.example/mcp",
                },
            ],
        }
    )


class PortfolioCase(unittest.TestCase):
    """Check filesystem state independently of the container daemon."""

    def setUp(self) -> None:
        """Create a fresh portfolio for each test."""
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.base = Path(temp.name).resolve()

    def make(self, key: str) -> Path:
        """Provision one synthetic tenant through the host entry point."""
        return workspace.initialize(self.base, key, intake(key))


class WorkspaceTests(PortfolioCase):
    """Check the host intake and catalog operations."""

    def test_clients_and_generated_configs(self) -> None:
        """Separate mounts and generate valid harness-specific configuration."""
        left, right = self.make("north"), self.make("south")
        args = workspace.container_args(left, "bridge-a", False)
        self.assertFalse(any(str(right) in arg for arg in args))
        self.assertEqual(args.count("--mount"), 3)
        self.assertIn("--cap-drop=ALL", args)
        self.assertNotIn("-e", args)
        self.assertTrue(all("docker.sock" not in arg for arg in args))
        config = tomllib.loads((left / "private-home/.codex/config.toml").read_text())
        self.assertFalse(config["features"]["apps"])
        self.assertEqual(set(config["mcp_servers"]), {"slack"})
        servers = json.loads((left / "work/.mcp.json").read_text())["mcpServers"]
        self.assertEqual(set(servers), {"slack", "calendar"})
        self.assertEqual(servers["calendar"]["oauth"], {"clientId": "public-app-id"})
        self.assertIn(
            "FREELANCE_SLACK_TOKEN", servers["slack"]["headers"]["Authorization"]
        )
        self.assertNotIn("north.example", str(catalog.inventory(self.base)))

    def test_safe_resume_and_collisions(self) -> None:
        """Retain local changes and reject rebinding, links and occupied targets."""
        root = self.make("north")
        ledger = root / "work/CONNECTIONS.md"
        ledger.write_text("local evidence")
        self.make("north")
        self.assertEqual(ledger.read_text(), "local evidence")
        with self.assertRaises(ValueError):
            workspace.initialize(self.base, "north", intake("south"))
        occupied = self.base / "occupied"
        occupied.mkdir()
        (occupied / "existing").touch()
        with self.assertRaises(OSError):
            self.make("occupied")
        (self.base / "alias").symlink_to(root)
        with self.assertRaises(ValueError):
            self.make("alias")
        with self.assertRaises(ValueError):
            workspace.base_path(root / "work")
        with self.assertRaises(ValueError):
            workspace.container_args(self.base / "alias", "bridge", False)

    def test_catalog_and_guest_changes(self) -> None:
        """Discover new tenant-side connector names without copying settings or URLs."""
        root = self.make("north")
        work, home = root / "work", root / "private-home"
        settings = {"mcpServers": {"Attio": {"url": "https://private.example/tenant"}}}
        (work / ".mcp.json").write_text(json.dumps(settings))
        with patch.object(guest, "WORK", work), patch.object(guest, "HOME_DIR", home):
            guest.sync(intake("north"))
        self.assertIn(("Copper", "both"), catalog.inventory(self.base))
        self.assertIn(("Attio", "claude"), catalog.inventory(self.base, review=True))
        self.assertNotIn("private.example", (work / catalog.RECEIPT).read_text())
        subprocess.run(
            [
                sys.executable,
                str(SKILL / "scripts/workspace.py"),
                "--base",
                str(self.base),
                "remember",
                "Attio",
                "claude",
            ],
            check=True,
        )
        self.assertNotIn(("Attio", "claude"), catalog.inventory(self.base, review=True))
        self.assertIn(("Attio", "claude"), catalog.inventory(self.base))

    def test_receipt_rejects_links_private_fields_and_large_input(self) -> None:
        """Ignore malformed receipts without reading private files through links."""
        root = self.make("north")
        path = root / "work" / catalog.RECEIPT
        path.symlink_to(root / workspace.CONTEXT)
        self.assertEqual(catalog.read_receipt(root), [])
        path.unlink()
        for content in ['[{"name":"CRM","harness":"both","url":"secret"}]', "x" * 8200]:
            path.write_text(content)
            self.assertEqual(catalog.read_receipt(root), [])
        with self.assertRaises(ValueError):
            catalog.entry("op@private.example", "both")

    def test_concurrent_initialization(self) -> None:
        """Serialize retries against the same workspace."""
        with ThreadPoolExecutor(max_workers=3) as pool:
            roots = list(pool.map(self.make, ["north"] * 3))
        self.assertEqual(len(set(roots)), 1)
        self.assertEqual(catalog.inventory(self.base).count(("Copper", "both")), 1)

    def test_untrusted_intake(self) -> None:
        """Reject path traversal, credential-bearing URLs and unexpected fields."""
        for key in ("../other", "ab/cd", "UPPER", ""):
            with self.assertRaises(ValueError):
                model.slug(key)
        for url in (
            "http://vendor.example",
            "https://user:pass@vendor.example/mcp",
            "https://vendor.example/mcp?token=secret",
        ):
            with self.assertRaises(ValueError):
                model.endpoint(url)
        spec = intake("north")["surfaces"][1] | {"harness": "both"}
        with self.assertRaises(ValueError):
            model.surface(spec)
        with self.assertRaises(ValueError):
            model.plan(intake("north") | {"password": "fake"})


@unittest.skipUnless(
    os.environ.get("TEST_DOCKER") == "1", "requires the built Docker image"
)
class ContainerTests(PortfolioCase):
    """Run container acceptance checks on a local Docker Engine."""

    def test_live_mounts_harnesses_and_persistence(self) -> None:
        """Launch both clients, prove credentials stay separate and load both CLIs."""
        left, right = self.make("north"), self.make("south")
        for root in (left, right):
            network = workspace.ensure_network(root)
            self.addCleanup(
                subprocess.run,
                ["docker", "network", "rm", network],
                stdout=subprocess.DEVNULL,
                check=False,
            )

        def run(client: str, *args: str) -> str:
            """Invoke the real host launcher and return the guest's standard output."""
            return subprocess.check_output(
                [
                    sys.executable,
                    str(SKILL / "scripts/workspace.py"),
                    "--base",
                    str(self.base),
                    "run",
                    client,
                    *args,
                ],
                text=True,
                env=os.environ | {"FREELANCE_HOST_SENTINEL": "host-only"},
            )

        run(
            "north",
            "sh",
            "-ec",
            "echo north > ~/private-marker; echo north > /work/data",
        )
        run(
            "south",
            "sh",
            "-ec",
            "test ! -e ~/private-marker && test ! -e /work/data && "
            'test ! -e /var/run/docker.sock && test -z "$FREELANCE_HOST_SENTINEL" && '
            'test "$ENABLE_CLAUDEAI_MCP_SERVERS" = false && '
            'test "$(id -u)" != 0 && test ! -w /client/CLIENT_CONTEXT.json && '
            "test -r /work/.claude/skills/freelancer-self-onboarding/SKILL.md",
        )
        self.assertEqual(
            run("north", "sh", "-c", "cat ~/private-marker /work/data").split(),
            ["north", "north"],
        )
        self.assertIn("codex", run("north", "codex", "--version").lower())
        self.assertIn("claude", run("south", "claude", "--version").lower())


if __name__ == "__main__":
    unittest.main()
