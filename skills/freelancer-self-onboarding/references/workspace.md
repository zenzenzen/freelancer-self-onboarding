# Host setup

Use Python 3.11+ on macOS or Linux and a local Docker Engine with support for nonrecursive bind mounts. Set `SKILL` to the absolute path of this installed skill. Create a private portfolio outside the distribution checkout. On macOS use its real path, e.g. a folder under your home directory.

```sh
docker build -t freelancer-self-onboarding:1 "$SKILL"
W="$SKILL/scripts/workspace.py"
BASE="$HOME/Clients"
python3 "$W" --base "$BASE" catalog
```

Create a client at `BASE/SLUG`. A missing or empty folder works. To retain an existing nonempty project, choose a new subfolder and move or clone only the authorized project into its `work/` directory. Run the following synthetic example with the user's choices substituted. A real provider code or token never belongs in this JSON.

```sh
python3 "$W" --base "$BASE" init northwind <<'JSON'
{
  "client": "Northwind Studio",
  "email": "operator@northwind.example",
  "surfaces": [
    {"id": "slack", "principal": "operator@northwind.example", "target": "Northwind Slack", "access": "Read assigned project channels", "method": "oauth", "connector": "Slack"},
    {"id": "google-drive", "principal": "operator@northwind.example", "target": "Client design drive", "access": "Read files in the assigned drive", "method": "oauth", "scopes": ["https://www.googleapis.com/auth/drive.readonly"]},
    {"id": "metamvp", "principal": "Client-issued Claude account", "target": "Northwind project", "access": "Use the assigned project", "method": "plugin", "connector": "MetaMVP"},
    {"id": "crm", "principal": "Client SSO seat", "target": "Northwind portal", "access": "View assigned leads", "method": "manual", "connector": "Example CRM"}
  ]
}
JSON
python3 "$W" --base "$BASE" run northwind codex
# In a separate terminal session for the same client:
python3 "$W" --base "$BASE" run northwind claude
```

`harness` accepts `both`, `claude` or `codex`. MetaMVP defaults to Claude. Set the field on other surfaces when the user selects only one harness. A generic CRM name is remembered across harnesses even if this client uses only one. Set `connector_harness` to record a known restriction for that connector. `method` accepts `oauth`, `bearer`, `plugin` or `manual`. HTTP MCP supports a verified `url`, optional public `client_id`, and optional `scopes`. The first release has built-in endpoints for Slack, Gmail, Drive and Calendar. Supply a verified HTTPS endpoint for another MCP service. Use `manual` to retain an integration pending a vendor or admin decision. The `access` field expresses the request. The provider must enforce the grant.

## What persists

| Location | Contents |
| --- | --- |
| `BASE/.freelancer-catalog.sqlite3` | Host-only index of registered folder names and reusable connector labels. |
| `BASE/SLUG/CLIENT_CONTEXT.json` | Client identity, intended accounts, resources and access. Mounted read-only at `/client/CLIENT_CONTEXT.json`. |
| `BASE/SLUG/work/` | Files for this client, Codex and Claude instruction files, MCP registration, connection ledger and name-only export receipt. |
| `BASE/SLUG/private-home/` | This client's CLI logins, MCP OAuth tokens, optional bearer tokens, plugin state and session history. Protect this directory and its backups as credentials. |

Each launch creates a disposable non-root container on a client-specific bridge. The launcher mounts the three client paths above, strips Linux capabilities, and uses a read-only image. The portfolio, sibling folders, host agent sockets, and host CLI profiles stay outside the container. The portfolio's operating-system owner and Docker administrator remain trusted. Both CLIs inside one client share that client's trust boundary. Outbound networking is enabled for vendor APIs. For browser consent use a client-specific browser profile and verify the displayed account. SaaS access, provider retention and scopes remain subject to the client's accounts and policies.

Use a client-approved upstream model account or API identity for each engagement. Reusing a single cloud account across clients can share server-side state even when local histories are separate. For durable settings added later, edit only the relevant client's native configuration from inside its container and update `CONNECTIONS.md`. Rerunning the original intake preserves those settings.
