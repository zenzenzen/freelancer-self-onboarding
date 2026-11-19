"""Validate the client plan and render each harness's connection settings."""

import json
import re
from typing import Any
from urllib.parse import urlsplit

from catalog import HARNESSES, entry

SLUG = re.compile(r"[a-z][a-z0-9]*(?:-[a-z0-9]+)*\Z")
EMAIL = re.compile(r"[^\s@<>]+@[^\s@<>]+\.[^\s@<>]+\Z")
GOOGLE = {
    "google-drive": "https://drivemcp.googleapis.com/mcp/v1",
    "google-calendar": "https://calendarmcp.googleapis.com/mcp/v1",
    "gmail": "https://gmailmcp.googleapis.com/mcp/v1",
}
ENDPOINTS = {"slack": "https://mcp.slack.com/mcp", **GOOGLE}
METHODS = {"oauth", "bearer", "plugin", "manual"}


def slug(value: str) -> str:
    """Return a bounded filesystem-safe tool or workspace identifier."""
    if not isinstance(value, str) or len(value) > 60 or not SLUG.fullmatch(value):
        raise ValueError("Use a lowercase identifier with letters, digits and hyphens.")
    return value


def label(value: Any) -> str:
    """Accept a short, single-line non-secret description."""
    if not isinstance(value, str) or not 0 < len(value.strip()) <= 240:
        raise ValueError("Expected a short nonempty label.")
    if not value.isprintable():
        raise ValueError("Labels must be printable single lines.")
    return value.strip()


def endpoint(value: str) -> str:
    """Accept an HTTPS endpoint without embedded credentials or query parameters."""
    url = urlsplit(label(value))
    if (
        url.scheme != "https"
        or not url.hostname
        or any(
            (
                url.username is not None,
                url.password is not None,
                url.query,
                url.fragment,
            )
        )
    ):
        raise ValueError(
            "Use an HTTPS endpoint without credentials, query or fragment."
        )
    return value


def plan(raw: dict[str, Any]) -> dict[str, Any]:
    """Normalize the intake document and reject unknown or secret-bearing fields."""
    if set(raw) != {"client", "email", "surfaces"}:
        raise ValueError("Expected exactly client, email and surfaces.")
    email = label(raw["email"])
    if not EMAIL.fullmatch(email):
        raise ValueError("Supply a work email address.")
    items = raw["surfaces"]
    if not isinstance(items, list) or len(items) > 64:
        raise ValueError("Use a list of up to 64 work surfaces.")
    surfaces = [surface(item) for item in items]
    if len({item["id"] for item in surfaces}) != len(surfaces):
        raise ValueError("Surface IDs must be unique within this workspace.")
    return {"client": label(raw["client"]), "email": email, "surfaces": surfaces}


def surface(item: dict[str, Any]) -> dict[str, Any]:
    """Check one explicit provider, expected principal, resource and access grant."""
    required = {"id", "principal", "target", "access", "method"}
    http = {"url", "client_id", "scopes"}
    optional = http | {"harness", "connector", "connector_harness"}
    if not isinstance(item, dict) or not required <= item.keys() <= required | optional:
        raise ValueError("Surface fields must match the intake schema.")
    result = {key: label(item[key]) for key in required}
    name = slug(result["id"])
    harness = item.get("harness", "claude" if name == "metamvp" else "both")
    if harness not in HARNESSES or (name == "metamvp" and harness != "claude"):
        raise ValueError("Select a supported harness. MetaMVP is Claude-only.")
    result["harness"] = harness
    if "connector" in item:
        affinity = (
            harness if name == "metamvp" or result["method"] == "plugin" else "both"
        )
        affinity = item.get("connector_harness", affinity)
        if name == "metamvp" and affinity != "claude":
            raise ValueError("MetaMVP is a Claude connector.")
        result["connector"], result["connector_harness"] = entry(
            item["connector"], affinity
        )
    elif "connector_harness" in item:
        raise ValueError("Supply a connector display name with connector_harness.")
    method = result["method"]
    if method not in METHODS:
        raise ValueError("Unknown connection method.")
    if method in {"manual", "plugin"}:
        if item.keys() & http:
            raise ValueError("Supply connection settings only for HTTP MCP.")
        return result
    url = item.get("url", ENDPOINTS.get(name))
    if not url:
        raise ValueError("This surface requires a vendor-confirmed MCP endpoint.")
    result["url"] = endpoint(url)
    if name in ENDPOINTS and result["url"] != ENDPOINTS[name]:
        raise ValueError("Use the documented endpoint for this built-in adapter.")
    if "client_id" in item:
        result["client_id"] = label(item["client_id"])
    scopes = item.get("scopes", [])
    if not isinstance(scopes, list) or len(scopes) > 40:
        raise ValueError("Scopes must be a short list.")
    return {**result, "scopes": [label(scope) for scope in scopes]}


def env_name(name: str) -> str:
    """Return the guest-only environment name for a provider token."""
    return "FREELANCE_" + slug(name).upper().replace("-", "_") + "_TOKEN"


def configurations(spec: dict[str, Any]) -> tuple[str, str]:
    """Render private Codex TOML and Claude project MCP JSON from the same plan."""
    quote = json.dumps
    codex = [
        'cli_auth_credentials_store = "file"',
        'mcp_oauth_credentials_store = "file"',
        "[features]",
        "apps = false",
    ]
    claude: dict[str, Any] = {}
    for item in spec["surfaces"]:
        if item["method"] not in {"oauth", "bearer"}:
            continue
        name = item["id"]
        url = item["url"]
        settings = ["", f"[mcp_servers.{name}]", f"url = {quote(url)}"]
        server: dict[str, Any] = {"type": "http", "url": url}
        if item["method"] == "bearer":
            var = env_name(name)
            server["headers"] = {"Authorization": "Bearer " + "$" + "{" + var + "}"}
            settings.append(f"bearer_token_env_var = {quote(var)}")
        if item.get("scopes"):
            settings.append(f"scopes = {quote(item['scopes'])}")
        if item.get("client_id"):
            settings.append(f"oauth.client_id = {quote(item['client_id'])}")
            server["oauth"] = {"clientId": item["client_id"]}
        if item["harness"] in {"both", "codex"}:
            codex.extend(settings)
        if item["harness"] in {"both", "claude"}:
            claude[name] = server
    return "\n".join(codex) + "\n", json.dumps({"mcpServers": claude}, indent=2) + "\n"
