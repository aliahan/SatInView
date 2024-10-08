import logging
import logging
import subprocess
import threading
import schedule

from config import DATA_DIR, STARLINK_GRPC_ADDR_PORT
from util import date_time_string, ensure_data_directory

logger = logging.getLogger(__name__)


GRPC_DATA_DIR = "{}/grpc".format(DATA_DIR)
GRPC_TIMEOUT = 10


def grpc_get_status() -> None:
    name = "grpcGetStatus"
    logger.info("{}, {}".format(name, threading.current_thread()))

    FILENAME = "{}/{}/GetStatus-{}.txt".format(GRPC_DATA_DIR, ensure_data_directory(GRPC_DATA_DIR), date_time_string())

    # grpcurl -plaintext -d {\"get_status\":{}} 192.168.100.1:9200 SpaceX.API.Device.Device/Handle
    cmd = ["grpcurl", "-plaintext", "-d", "{\"get_status\":{}}", STARLINK_GRPC_ADDR_PORT, "SpaceX.API.Device.Device/Handle"]
    try:
        with open(FILENAME, "w") as outfile:
            subprocess.run(cmd, stdout=outfile, timeout=GRPC_TIMEOUT)
    except subprocess.TimeoutExpired:
        pass

    logger.info("[{}] Next scheduled run at {}".format(name, schedule.next_run()))
