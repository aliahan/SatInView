import logging
import threading
from datetime import datetime, timezone
from pathlib import Path
from shutil import which

from config import DATA_DIR

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] [%(levelname)s] %(message)s')


def date_time_string() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d-%H-%M-%S")


def ensure_directory(name: str):
    return Path(name).mkdir(parents=True, exist_ok=True)


def ensure_data_directory(directory: str) -> str:
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    ensure_directory(str(Path(directory).joinpath(today)))
    return today


def test_command(command: str) -> bool:
    return which(command) is not None


def failed(e: str) -> None:
    with open("{}/failed.txt".format(DATA_DIR), "a+") as f:
        f.write("{}: {}\n".format(date_time_string(), e))


def run(func):
    job_thread = threading.Thread(target=func)
    job_thread.start()
