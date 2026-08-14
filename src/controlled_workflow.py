import json
import re
import subprocess

from paths import (
    DEPENDENCIES_PATH,
    PLAN_PATH,
    CONTRACT_PATH,
    PROJECT_ROOT,
    WORKSPACE_FILES,
    ensure_runtime_directory
)


def get_previous_plan():
    """Read the most recent committed version of the plan from Git."""

    possible_paths = ["workspace/plan.md", "plan.md"]

    for git_path in possible_paths:
        result = subprocess.run(
            ["git", "show", f"HEAD:{git_path}"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            return result.stdout

    raise RuntimeError("Git could not find a committed plan.md file.")


def get_current_plan():
    """Read the user's current plan from the workspace."""

    return PLAN_PATH.read_text(encoding="utf-8")


def extract_decisions(plan_text):
    """Convert Markdown decisions into {decision_id: decision_value}."""

    decisions = {}
    current_id = None
    content = []

    for line in plan_text.splitlines():
        match = re.match(r"#+\s*(DEC-\d+)", line)

        if match:
            if current_id:
                decisions[current_id] = "\n".join(content).strip()

            current_id = match.group(1)
            content = []

        elif current_id:
            content.append(line)

    if current_id:
        decisions[current_id] = "\n".join(content).strip()

    return decisions


def find_changed_decisions():
    """Compare Git's baseline plan with the current plan."""

    old_decisions = extract_decisions(get_previous_plan())
    current_decisions = extract_decisions(get_current_plan())

    changes = []

    for decision_id, current_value in current_decisions.items():
        old_value = old_decisions.get(decision_id)

        if old_value != current_value:
            changes.append({
                "decision_id": decision_id,
                "before": old_value,
                "after": current_value
            })

    return changes


def create_contract(change):
    """Create a scoped permission document for exactly one decision."""

    dependencies = json.loads(
        DEPENDENCIES_PATH.read_text(encoding="utf-8")
    )

    decision_id = change["decision_id"]

    if decision_id not in dependencies:
        raise ValueError(
            f"No dependency rule exists for {decision_id}."
        )

    allowed_files = dependencies[decision_id]
    protected_files = sorted(
        WORKSPACE_FILES - set(allowed_files)
    )

    contract = {
        "decision_id": decision_id,
        "before": change["before"],
        "after": change["after"],
        "allowed_files": allowed_files,
        "protected_files": protected_files,
        "maximum_files_changed": len(allowed_files),
        "human_approval_required": True,
        "status": "proposed"
    }

    ensure_runtime_directory()

    CONTRACT_PATH.write_text(
        json.dumps(contract, indent=2),
        encoding="utf-8"
    )

    print(f"Contract created for {decision_id}")
    print("Allowed files:", ", ".join(allowed_files))
    print("Protected files:", ", ".join(protected_files))


def main():
    changes = find_changed_decisions()

    if len(changes) == 0:
        print("No decision changes found.")

    elif len(changes) > 1:
        print(
            "More than one decision changed. "
            "Review one decision at a time."
        )

    else:
        create_contract(changes[0])


if __name__ == "__main__":
    main()