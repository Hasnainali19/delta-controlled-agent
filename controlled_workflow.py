import json
import re
import subprocess

WORKSPACE_FILES = {
    "job_targets.md",
    "weekly_actions.md",
    "relocation_notes.md",
    "resume_strategy.md"
}


def get_previous_plan():
    result = subprocess.run(
        ["git", "show", "HEAD:plan.md"],
        capture_output=True,
        text=True
    )
    return result.stdout


def get_current_plan():
    with open("plan.md", "r") as file:
        return file.read()


def extract_decisions(plan_text):
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
    old_decisions = extract_decisions(get_previous_plan())
    new_decisions = extract_decisions(get_current_plan())

    changed = []

    for decision_id, new_value in new_decisions.items():
        old_value = old_decisions.get(decision_id)

        if old_value != new_value:
            changed.append({
                "decision_id": decision_id,
                "before": old_value,
                "after": new_value
            })

    return changed


def create_contract(change):
    with open("dependencies.json", "r") as file:
        dependencies = json.load(file)

    decision_id = change["decision_id"]

    if decision_id not in dependencies:
        print(f"No dependency rule exists for {decision_id}.")
        return

    allowed_files = dependencies[decision_id]
    protected_files = sorted(WORKSPACE_FILES - set(allowed_files))

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

    with open("mutation_contract.json", "w") as file:
        json.dump(contract, file, indent=4)

    print(f"\nContract created for {decision_id}")
    print("Allowed files:", ", ".join(allowed_files))
    print("Protected files:", ", ".join(protected_files))


changes = find_changed_decisions()

if len(changes) == 0:
    print("No decision changes found.")

elif len(changes) > 1:
    print("More than one decision changed. Review each change separately.")

else:
    create_contract(changes[0])