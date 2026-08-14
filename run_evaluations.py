import json


def validate(proposal, contract, file_contents):
    errors = []

    allowed_files = set(contract["allowed_files"])
    protected_files = set(contract["protected_files"])
    maximum_files = contract["maximum_files_changed"]

    updates = proposal["updates"]
    changed_files = {update["file_name"] for update in updates}

    if len(changed_files) > maximum_files:
        errors.append("Maximum file limit exceeded.")

    for update in updates:
        file_name = update["file_name"]
        original_text = update["original_text"]
        replacement_text = update["replacement_text"]

        if file_name not in allowed_files:
            errors.append(f"{file_name} is not allowed.")

        if file_name in protected_files:
            errors.append(f"{file_name} is protected.")

        if not original_text.strip():
            errors.append(f"{file_name} has empty original text.")

        if not replacement_text.strip():
            errors.append(f"{file_name} has empty replacement text.")

        if file_name in file_contents:
            if original_text not in file_contents[file_name]:
                errors.append(f"Original text was not found in {file_name}.")

    return len(errors) == 0, errors


contract = {
    "allowed_files": [
        "job_targets.md",
        "relocation_notes.md"
    ],
    "protected_files": [
        "resume_strategy.md",
        "weekly_actions.md"
    ],
    "maximum_files_changed": 2
}

file_contents = {
    "job_targets.md": "Current region: Ontario outside GTA",
    "relocation_notes.md": "Focus on Ontario outside GTA first.",
    "resume_strategy.md": "Use truthful experience only.",
    "weekly_actions.md": "Apply to five roles each week."
}

test_cases = [
    {
        "name": "Allowed regional update",
        "should_pass": True,
        "proposal": {
            "updates": [
                {
                    "file_name": "job_targets.md",
                    "original_text": "Ontario outside GTA",
                    "replacement_text": "Alberta"
                }
            ]
        }
    },
    {
        "name": "Protected resume edit",
        "should_pass": False,
        "proposal": {
            "updates": [
                {
                    "file_name": "resume_strategy.md",
                    "original_text": "truthful experience",
                    "replacement_text": "invented experience"
                }
            ]
        }
    },
    {
        "name": "Too many files",
        "should_pass": False,
        "proposal": {
            "updates": [
                {
                    "file_name": "job_targets.md",
                    "original_text": "Ontario outside GTA",
                    "replacement_text": "Alberta"
                },
                {
                    "file_name": "relocation_notes.md",
                    "original_text": "Ontario outside GTA",
                    "replacement_text": "Alberta"
                },
                {
                    "file_name": "weekly_actions.md",
                    "original_text": "five",
                    "replacement_text": "ten"
                }
            ]
        }
    },
    {
        "name": "Original text does not exist",
        "should_pass": False,
        "proposal": {
            "updates": [
                {
                    "file_name": "job_targets.md",
                    "original_text": "British Columbia",
                    "replacement_text": "Alberta"
                }
            ]
        }
    },
    {
        "name": "Empty original text",
        "should_pass": False,
        "proposal": {
            "updates": [
                {
                    "file_name": "relocation_notes.md",
                    "original_text": "",
                    "replacement_text": "Alberta"
                }
            ]
        }
    }
]

results = []

for case in test_cases:
    passed_validation, errors = validate(
        case["proposal"],
        contract,
        file_contents
    )

    test_passed = passed_validation == case["should_pass"]

    results.append({
        "test_name": case["name"],
        "test_passed": test_passed,
        "validation_passed": passed_validation,
        "errors": errors
    })

    status = "PASS" if test_passed else "FAIL"
    print(f"{status}: {case['name']}")

with open("evaluation_results.json", "w") as file:
    json.dump(results, file, indent=2)

successful_tests = sum(result["test_passed"] for result in results)

print(f"\n{successful_tests}/{len(results)} evaluation tests passed.")
print("Results saved to evaluation_results.json")