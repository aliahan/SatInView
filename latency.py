import logging
import ipaddress
import subprocess
import threading
from datetime import datetime

import schedule

from config import INTERVAL_MS, INTERVAL_SEC, DURATION, DURATION_SECONDS, IFCE, IRTT_SERVER_PORT, DATA_DIR, IRTT_LOCAL_IP, \
    COUNT, LOCAL_IP, STARLINK_DEFAULT_GW, ENABLE_IRTT
from util import date_time_string, ensure_data_directory, failed

logger = logging.getLogger(__name__)


LATENCY_DATA_DIR = "{}/latency".format(DATA_DIR)


def setup():
    global IRTT_LOCAL_IP

    if ENABLE_IRTT == True:
        ip = ipaddress.ip_address(LOCAL_IP)
        if ip.version == 4:
            IRTT_LOCAL_IP = LOCAL_IP
        elif ip.version == 6:
            IRTT_LOCAL_IP = "[{}]".format(LOCAL_IP)

        logger.info("Local IP: {}".format(LOCAL_IP))
        logger.info("IRTT Local IP: {}".format(IRTT_LOCAL_IP))
        logger.info("IRTT Server: {}".format(IRTT_SERVER_PORT))


def irtt_ping() -> None:
    name = "IRTT_PING"
    print(datetime.now(), "irtt", threading.current_thread())
    setup()

    FILENAME = "{}/{}/irtt-{}-{}-{}.json".format(LATENCY_DATA_DIR, ensure_data_directory(LATENCY_DATA_DIR), INTERVAL_MS, DURATION, date_time_string())
    try:
        output = subprocess.check_output(["irtt", "client", "-6", "-Q", "-i", INTERVAL_MS, "-d", DURATION, "--local={}".format(IRTT_LOCAL_IP), IRTT_SERVER_PORT, "-o", FILENAME])
        if "Error" in output.decode("utf-8"):
            failed(output.decode("utf-8"))
    except Exception as e:
        failed(str(e))

    logger.info("[{}] Next scheduled run at {}".format(name, schedule.next_run()))


def icmp_ping() -> None:
    name = "ICMP_PING"
    logger.info("{}, {}".format(name, threading.current_thread()))

    FILENAME = "{}/{}/ping-{}-{}-{}.txt".format(LATENCY_DATA_DIR, ensure_data_directory(LATENCY_DATA_DIR), INTERVAL_MS, DURATION, date_time_string())

    cmd = ["ping", "-D", "-i", INTERVAL_SEC, "-c", str(COUNT), STARLINK_DEFAULT_GW, "-I", IFCE]
    try:
        with open(FILENAME, "w") as outfile:
            subprocess.run(cmd, stdout=outfile, timeout=DURATION_SECONDS)
    except subprocess.TimeoutExpired:
        pass

    logger.info("[{}] Next scheduled run at {}".format(name, schedule.next_run()))
