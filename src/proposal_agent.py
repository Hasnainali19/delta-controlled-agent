import json
from pathlib import Path

from ollama import chat
from pydantic import BaseModel

from paths import (
    CONTRACT_PATH,
    PROPOSAL_PATH,
    WORKSPACE_DIR,
    ensure_runtime_directory
)


MODEL_NAME = "qwen2.5:1.5b"


class TargetSelection(BaseModel):
    target_id: str
    replacement_text: str
    reason: str


class AnchoredProposal(BaseModel):
    summary: str
    updates: list[TargetSelection]


def safe_workspace_path(file_name):
    path = Path(file_name)

    if path.name != file_name:
        raise ValueError("Invalid workspace filename.")

    return WORKSPACE_DIR / file_name


def build_targets(contract):
    """
    Create deterministic editable targets from non-empty workspace lines.
    The model chooses an ID; it never reproduces original source text.
    """

    targets = {}

    for file_name in contract["allowed_files"]:
        path = safe_workspace_path(file_name)
        lines = path.read_text(encoding="utf-8").splitlines()

        for line_number, line in enumerate(lines, start=1):
            if line.strip():
                target_id = f"{file_name}#L{line_number}"

                targets[target_id] = {
                    "file_name": file_name,
                    "original_text": line
                }

    return targets


def generate_anchored_proposal(contract, targets):
    schema = AnchoredProposal.model_json_schema()

    available_targets = [
        {
            "target_id": target_id,
            "file_name": target["file_name"],
            "current_text": target["original_text"]
        }
        for target_id, target in targets.items()
    ]

    system_prompt = """
You are a controlled change-proposal agent.

You never edit files directly.

Rules:
1. Select target_id values only from available_targets.
2. Do not reproduce original text.
3. Propose only a replacement_text for the selected target.
4. Keep updates directly related to the decision change.
5. Return an empty updates list if no target needs updating.
"""

    user_prompt = f"""
Mutation contract:
{json.dumps(contract, indent=2)}

Available editable targets:
{json.dumps(available_targets, indent=2)}

Return data following this JSON schema:
{json.dumps(schema, indent=2)}
"""

    response = chat(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        format=schema,
        options={"temperature": 0}
    )

    return AnchoredProposal.model_validate_json(
        response.message.content
    )


def build_patch_proposal(anchored_proposal, targets):
    """Convert model-selected IDs into exact deterministic replacements."""

    updates = []

    for update in anchored_proposal.updates:
        if update.target_id not in targets:
            raise ValueError(
                f"Model selected an invalid target: {update.target_id}"
            )

        target = targets[update.target_id]

        replacement_text = update.replacement_text.strip()

        if not replacement_text:
            raise ValueError(
                f"Model proposed empty replacement text for {update.target_id}"
            )

        if replacement_text == target["original_text"]:
            continue

        updates.append({
            "file_name": target["file_name"],
            "original_text": target["original_text"],
            "replacement_text": replacement_text,
            "reason": update.reason
        })

    return {
        "summary": anchored_proposal.summary,
        "updates": updates
    }


def main():
    if not CONTRACT_PATH.exists():
        raise FileNotFoundError(
            "Run controlled_workflow.py first."
        )

    contract = json.loads(
        CONTRACT_PATH.read_text(encoding="utf-8")
    )

    targets = build_targets(contract)

    if not targets:
        raise ValueError(
            "No non-empty editable targets exist in the allowed files."
        )

    anchored_proposal = generate_anchored_proposal(
        contract,
        targets
    )

    proposal = build_patch_proposal(
        anchored_proposal,
        targets
    )

    ensure_runtime_directory()

    PROPOSAL_PATH.write_text(
        json.dumps(proposal, indent=2),
        encoding="utf-8"
    )

    print("Anchored proposal saved:", PROPOSAL_PATH)
    print("Summary:", proposal["summary"])

    for update in proposal["updates"]:
        print(f"\nProposed file: {update['file_name']}")
        print("Exact source text:", update["original_text"])
        print("Replacement:", update["replacement_text"])


if __name__ == "__main__":
    main()