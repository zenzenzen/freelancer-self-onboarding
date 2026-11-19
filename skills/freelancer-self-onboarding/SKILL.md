---
name: freelancer-self-onboarding
description: Bind a client work folder to its work email, verify the active account and tenant on each connector before doing client work, and resume tasks from durable Markdown across Claude Code and Codex sessions. Use when onboarding a client, switching folders or accounts, or handing off ongoing work.
---

# Freelancer self-onboarding

## Set up a folder

1. Use the work email and destination the operator supplies. Ask for whichever is missing and the client's label. Use an existing client folder or create the requested subfolder. Read its root instructions and any existing `WORKSPACE.md` first. Keep each client at its own root. If the folder already names another client/email, leave it intact and resolve the destination with the operator.
2. Offer Slack, the Google products the operator uses, and MetaMVP for Claude. Read any remembered product names from the operator's catalog. Ask which apply here and let the operator type additional connectors or CRMs. For each selected connection, establish its display label, expected email (inherit the work email unless explicitly told otherwise), client tenant or resource, and intended access. Ask for MetaMVP's exact Claude listing on first use. When the operator sees multiple connections to the same provider, record enough detail to choose the right one.
3. Create the root `WORKSPACE.md` from [the workspace template](assets/WORKSPACE.md). Fill the known fields and label pending items explicitly. Carry client-wide conventions from existing harness instructions into the shared root, with a source link. Keep harness-specific settings in their original file. On later visits update only what changed. Record the user's connector choices immediately. If setup is needed, use the harness's native connector or plugin flow for the approved listing and account. The operator completes provider consent privately. An installed connector still needs an identity check before use.
4. Put the following instruction in both root `AGENTS.md` and `CLAUDE.md`. Create missing files. In existing files add it once, preserving project instructions. Resolve any existing contradictory account binding with the operator. Use a relative path so a different account can open the same folder.

   > Before starting or resuming any work product, read WORKSPACE.md in this client root. Apply its account and target checks, then open the relevant active task. Follow its handoff instructions before ending work.

5. Keep reusable **product names and harness compatibility only** in `~/.config/freelancer-self-onboarding/connectors.md`, or the operator's chosen portfolio catalog. Upsert a new generic name when the operator adds or renames a connector here. Reuse it as a suggestion next time. For a local alias that identifies a client, record its generic product name in the catalog and keep the alias in the client folder. Membership, identity, history, and access are specific to the current folder.

## Do or resume work

Start from the root file even if the current conversation recalls a different account. Apply its gate before producing a work product. Only identity/target inspection and onboarding may precede the gate. If the intended client itself is uncertain, resolve that before any connector call. Keep credentials in the provider or harness credential store.

Use the active-task index to select a task. For a new ongoing task, copy [the task template](assets/TASK.md) to `tasks/<descriptive-slug>.md` and link it from the index. Read that task, the dated note it references, and the actual working artifact. If the folder already has an ICM task index or dated journal, link and use those existing files. When task state conflicts, follow the latest explicit decision supported by a date and source. Ask if the conflict is unresolved.

At a handoff, interruption or delivery, persist the current artifact, status and next action. Append a short entry to `context/YYYY-MM-DD.md` for decisions, blockers or delivery events worth retaining. Include the task link, what changed, why, and the evidence or artifact. Preserve earlier entries. Promote a recurring client convention to the root once. A fresh agent should be able to identify the work email, find the latest artifact, tell what has already been sent, and name the next step from the folder alone.

## Adopt a folder from the earlier version

If the folder contains `CLIENT_CONTEXT.json`, read its non-secret intake fields and the task-relevant entries in `work/CONNECTIONS.md`. With the operator's chosen work folder as root, carry over the expected identities, connector targets and pending work. Replace any previous generated instruction pointing to `/client/CLIENT_CONTEXT.json` with the relative root instruction. Treat old verification records as history. Leave credentials and project files in place. An existing portfolio catalog can supply its generic connector labels and harness hints.
