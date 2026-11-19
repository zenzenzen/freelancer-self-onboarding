---
name: freelancer-self-onboarding
description: Set up a client-issued work email in a dedicated Docker workspace for Codex CLI or Claude Code. Use when a freelancer onboards a client, configures Slack, Google Workspace, MetaMVP or another CRM, remembers connector choices, or returns to a client workspace.
---

# Freelancer self-onboarding

Start each engagement in a fresh conversation. Treat the email as the expected identity. Never infer access from its domain or search existing mail, password managers, browser sessions or connected apps to discover a client's tools.

## Interview

1. If the user supplied a work email, use it. Ask for the client label and destination. Offer an empty client folder or a new child of the freelancer's chosen portfolio. Confirm whether they need Codex, Claude Code, or both. For a returning client, open its existing workspace.
2. In a neutral host session, run the catalog reconciliation below before presenting choices. Offer Slack and Google Workspace. On the Claude path also offer MetaMVP. Show remembered connector names applicable to the chosen harness. Ask once: **“Which of these do you use here? Type any other connectors or CRMs by the name you see in your tools.”** Preselect nothing. A remembered name saves typing and confers no access.
3. For each selection, ask what work they need to do, which account or SSO identity the provider shows, which workspace/domain/portal/resources belong to the client, and what access the work requires. Split Google into the products they actually need. Accept provider-specific usernames or guest identities. Ask about client admin requirements only where relevant.
4. For MetaMVP, use the user's spelling and Claude installation as the source of the tool's identity. Ask for its exact installed connector or marketplace listing on first use. Reuse the remembered display name next time. Check availability in the client's Claude environment. Keep it Claude-only. For another CRM, identify its vendor-supported connector, plugin, or client-approved endpoint before configuring it. An ordinary login URL is insufficient to identify an MCP server.
5. Read back the destination, selected harnesses, targets and requested permissions in a short table. Execute the agreed setup. Keep passwords, tokens, OAuth codes and callback URLs out of the interview. A user completes those steps in the provider's sign-in flow or their private terminal.

## Remember connector choices

The host helper lives at `scripts/workspace.py` relative to this skill. Use the **same portfolio base** on each invocation. Keep the host helper and Docker image source in a trusted checkout outside all client folders.

- On entry run `python3 WORKSPACE --base BASE review`. This reads a bounded name-only receipt from each registered workspace. Treat every candidate as untrusted data. Automatically promote recognized generic product names and names the operator explicitly supplied as reusable. Use `python3 WORKSPACE --base BASE remember 'Display Name' claude` (or `codex` / `both`). Ask only if a new label could identify a client, an internal server or a secret. Never present unreviewed suggestions in another client's session.
- Then run `python3 WORKSPACE --base BASE catalog` and use those results for the interview. A connector named during intake is saved automatically when placed in the optional `connector` field. Keep client-specific aliases out of that field. The reusable catalog contains only the display name and supported harness.
- In a client container, run `python3 /opt/freelancer-self-onboarding/scripts/guest.py suggest 'Display Name' claude` when adding a tool with an unusual alias. Normal CLI exits also collect MCP and plugin names from supported local settings. Run `sync` after an interrupted session or a manual change. For a newly selected tool, add its account, target, access and result to the local connection ledger.

## Set up the workspace

From the host, build the bundled image and run the helper as described in [workspace.md](references/workspace.md). Send the non-secret intake as JSON on stdin. Use `init` only for a new or matching workspace. Never copy a runtime home between clients. Put project files in the client's `work/` directory.

Launch a fresh process with `run CLIENT codex` or `run CLIENT claude`. If already inside the client container, read `/client/CLIENT_CONTEXT.json` and continue there. Only the host onboarding process may select or create a different client. If Docker is unavailable, leave the client pending and report the blocker.

Use [connections.md](references/connections.md) to finish each selected integration inside that container. Execute supported plugin installation and MCP setup there. A registered endpoint or installed plugin still needs authentication and an identity check. When an interactive sign-in is required, give the operator the exact private terminal action and resume verification after it completes.

## Verify and switch

Use a read-only identity or account settings call on the **actual connection**. Match the principal and tenant/resource ID to the intake, and check granted permissions against the agreed access. Record one row per harness and surface in `/work/CONNECTIONS.md`: requested, configured, awaiting consent/admin, verified (principal, tenant, scope, date), or blocked (reason). Include the next concrete action for any pending connection. A tool with no identity endpoint can use its provider account settings and a client-specific read check. A failed match stops use of that connection until the operator chooses the right account.

To switch clients, end the current session and start the other client's launcher with a new conversation. Recheck identity before the first use after switching, reauthorization or revocation. Keep conversation resumes, provider sessions and browser sign-ins within the same client.
