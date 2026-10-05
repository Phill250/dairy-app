import logging
from pathlib import Path

LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

security_logger = logging.getLogger("security")
security_logger.setLevel(logging.INFO)

if not security_logger.handlers:
    file_handler = logging.FileHandler(LOG_DIR / "security.log")
    console_handler = logging.StreamHandler()
    formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    security_logger.addHandler(file_handler)
    security_logger.addHandler(console_handler)