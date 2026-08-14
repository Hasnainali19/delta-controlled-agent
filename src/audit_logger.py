import hashlib
import json
import subprocess
from datetime import datetime, timezone

from paths import (
    AUDIT_LOG_PATH,
    CONTRACT_PATH,
    PROPOSAL_PATH,
    VALIDATION_REPORT_PATH,
    PROJECT_ROOT,
    ensure_runtime_directory
)


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def get_workspace_diff(contract):
    """Capture the Git diff for the plan and permitted workspace files."""

    files_to_check = [
        "workspace/plan.md"
    ] + [
        f"workspace/{file_name}"
        for file_name in contract["allowed_files"]
    ]

    result = subprocess.run(
        ["git", "diff", "--"] + files_to_check,
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True
    )

    return result.stdout


def main():
    required_files = [
        CONTRACT_PATH,
        PROPOSAL_PATH,
        VALIDATION_REPORT_PATH
    ]

    if not all(path.exists() for path in required_files):
        raise FileNotFoundError(
            "Contract, proposal, and validation report are required."
        )

    contract = load_json(CONTRACT_PATH)
    proposal = load_json(PROPOSAL_PATH)
    validation = load_json(VALIDATION_REPORT_PATH)

    git_diff = get_workspace_diff(contract)

    outcome = (
        "validation_passed"
        if validation["passed"]
        else "validation_failed"
    )

    record = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "decision_id": contract["decision_id"],
        "contract_status": contract["status"],
        "outcome": outcome,
        "allowed_files": contract["allowed_files"],
        "protected_files": contract["protected_files"],
        "proposal_summary": proposal["summary"],
        "proposed_files": [
            update["file_name"]
            for update in proposal["updates"]
        ],
        "validation_errors": validation["errors"],
        "git_diff_sha256": hashlib.sha256(
            git_diff.encode("utf-8")
        ).hexdigest()
    }

    ensure_runtime_directory()

    with AUDIT_LOG_PATH.open("a", encoding="utf-8") as file:
        file.write(json.dumps(record) + "\n")

    print("Audit record saved:", AUDIT_LOG_PATH)
    print("Outcome:", outcome)


if __name__ == "__main__":
    main()