import json
from pathlib import Path

from ollama import chat
from pydantic import BaseModel


class FileUpdate(BaseModel):
    file_name: str
    original_text: str
    replacement_text: str
    reason: str


class PatchProposal(BaseModel):
    summary: str
    updates: list[FileUpdate]


with open("mutation_contract.json", "r") as file:
    contract = json.load(file)

allowed_files = contract["allowed_files"]

allowed_file_contents = {}

for file_name in allowed_files:
    allowed_file_contents[file_name] = Path(file_name).read_text(
        encoding="utf-8"
    )

schema = PatchProposal.model_json_schema()

system_prompt = """
You are a controlled change-proposal agent.

You do not edit files. You only propose changes.

Rules:
- Propose changes only in allowed_files.
- Never mention or propose edits to protected files.
- Keep changes minimal and directly connected to the decision change.
- original_text must exactly match text from the supplied file content.
- Return an empty updates list if no update is needed.
"""

user_prompt = f"""
Mutation contract:
{json.dumps(contract, indent=2)}

Allowed file contents:
{json.dumps(allowed_file_contents, indent=2)}

Return data that follows this JSON schema:
{json.dumps(schema, indent=2)}
"""

response = chat(
    model="qwen2.5:1.5b",
    messages=[
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ],
    format=schema,
    options={"temperature": 0}
)

proposal = PatchProposal.model_validate_json(response.message.content)

with open("proposal.json", "w") as file:
    file.write(proposal.model_dump_json(indent=2))

print("\nProposal created: proposal.json")
print("Summary:", proposal.summary)

for update in proposal.updates:
    print(f"\nProposed file: {update.file_name}")
    print("Reason:", update.reason)
    print("Replace:", update.original_text)
    print("With:", update.replacement_text)