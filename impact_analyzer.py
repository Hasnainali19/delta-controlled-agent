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


def analyze_impact(decision_id):
    dependencies = load_dependencies()

    if decision_id not in dependencies:
        print("Unknown decision ID.")
        return

    allowed_files = set(dependencies[decision_id])
    protected_files = WORKSPACE_FILES - allowed_files

    print(f"\nDecision changed: {decision_id}")

    print("\nAllowed files — unlocked rooms:")
    for file_name in allowed_files:
        print(f"- {file_name}")

    print("\nProtected files — locked rooms:")
    for file_name in protected_files:
        print(f"- {file_name}")


if len(sys.argv) != 2:
    print("Usage: python impact_analyzer.py DEC-001")
else:
    analyze_impact(sys.argv[1])