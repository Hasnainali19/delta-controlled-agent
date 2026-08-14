import hashlib
import json
import subprocess
from datetime import datetime, timezone


def load_json(file_name):
    with open(file_name, "r") as file:
        return json.load(file)


contract = load_json("mutation_contract.json")
proposal = load_json("proposal.json")
validation = load_json("validation_report.json")

files_to_audit = ["plan.md"] + contract["allowed_files"]

result = subprocess.run(
    ["git", "diff", "--"] + files_to_audit,
    capture_output=True,
    text=True
)

git_diff = result.stdout

record = {
    "timestamp_utc": datetime.now(timezone.utc).isoformat(),
    "decision_id": contract["decision_id"],
    "status": contract["status"],
    "allowed_files": contract["allowed_files"],
    "protected_files": contract["protected_files"],
    "proposal_summary": proposal["summary"],
    "validation_passed": validation["passed"],
    "changed_files": [update["file_name"] for update in proposal["updates"]],
    "git_diff_sha256": hashlib.sha256(
        git_diff.encode("utf-8")
    ).hexdigest()
}

with open("audit_log.jsonl", "a") as file:
    file.write(json.dumps(record) + "\n")

print("Audit record saved to audit_log.jsonl")
print("Diff hash:", record["git_diff_sha256"])