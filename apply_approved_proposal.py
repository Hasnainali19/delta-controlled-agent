import json
from pathlib import Path


def load_json(file_name):
    with open(file_name, "r") as file:
        return json.load(file)


contract = load_json("mutation_contract.json")
proposal = load_json("proposal.json")
validation = load_json("validation_report.json")

if not validation["passed"]:
    print("Application blocked: validation did not pass.")
    raise SystemExit(1)

if contract["human_approval_required"] is not True:
    print("Application blocked: human approval is required.")
    raise SystemExit(1)

print("\nProposed changes:")

for update in proposal["updates"]:
    print(f"\nFile: {update['file_name']}")
    print(f"Replace: {update['original_text']}")
    print(f"With:    {update['replacement_text']}")
    print(f"Reason:  {update['reason']}")

approval = input("\nType APPROVE to apply these changes: ")

if approval != "APPROVE":
    print("No changes were applied.")
    raise SystemExit(0)

for update in proposal["updates"]:
    file_name = update["file_name"]
    original_text = update["original_text"]
    replacement_text = update["replacement_text"]

    if file_name not in contract["allowed_files"]:
        print(f"Blocked: {file_name} is not allowed.")
        raise SystemExit(1)

    path = Path(file_name)
    content = path.read_text(encoding="utf-8")

    if content.count(original_text) != 1:
        print(
            f"Blocked: expected to find the original text exactly once "
            f"in {file_name}."
        )
        raise SystemExit(1)

    updated_content = content.replace(
        original_text,
        replacement_text,
        1
    )

    path.write_text(updated_content, encoding="utf-8")

contract["status"] = "approved_and_applied"

with open("mutation_contract.json", "w") as file:
    json.dump(contract, file, indent=2)

print("\nApproved changes applied successfully.")
print("Run 'git diff' to review the final file changes.")