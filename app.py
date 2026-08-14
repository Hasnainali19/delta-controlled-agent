import json
import subprocess
import sys
from pathlib import Path

import streamlit as st

from src.paths import (
    AUDIT_LOG_PATH,
    CONTRACT_PATH,
    EVALUATION_RESULTS_PATH,
    PLAN_PATH,
    PROJECT_ROOT,
    PROPOSAL_PATH,
    SRC_DIR,
    VALIDATION_REPORT_PATH
)


st.set_page_config(
    page_title="Delta-Controlled Agent",
    page_icon="🔒",
    layout="wide"
)


def load_json(path):
    if not path.exists():
        return None

    return json.loads(path.read_text(encoding="utf-8"))


def run_script(script_name, user_input=None):
    result = subprocess.run(
        [sys.executable, str(SRC_DIR / script_name)],
        cwd=PROJECT_ROOT,
        input=user_input,
        capture_output=True,
        text=True
    )

    st.session_state["last_output"] = (
        result.stdout + result.stderr
    )

    st.session_state["last_success"] = (
        result.returncode == 0
    )


def show_last_output():
    if "last_output" not in st.session_state:
        return

    if st.session_state["last_success"]:
        st.success("Command completed.")
    else:
        st.error("Command stopped with an error.")

    st.code(
        st.session_state["last_output"] or "No terminal output",
        language="text"
    )


st.title("🔒 Delta-Controlled Agent")
st.caption(
    "A human-in-the-loop system that converts a plan decision "
    "into a dependency-scoped, validated, reviewable update."
)

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

    show_last_output()


tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "Plan",
    "Mutation Contract",
    "AI Proposal",
    "Validation & Audit",
    "Evaluations"
])


with tab1:
    st.subheader("Source plan")

    current_plan = PLAN_PATH.read_text(encoding="utf-8")

    edited_plan = st.text_area(
        "Edit one decision, save it, then create a contract.",
        value=current_plan,
        height=320
    )

    if st.button("Save plan"):
        PLAN_PATH.write_text(
            edited_plan,
            encoding="utf-8"
        )
        st.success("Plan saved. No agent changes were applied.")


with tab2:
    st.subheader("Mutation contract")

    contract = load_json(CONTRACT_PATH)

    if contract:
        unlocked, locked = st.columns(2)

        with unlocked:
            st.success("Unlocked files")
            st.write(contract["allowed_files"])

        with locked:
            st.error("Protected files")
            st.write(contract["protected_files"])

        st.json(contract)
    else:
        st.info("Create a mutation contract to view it here.")


with tab3:
    st.subheader("AI patch proposal")

    proposal = load_json(PROPOSAL_PATH)

    if proposal:
        st.write(proposal["summary"])

        for update in proposal["updates"]:
            st.markdown(f"### {update['file_name']}")
            st.write(f"**Reason:** {update['reason']}")

            before, after = st.columns(2)

            with before:
                st.error("Exact source text")
                st.code(update["original_text"])

            with after:
                st.success("Proposed replacement")
                st.code(update["replacement_text"])
    else:
        st.info("Generate a proposal to view it here.")


with tab4:
    st.subheader("Validation and audit trail")

    validation = load_json(VALIDATION_REPORT_PATH)

    if validation:
        if validation["passed"]:
            st.success("Validation passed")
        else:
            st.error("Validation failed")

        st.json(validation)
    else:
        st.info("No validation report exists yet.")

    if AUDIT_LOG_PATH.exists():
        audit_events = [
            json.loads(line)
            for line in AUDIT_LOG_PATH.read_text(
                encoding="utf-8"
            ).splitlines()
            if line.strip()
        ]

        st.subheader("Audit events")
        st.dataframe(audit_events, use_container_width=True)


with tab5:
    st.subheader("Guardrail evaluation results")

    evaluation_results = load_json(EVALUATION_RESULTS_PATH)

    if evaluation_results:
        st.dataframe(
            evaluation_results,
            use_container_width=True
        )

        passed_tests = sum(
            result["test_passed"]
            for result in evaluation_results
        )

        st.metric(
            "Tests passed",
            f"{passed_tests}/{len(evaluation_results)}"
        )
    else:
        st.info("Run evaluations to show results.")