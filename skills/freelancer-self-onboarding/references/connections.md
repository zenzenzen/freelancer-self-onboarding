# Finish the connections

Run these commands **inside the selected client container** or prefix them with the host helper's `--base BASE run SLUG`. The host's currently connected apps and browser cookies do not establish the client's identity.

| Surface | First setup | Evidence before marking verified |
| --- | --- | --- |
| Slack | Choose the expected workspace and approved user or app. Register the built-in Slack MCP entry. If Slack requires an approved OAuth client, obtain its public client ID and handle its secret privately. | Match the signed-in member and workspace/team ID. Check the approved scopes and a permitted channel. |
| Google | Ask which of Gmail, Drive and Calendar the client uses. Confirm the client's OAuth app, product API, MCP service, scopes and any preview/admin eligibility. A registered client used for Google Workspace MCP must be marked for AI-powered agent use. | Match the returned Google identity and the requested mailbox, calendar or shared drive. A broad domain or Drive scope alone cannot establish resource isolation. |
| MetaMVP | Ask for the exact Claude tool/connector name once. Use the tenant's Claude plugin listing or MCP configuration to identify its publisher and install method. If it is visible only through a shared account-wide connector, keep it pending until the client provides a scoped route. | Match its displayed Claude installation and the client project or account it opens. |
| Additional CRM | Accept a free-text display name. Determine whether the vendor provides a plugin, OAuth MCP, bearer MCP, or only a web UI. Save the generic connector name for later intakes. | Match provider user/seat, portal or organization ID, and the requested role. For a browser-only surface record manual access. |

## Authentication

- For Codex CLI sign-in, use `codex login --device-auth` where the client organization permits device login. For Claude, use `claude auth login` and follow the client's SSO flow. Each CLI persists login in this workspace's private home. Keep account-level connectors disabled in both clients.
- For a configured OAuth MCP, use `codex mcp login NAME --no-browser` or `claude mcp login NAME --no-browser` in the operator's terminal. Claude may first ask the user to trust the project and approve the selected project MCP servers. Complete consent in the client's browser profile. Paste a callback only into the waiting CLI. Check the scopes on the consent screen, especially for Claude project entries. Decline grants exceeding the agreed access.
- If the provider requires a confidential client, use the provider-approved native secret prompt or configure the private runtime directly. For example, Claude supports `claude mcp add --scope local --transport http --client-id PUBLIC_ID --client-secret NAME VERIFIED_URL` with a masked secret prompt. Use the redirect URI registered by the client. Codex supports a pre-registered OAuth client in its private MCP settings. Edit any necessary secret privately in the client terminal. Never paste a secret into the agent session, the project file, a shell argument or the root context.
- For an approved bearer connector, select `bearer` at intake. Run `python3 "$W" --base "$BASE" run SLUG token NAME` in the operator's host terminal. The guest reads masked input, writes into its private home, then injects the token only into a matching harness at its next launch. Rotate it with the same command.
- For a plugin, check the live client catalog first. Install the exact approved selector inside the container with `claude plugin install --scope local PLUGIN@MARKETPLACE` or `codex plugin add PLUGIN@MARKETPLACE`. If an approved marketplace must be added, use its official source and check the installed harness's marketplace help. Complete plugin authorization and verify the connected identity separately. A cloud-only connector that cannot be restricted to this client stays pending.
- For a mismatch, stop work on that surface, sign out or revoke that connection in the client profile, and reauthenticate. Record the result locally. Do not probe other clients as an isolation test.

## Provider references

- [Slack MCP setup](https://docs.slack.dev/ai/slack-mcp-server/)
- [Google Workspace MCP setup and endpoints](https://developers.google.com/workspace/guides/configure-mcp-servers)
- [Codex configuration](https://developers.openai.com/codex/config-reference/)
- [Claude Code MCP and connector scopes](https://code.claude.com/docs/en/mcp)
