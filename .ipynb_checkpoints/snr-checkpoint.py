#!/usr/bin/env python3

import os
import csv
import sys
import time
import numpy as np

from scipy.ndimage import label
from datetime import datetime, timedelta
from skyfield.api import load, wgs84, utc

sys.path.append(os.path.abspath('./starlink-grpc-tools'))
import starlink_grpc

dish_id="test"
exp_round=1


def capture_snr_data(duration_seconds, interval_seconds, context):
    snapshots = []
    end_time = time.time() + duration_seconds

    while time.time() < end_time:
        try:
            snr_data = starlink_grpc.obstruction_map(context)
            snr_data_array = np.array(snr_data, dtype=int)
            snr_data_array[snr_data_array == -1] = 0
            snapshots.append(snr_data_array)
            time.sleep(interval_seconds)
        except starlink_grpc.GrpcError as e:
            print("Failed getting obstruction map data:", str(e))
            break

    return snapshots


def save_white_pixel_coordinates_xor(snapshots, start_time):
    start_time_dt = datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")
    previous_snr_data = np.zeros_like(snapshots[0][1])
    white_pixel_coords = []

    with open('white_pixel_coordinates_xor-{}.csv'.format(dish_id), 'a', newline='') as csvfile:
        writer = csv.writer(csvfile)
        i = 0
        hold_coord = None  # Initialize as None

        for snr_data in snapshots:
            xor_snr_data = np.bitwise_xor(previous_snr_data, snr_data)
            coords = np.argwhere(xor_snr_data == 1)

            if coords.size > 0:
                coord = coords[-1]  # Get the last occurrence
                hold_coord = coord  # Update hold_coord
            elif hold_coord is not None:
                coord = hold_coord  # Use the previous hold_coord if coords is empty
            else:
                continue  # If both coords is empty and hold_coord is None, skip this iteration

            white_pixel_coords.append((start_time_dt + timedelta(seconds=i), tuple(coord)))
            previous_snr_data = snr_data
            i += 1

        for coord in white_pixel_coords:
            writer.writerow([coord[0].strftime("%Y-%m-%d %H:%M:%S"), coord[1][0], coord[1][1]])


def wait_until_target_time():
    target_seconds = {12, 27, 42, 57}
    while True:
        current_second = datetime.utcnow().second
        if current_second in target_seconds:
            break
        time.sleep(0.5)


def load_satellites():
    stations_url = 'https://celestrak.org/NORAD/elements/gp.php?GROUP=starlink&FORMAT=tle'
    satellites = load.tle_file(stations_url)
    print('Loaded', len(satellites), 'satellites')
    return satellites


def main():
    load_satellites()

    context = starlink_grpc.ChannelContext(target="192.168.100.1:9200")

    all_snapshots = []
    start_times = []
    end_times = []

    for i in range(exp_round):
        print("Round {}/{}".format(i, exp_round))
        wait_until_target_time()
        starlink_grpc.reset_obstruction_map(context)
        duration_seconds = 14
        interval_seconds = 1  # Capture a snapshot every 1 second

        S = datetime.utcnow()
        start_time= S.strftime("%Y-%m-%d %H:%M:%S")
        snapshots = capture_snr_data(duration_seconds, interval_seconds, context)

        end_time = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

        all_snapshots.append(snapshots)
        start_times.append(start_time)
        end_times.append(end_time)

        save_white_pixel_coordinates_xor(snapshots, start_time)


if __name__ == "__main__":
    main()