# settings.py

from pathlib import Path

# ============================================================================
# APPLICATION
# ============================================================================

APP_NAME = "Windows Update Manager"

APP_VERSION = "1.0.0"

COMPANY_NAME = "SODTECH"

MAX_WORKERS = 5

# ============================================================================
# DOSSIERS
# ============================================================================

BASE_DIR = Path(__file__).resolve().parent

LOG_DIR = BASE_DIR / "logs"

LOG_FILE = LOG_DIR / "windows_update_manager.log"

LOG_LEVEL = "INFO"

LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"

LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

REPORT_DIR = BASE_DIR / "reports"
