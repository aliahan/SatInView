import ipaddress
import logging
import time

import schedule

from config import ENABLE_IRTT
from latency import irtt_ping, icmp_ping
from satellite import load_satellites, collect_obstruction_data
from dish import grpc_get_status
from util import run

logger = logging.getLogger(__name__)


if ENABLE_IRTT:
    schedule.every(1).hours.at(":00").do(run, irtt_ping).tag("Latency")

schedule.every(1).hours.at(":00").do(run, icmp_ping).tag("Latency")
schedule.every(1).hours.at(":00").do(run, grpc_get_status).tag("gRPC")
schedule.every(6).hours.at(":00").do(run, load_satellites).tag("TLE")
schedule.every(1).hours.at(":00").do(run, collect_obstruction_data).tag("TLE")


if __name__ == "__main__":
    for job in schedule.get_jobs("Latency"):
        logger.info("[Latency]: {}".format(job.next_run))
    for job in schedule.get_jobs("TLE"):
        logger.info("[TLE]: {}".format(job.next_run))
    for job in schedule.get_jobs("gRPC"):
        logger.info("[gRPC]: {}".format(job.next_run))

    while True:
        schedule.run_pending()
        time.sleep(0.5)
