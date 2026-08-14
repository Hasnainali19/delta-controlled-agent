import subprocess
import re


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
        match = re.match(r"## (DEC-\d+)", line)

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


old_plan = get_previous_plan()
new_plan = get_current_plan()

old_decisions = extract_decisions(old_plan)
new_decisions = extract_decisions(new_plan)

for decision_id in new_decisions:
    if old_decisions.get(decision_id) != new_decisions[decision_id]:
        print(f"\nChanged decision: {decision_id}")
        print(f"Before: {old_decisions.get(decision_id)}")
        print(f"After:  {new_decisions[decision_id]}")