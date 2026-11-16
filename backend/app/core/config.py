import os
from pathlib import Path

# Base Paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent
WORKSPACE_DIR = BASE_DIR.parent
TASK_KIT_DIR = WORKSPACE_DIR / "Cantill_FullStack_Task_Kit"

# Fallback to local data dir if task kit isn't directly above
DATA_DIR = TASK_KIT_DIR if TASK_KIT_DIR.exists() else (BASE_DIR / "data")
MASTER_DATA_DIR = DATA_DIR / "master_data"
CONTRACTS_DIR = DATA_DIR / "contracts"
PDF_CONTRACTS_DIR = CONTRACTS_DIR / "pdf"
PR_BATCHES_DIR = DATA_DIR / "pr_batches"

POLICIES_DIR = BASE_DIR / "policies"
POLICIES_DIR.mkdir(exist_ok=True, parents=True)

# App Settings
APP_TITLE = "Corvo Engineering - Procurement Decision Engine"
APP_VERSION = "1.0.0"
DEFAULT_POLICY_VERSION = "5.0"
