import json
from pathlib import Path

from paths import (
    CONTRACT_PATH,
    PROPOSAL_PATH,
    VALIDATION_REPORT_PATH,
    WORKSPACE_DIR,
    ensure_runtime_directory
)


def safe_workspace_path(file_name):
    """Reject paths outside workspace/."""

    path = Path(file_name)

    if path.name != file_name:
        raise ValueError("Invalid workspace filename.")

    return WORKSPACE_DIR / file_name


def validate_proposal(contract, proposal):
    """Return errors and warnings for a proposed patch."""

    errors = []
    warnings = []

    allowed_files = set(contract["allowed_files"])
    protected_files = set(contract["protected_files"])
    maximum_files = contract["maximum_files_changed"]

    updates = proposal.get("updates", [])
    changed_files = [update["file_name"] for update in updates]
    unique_changed_files = set(changed_files)

    if len(unique_changed_files) > maximum_files:
        errors.append(
            f"Proposal changes {len(unique_changed_files)} files, "
            f"but the contract allows only {maximum_files}."
        )

    if len(changed_files) != len(unique_changed_files):
        errors.append(
            "A file appears more than once in the proposal. "
            "This MVP permits one replacement per file."
        )

    if not updates:
        warnings.append("The model proposed no changes.")

    for update in updates:
        file_name = update["file_name"]
        original_text = update["original_text"]
        replacement_text = update["replacement_text"]

        if file_name not in allowed_files:
            errors.append(f"{file_name} is not an allowed file.")

        if file_name in protected_files:
            errors.append(f"{file_name} is protected.")

        if not original_text.strip():
            errors.append(
                f"{file_name} has empty original text."
            )

        if not replacement_text.strip():
            errors.append(
                f"{file_name} has empty replacement text."
            )

        if original_text == replacement_text:
            errors.append(
                f"{file_name} has identical original and replacement text."
            )

        try:
            path = safe_workspace_path(file_name)
        except ValueError as error:
            errors.append(str(error))
            continue

        if not path.exists():
            errors.append(f"{file_name} does not exist.")
            continue

        file_content = path.read_text(encoding="utf-8")

        if file_content.count(original_text) != 1:
            errors.append(
                f"{file_name} must contain the original text exactly once."
            )

    return errors, warnings


def main():
    if not CONTRACT_PATH.exists() or not PROPOSAL_PATH.exists():
        raise FileNotFoundError(
            "Run controlled_workflow.py and proposal_agent.py first."
        )

    contract = json.loads(
        CONTRACT_PATH.read_text(encoding="utf-8")
    )

    proposal = json.loads(
        PROPOSAL_PATH.read_text(encoding="utf-8")
    )

    errors, warnings = validate_proposal(contract, proposal)

    report = {
        "passed": len(errors) == 0,
        "decision_id": contract["decision_id"],
        "checked_files": [
            update["file_name"]
            for update in proposal.get("updates", [])
        ],
        "errors": errors,
        "warnings": warnings
    }

    ensure_runtime_directory()

    VALIDATION_REPORT_PATH.write_text(
        json.dumps(report, indent=2),
        encoding="utf-8"
    )

    if report["passed"]:
        print("Validation passed.")
    else:
        print("Validation failed.")

        for error in errors:
            print("-", error)

    for warning in warnings:
        print("Warning:", warning)

    print("Report saved:", VALIDATION_REPORT_PATH)


if __name__ == "__main__":
    main()