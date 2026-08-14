from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent

SRC_DIR = PROJECT_ROOT / "src"
CONFIG_DIR = PROJECT_ROOT / "config"
WORKSPACE_DIR = PROJECT_ROOT / "workspace"
RUNTIME_DIR = PROJECT_ROOT / "runtime"

DEPENDENCIES_PATH = CONFIG_DIR / "dependencies.json"

PLAN_PATH = WORKSPACE_DIR / "plan.md"
JOB_TARGETS_PATH = WORKSPACE_DIR / "job_targets.md"
RELOCATION_NOTES_PATH = WORKSPACE_DIR / "relocation_notes.md"
RESUME_STRATEGY_PATH = WORKSPACE_DIR / "resume_strategy.md"
WEEKLY_ACTIONS_PATH = WORKSPACE_DIR / "weekly_actions.md"

CONTRACT_PATH = RUNTIME_DIR / "mutation_contract.json"
PROPOSAL_PATH = RUNTIME_DIR / "proposal.json"
VALIDATION_REPORT_PATH = RUNTIME_DIR / "validation_report.json"
EVALUATION_RESULTS_PATH = RUNTIME_DIR / "evaluation_results.json"
AUDIT_LOG_PATH = RUNTIME_DIR / "audit_log.jsonl"

WORKSPACE_FILES = {
    "job_targets.md",
    "relocation_notes.md",
    "resume_strategy.md",
    "weekly_actions.md"
}


def ensure_runtime_directory():
    RUNTIME_DIR.mkdir(exist_ok=True)