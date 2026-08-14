import json
from pathlib import Path

from paths import (
    CONTRACT_PATH,
    PROPOSAL_PATH,
    VALIDATION_REPORT_PATH,
    WORKSPACE_DIR
)


def safe_workspace_path(file_name):
    """Reject paths outside workspace/."""

    path = Path(file_name)

    if path.name != file_name:
        raise ValueError("Invalid workspace filename.")

    return WORKSPACE_DIR / file_name


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def show_proposal(proposal):
    print("\nProposed changes:")

    for update in proposal["updates"]:
        print(f"\nFile: {update['file_name']}")
        print(f"Replace: {update['original_text']}")
        print(f"With:    {update['replacement_text']}")
        print(f"Reason:  {update['reason']}")


def apply_updates(contract, proposal):
    """Apply one validated replacement per permitted workspace file."""

    for update in proposal["updates"]:
        file_name = update["file_name"]
        original_text = update["original_text"]
        replacement_text = update["replacement_text"]

        if file_name not in contract["allowed_files"]:
            raise PermissionError(
                f"Blocked: {file_name} is not allowed by the contract."
            )

        path = safe_workspace_path(file_name)

        content = path.read_text(encoding="utf-8")

        if content.count(original_text) != 1:
            raise ValueError(
                f"Blocked: {file_name} must contain the original text "
                "exactly once before an update can be applied."
            )

        updated_content = content.replace(
            original_text,
            replacement_text,
            1
        )

        path.write_text(updated_content, encoding="utf-8")


def main():
    required_files = [
        CONTRACT_PATH,
        PROPOSAL_PATH,
        VALIDATION_REPORT_PATH
    ]

    if not all(path.exists() for path in required_files):
        raise FileNotFoundError(
            "Run the workflow, proposal agent, and validator first."
        )

    contract = load_json(CONTRACT_PATH)
    proposal = load_json(PROPOSAL_PATH)
    validation = load_json(VALIDATION_REPORT_PATH)

    if not validation["passed"]:
        print("Application blocked: validation did not pass.")
        raise SystemExit(1)

    if contract["human_approval_required"] is not True:
        print("Application blocked: human approval is required.")
        raise SystemExit(1)

    show_proposal(proposal)

    approval = input(
        "\nType APPROVE to apply these changes: "
    )

    if approval != "APPROVE":
        print("No changes were applied.")
        return

    apply_updates(contract, proposal)

    contract["status"] = "approved_and_applied"

    CONTRACT_PATH.write_text(
        json.dumps(contract, indent=2),
        encoding="utf-8"
    )

    print("\nApproved changes applied successfully.")
    print("Run: git --no-pager diff")


if __name__ == "__main__":
    main()