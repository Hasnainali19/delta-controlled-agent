import json
import subprocess
import sys
from pathlib import Path

import streamlit as st


st.set_page_config(
    page_title="Delta-Controlled Agent",
    page_icon="Locked ",
    layout="wide"
)


def load_json(file_name):
    path = Path(file_name)

    if not path.exists():
        return None

    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def read_text(file_name):
    path = Path(file_name)

    if not path.exists():
        return ""

    return path.read_text(encoding="utf-8")


def run_script(script_name, user_input=None):
    result = subprocess.run(
        [sys.executable, script_name],
        input=user_input,
        capture_output=True,
        text=True
    )

    output = result.stdout + result.stderr

    if result.returncode == 0:
        st.success(f"{script_name} completed.")
    else:
        st.error(f"{script_name} stopped with an error.")

    st.code(output or "No terminal output", language="text")


st.title("Locked  Delta-Controlled Agent")
st.caption(
    "A human-in-the-loop system that turns one plan edit into a "
    "small, reviewable, dependency-scoped update."
)

contract = load_json("mutation_contract.json")
proposal = load_json("proposal.json")
validation = load_json("validation_report.json")
evaluation_results = load_json("evaluation_results.json")

with st.sidebar:
    st.header("Control panel")

    if st.button("1. Detect change and create contract"):
        run_script("controlled_workflow.py")

    if st.button("2. Generate local AI proposal"):
        run_script("proposal_agent.py")

    if st.button("3. Validate proposal"):
        run_script("validate_proposal.py")

    approved = st.checkbox(
        "I reviewed the proposal and approve the exact changes."
    )

    if st.button(
        "4. Approve and apply proposal",
        disabled=not approved
    ):
        run_script(
            "apply_approved_proposal.py",
            user_input="APPROVE\n"
        )

    if st.button("5. Save audit record"):
        run_script("audit_logger.py")

    if st.button("Run guardrail evaluations"):
        run_script("run_evaluations.py")

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "Plan",
    "Mutation Contract",
    "AI Proposal",
    "Validation & Audit",
    "Evaluations"
])

with tab1:
    st.subheader("Source plan")

    current_plan = read_text("plan.md")

    edited_plan = st.text_area(
        "Edit a decision, then use step 1 in the control panel.",
        value=current_plan,
        height=300
    )

    if st.button("Save plan.md"):
        Path("plan.md").write_text(edited_plan, encoding="utf-8")
        st.success("plan.md saved. The agent has not made any changes yet.")

with tab2:
    st.subheader("The painter's job card")

    if contract:
        left, right = st.columns(2)

        with left:
            st.success("Unlocked rooms")
            st.write(contract["allowed_files"])

        with right:
            st.error("Locked rooms")
            st.write(contract["protected_files"])

        st.json(contract)
    else:
        st.info("Create a mutation contract to view it here.")

with tab3:
    st.subheader("AI patch proposal")

    if proposal:
        st.write(proposal.get("summary", ""))

        for update in proposal.get("updates", []):
            st.markdown(f"### {update['file_name']}")
            st.write(f"**Reason:** {update['reason']}")

            before, after = st.columns(2)

            with before:
                st.error("Before")
                st.code(update["original_text"])

            with after:
                st.success("Proposed replacement")
                st.code(update["replacement_text"])

        st.json(proposal)
    else:
        st.info("Generate a local proposal to view it here.")

with tab4:
    st.subheader("Validation and audit trail")

    if validation:
        if validation["passed"]:
            st.success("Validation passed")
        else:
            st.error("Validation failed")

        st.json(validation)
    else:
        st.info("No validation report yet.")

    audit_path = Path("audit_log.jsonl")

    if audit_path.exists():
        st.subheader("Audit events")

        audit_events = [
            json.loads(line)
            for line in audit_path.read_text(
                encoding="utf-8"
            ).splitlines()
            if line.strip()
        ]

        st.dataframe(audit_events, use_container_width=True)

with tab5:
    st.subheader("Guardrail evaluation results")

    if evaluation_results:
        st.dataframe(evaluation_results, use_container_width=True)

        passed_tests = sum(
            result["test_passed"]
            for result in evaluation_results
        )

        st.metric(
            "Tests passed",
            f"{passed_tests}/{len(evaluation_results)}"
        )
    else:
        st.info("Run the guardrail evaluations to view results.")