# {Client} workspace

Work email: `{client-issued email}`

Folder: `{client folder name}`

## Before starting any work product

1. Read this file from the client folder you are working in. Match the requested client, work email, and task to this folder. If the binding is missing, ambiguous or conflicts with the request, pause before drafting, editing, or calling a connector. Ask which workspace to use. The Claude or Codex subscription account may differ from the client work email.
2. Identify which connectors the work product depends on. For each one, use that specific connection's read-only account/profile check. Match its signed-in email and target workspace, organization or resource ID against the row below. Use an alternate provider principal only if the operator recorded it explicitly. For a local-only task, the folder and task match completes the check.
3. If the connector hides the account, have the operator inspect the account and target in that exact connection's settings. If either is wrong or cannot be established, stop the affected work before reading client content, drafting from it, or sending anything. Ask the operator to select or reconnect the correct account and repeat the check. Never fall back to the first available connection.
4. Use the verified connection for this work item. Repeat the check when starting another work product, resuming a session, switching accounts or connectors, or changing targets. If a write or send can silently use another account, recheck immediately before it. Only take actions the operator authorized. A saved check is historical evidence.

## Connectors

| Connector and connection label | Expected email or approved principal | Target workspace or resource | Allowed work |
| --- | --- | --- | --- |
| {selected connector} | {exact identity} | {tenant or resource ID, or unambiguous target} | {agreed access} |

## Client conventions

{Keep durable preferences, terminology, standing decisions and deliverable conventions here. Link authoritative references when needed.}

## Active tasks

{Link each active task file. Remove completed tasks from this list and retain their files.}

## Resume and hand off

Read the relevant task file, then its linked handoff or artifact. Use the task's goal, decisions, status and next action to resume. At an interruption, decision or delivery, update the task. Append a dated entry to `context/YYYY-MM-DD.md` for a material change, link it from the task, and identify any earlier decision it supersedes. Use a timestamp with an offset if order matters. Keep credentials, OAuth codes and client content unrelated to the task out of these notes.
