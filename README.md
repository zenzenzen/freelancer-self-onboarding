# Freelancer Self-Onboarding

Give Codex CLI or Claude Code a client-issued work email and the skill asks where you use it, which account the provider displays, and what access the job calls for. It creates a dedicated Docker workspace for that client. Your next engagement starts with the connector names you already know and a fresh set of credentials.

## Start an onboarding

Clone this repository, open it in Codex CLI or Claude Code, and use one of these prompts. Both project skill directories point to the same source. The operator machine needs Python 3.11+ and a running local Docker Engine on macOS or Linux.

```text
Codex: $freelancer-self-onboarding Onboard operator@northwind.example in ~/Clients/northwind.
Claude Code: /freelancer-self-onboarding Onboard operator@northwind.example in ~/Clients/northwind.
```

Choose Slack, the Google Workspace products you use, and any additional connector or CRM by name. Claude users also get MetaMVP. The skill writes a private client context at the workspace root, registers selected MCP endpoints, and walks the installed harness through plugin installation, consent and verification. For an unfamiliar connector, it asks for the exact listing. Each connection stays pending until the signed-in account and target workspace match the intake.

To make the skill available from other folders, run the following once from the trusted clone. The links load the onboarding instructions in each CLI. Client credentials are created later in the selected workspace.

```sh
mkdir -p "$HOME/.agents/skills" "$HOME/.claude/skills"
ln -s "$PWD/skills/freelancer-self-onboarding" "$HOME/.agents/skills/"
ln -s "$PWD/skills/freelancer-self-onboarding" "$HOME/.claude/skills/"
```

## What carries over to the next client

| Reused by the freelancer | Specific to each client |
| --- | --- |
| Generic connector names and which harness can use them | Work email, provider identities, resource IDs and intended permissions |
| New CRM names typed during intake | Tokens, OAuth sessions, CLI history, plugins and project files |
| Changes discovered in client MCP settings and plugin lists, after the skill checks the labels | Provider configuration, tenant URLs and connection verification records |

The base catalog lives on your machine. Returning to the skill refreshes it from small name-only receipts. The skill checks unfamiliar aliases before offering them to another client. A client container cannot mount the catalog or open a sibling's workspace through the launcher.

## Switch clients

Build the image once from this checkout, then launch the workspace created during intake.

```sh
SKILL="$PWD/skills/freelancer-self-onboarding"
docker build -t freelancer-self-onboarding:1 "$SKILL"
python3 "$SKILL/scripts/workspace.py" --base "$HOME/Clients" run northwind claude
# After ending that session, open another client's fresh Codex session.
python3 "$SKILL/scripts/workspace.py" --base "$HOME/Clients" run southwind codex
```

Each launch gets a fresh container on the client's own Docker network. Its work directory and private home persist. The host operator and Docker administrator can access those files. The container can reach provider APIs, and providers enforce their own tenant permissions. Use a client-specific browser profile for consent and a client-approved model identity. Account-wide hosted connectors are disabled by default.

- [Onboarding skill](skills/freelancer-self-onboarding/SKILL.md)
- [Workspace layout, intake schema and worked example](skills/freelancer-self-onboarding/references/workspace.md)
- [Provider setup and identity checks](skills/freelancer-self-onboarding/references/connections.md)

## Verify the installation

```sh
python3 -m unittest discover -s tests -v
# After building the image, include the live two-client Docker checks.
TEST_DOCKER=1 python3 -m unittest discover -s tests -v
```

The tests use synthetic clients. No provider login is needed.
