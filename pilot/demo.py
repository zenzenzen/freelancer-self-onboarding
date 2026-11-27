"""Command-line entry for the synthetic guarded handoff demonstration."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .guard import GuardDenied, guarded_handoff


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("operation", choices=["save", "resume"])
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--intended-root", type=Path, required=True)
    parser.add_argument("--workspace-id", required=True)
    parser.add_argument("--principal", required=True)
    parser.add_argument("--tenant", required=True)
    parser.add_argument("--target", required=True)
    parser.add_argument("--key", required=True)
    parser.add_argument("--request", type=Path)
    parser.add_argument("--next-step")
    args = parser.parse_args()
    try:
        result = guarded_handoff(
            args.workspace,
            args.intended_root,
            args.workspace_id,
            {
                "principal": args.principal,
                "tenant": args.tenant,
                "target": args.target,
            },
            args.operation,
            args.key,
            args.request,
            args.next_step,
        )
    except GuardDenied as exc:
        print(json.dumps({"status": "denied", "reason": str(exc)}))
        return 3
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
