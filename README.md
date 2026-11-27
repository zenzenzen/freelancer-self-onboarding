# Freelancer Self-Onboarding

Give Codex or Claude Code a client folder and a work email. The skill records which account and workspace each connector should use. Before starting a deliverable, the agent reads that folder's identity and checks the connections the task needs.

For example, suppose the folder expects `alex@northwind.example` and the Google Drive connector reports `alex@southwind.example`. The agent pauses before opening the brief or drafting from it. Once the operator selects the Northwind connection, the agent checks the email and shared drive again and resumes the task.

## Start

Open this repository in Codex CLI or Claude Code and invoke the skill with the path to your client folder. Use either command below. The skill consists of Markdown instructions and templates.

```text
$freelancer-self-onboarding Set up ~/Clients/northwind for alex@northwind.example.
/freelancer-self-onboarding Set up ~/Clients/northwind for alex@northwind.example.
```

The first form is for Codex and the second is for Claude Code. To make the onboarding command available from other folders, run these commands once from the cloned repository:

```sh
mkdir -p "$HOME/.agents/skills" "$HOME/.claude/skills"
ln -s "$PWD/skills/freelancer-self-onboarding" "$HOME/.agents/skills/"
ln -s "$PWD/skills/freelancer-self-onboarding" "$HOME/.claude/skills/"
```

Choose Slack, the relevant Google products, MetaMVP on Claude, or type the name of another connector or CRM. The skill remembers reusable product names for future intakes. The client folder records the specific account, tenant and access.

## What another account reads

| File in the client folder | What it tells the next agent |
| --- | --- |
| `AGENTS.md` and `CLAUDE.md` | Open the same root instructions before starting or resuming work. |
| `WORKSPACE.md` | Which client and email own the work, the expected account and target for each connector, standing conventions and links to active tasks. |
| `tasks/<task>.md` | What counts as done, the latest artifact, what has already been delivered and the next action. |
| `context/YYYY-MM-DD.md` | What changed on that date, who decided it or what supported it, and which task it affects. |

Open the client folder in a fresh session after switching Claude accounts or moving to Codex. Ask it to resume the relevant task. The agent can recover the work from disk and must verify any live connection it uses. A local-only deliverable requires the matching folder and task. Credentials stay in the harness or provider's normal credential store. The folder supplies an agent-level identity check. The provider enforces access permissions.

The layout adapts ICM's context map and task records to this one workflow. Existing task indexes and dated journals can be linked in place. [ICM Architect](https://github.com/RinDig/icm-architect) · [Methodology paper](https://arxiv.org/abs/2603.16021)

[Read the onboarding skill](skills/freelancer-self-onboarding/SKILL.md) · [Preview the workspace identity file](skills/freelancer-self-onboarding/assets/WORKSPACE.md)

## Synthetic GEM isolation pilot

The local pilot switches between two synthetic clients and resumes each client’s own task. It uses the installed `graph-engineering-magic` executable. [Acceptance tests and scope](PILOT.md)

Validate the repository and compile its pilot task.

```sh
graph-engineering-magic --workspace . --workspace-id fso-pilot validate
graph-engineering-magic --workspace . --workspace-id fso-pilot context compile --task "run synthetic isolation pilot" --seed task.synthetic-isolation-pilot --budget 7000
```

Save and resume a synthetic Client B handoff from the repository root.

```sh
python3 -m pilot.demo save --workspace fixtures/client-b --intended-root fixtures/client-b --workspace-id client-b --principal worker-b@example.invalid --tenant tenant-b --target drive-b --key demo --request pilot/requests/client-b.json --next-step "Review the synthetic Client B status note."
python3 -m pilot.demo resume --workspace fixtures/client-b --intended-root fixtures/client-b --workspace-id client-b --principal worker-b@example.invalid --tenant tenant-b --target drive-b --key demo
```
