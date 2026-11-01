# settings.py

from pathlib import Path

# ============================================================================
# APPLICATION
# ============================================================================

APP_NAME = "Windows Update Manager"

APP_VERSION = "1.0.0"

COMPANY_NAME = "SODTECH"

# ============================================================================
# DOSSIERS
# ============================================================================

BASE_DIR = Path(__file__).resolve().parent

LOG_DIR = BASE_DIR / "logs"

REPORT_DIR = BASE_DIR / "reports"
