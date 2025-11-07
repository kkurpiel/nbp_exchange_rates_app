import logging
import os
from datetime import datetime

import logging, os
from datetime import datetime

def init_logger():
    project_root = os.path.dirname(os.path.abspath(__file__))
    log_dir = os.path.join(project_root, "..", "logs")
    os.makedirs(log_dir, exist_ok=True)

    log_path = os.path.join(log_dir, f"{datetime.now():%Y-%m-%d}.log")

    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    console_handler = logging.StreamHandler()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[file_handler, console_handler],
    )
    return logging.getLogger("nbp_app")
