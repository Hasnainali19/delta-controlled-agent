import json
from pathlib import Path


def load_json(file_name):
    with open(file_name, "r") as file:
        return json.load(file)


contract = load_json("mutation_contract.json")
proposal = load_json("proposal.json")

allowed_files = set(contract["allowed_files"])
protected_files = set(contract["protected_files"])
maximum_files = contract["maximum_files_changed"]

errors = []
warnings = []

updates = proposal["updates"]
proposed_file_names = {update["file_name"] for update in updates}

if len(proposed_file_names) > maximum_files:
    errors.append(
        f"Proposal changes {len(proposed_file_names)} files, "
        f"but the limit is {maximum_files}."
    )

if len(updates) == 0:
    warnings.append("The model proposed no updates.")

for update in updates:
    file_name = update["file_name"]
    original_text = update["original_text"]
    replacement_text = update["replacement_text"]

    if not original_text.strip():
        errors.append(
            f"{file_name} has empty original text. "
            "A patch must replace real existing text."
        )

    if not replacement_text.strip():
        errors.append(
            f"{file_name} has empty replacement text."
        )

    if file_name not in allowed_files:
        errors.append(f"{file_name} is not an allowed file.")

    if file_name in protected_files:
        errors.append(f"{file_name} is protected and must stay locked.")

    if not Path(file_name).exists():
        errors.append(f"{file_name} does not exist.")
        continue

    file_content = Path(file_name).read_text(encoding="utf-8")

    if original_text not in file_content:
        errors.append(
            f"The original text for {file_name} was not found exactly "
            "in the real file."
        )

    if original_text == replacement_text:
        errors.append(
            f"{file_name} has identical original and replacement text."
        )

report = {
    "passed": len(errors) == 0,
    "decision_id": contract["decision_id"],
    "checked_files": sorted(proposed_file_names),
    "errors": errors,
    "warnings": warnings
}

with open("validation_report.json", "w") as file:
    json.dump(report, file, indent=2)

if report["passed"]:
    print("\nValidation passed.")
    print("The proposal stayed inside the permitted scope.")
else:
    print("\nValidation failed.")
    for error in errors:
        print("-", error)

if warnings:
    print("\nWarnings:")
    for warning in warnings:
        print("-", warning)