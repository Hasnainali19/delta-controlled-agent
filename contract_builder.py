import json
import sys

WORKSPACE_FILES = {
    "job_targets.md",
    "weekly_actions.md",
    "relocation_notes.md",
    "resume_strategy.md"
}


def load_dependencies():
    with open("dependencies.json", "r") as file:
        return json.load(file)


def build_contract(decision_id):
    dependencies = load_dependencies()

    if decision_id not in dependencies:
        print("Unknown decision ID.")
        return

    allowed_files = dependencies[decision_id]
    protected_files = list(WORKSPACE_FILES - set(allowed_files))

    contract = {
        "decision_id": decision_id,
        "allowed_files": allowed_files,
        "protected_files": protected_files,
        "maximum_files_changed": len(allowed_files),
        "human_approval_required": True,
        "status": "proposed"
    }

    with open("mutation_contract.json", "w") as file:
        json.dump(contract, file, indent=4)

    print("\nMutation contract created: mutation_contract.json")


if len(sys.argv) != 2:
    print("Usage: python contract_builder.py DEC-001")
else:
    build_contract(sys.argv[1])