# Two-client handoff pilot

The two fixtures represent clients with different connector principals, tenants and targets. Their account data and work notes are synthetic. The repository's onboarding skill supplies the policy. Each fixture has a separate GEM workspace and task.

The demo checks the intended folder and workspace ID, then compares the supplied identity to `binding.json`. Before calling GEM, it checks that the manifest enrolls exactly the bound sources. Both save and resume take this path. The tests try the wrong root, workspace ID, principal, tenant and target. They watch file reads and process launches to verify that a rejected request stops before GEM reads client content.

For the handoff test, both clients save different next steps under the same key. Fresh processes switch back through the clients, recheck identity, and recover each client's own next step. All mutable test state stays in temporary copies.

Run these commands from the repository root with Python, pytest and the installed GEM CLI on PATH.

```sh
graph-engineering-magic --workspace . --workspace-id fso-pilot validate
graph-engineering-magic --workspace . --workspace-id fso-pilot context compile --task "run synthetic isolation pilot" --seed task.synthetic-isolation-pilot --budget 7000
python3 -m pytest -q pilot/test_pilot.py
```

The demo accepts synthetic identity values supplied by the test operator. Live onboarding still requires the connector's own identity check and provider-enforced permissions. The handoff records a next step for the operator.
