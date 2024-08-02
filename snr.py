#!/usr/bin/env python3

import os
import csv
import sys
import time
import numpy as np
import matplotlib.pyplot as plt

from scipy.ndimage import label
from datetime import datetime, timedelta
from skyfield.api import load, wgs84, utc

sys.path.append(os.path.abspath('./starlink-grpc-tools'))
import starlink_grpc


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


def save_white_pixel_coordinates(snapshots, start_time):
    white_pixel_coords = set()  # Use a set to store unique coordinates
    for snr_data in snapshots:
        coords = np.argwhere(snr_data == 1)
        for coord in coords:
            white_pixel_coords.add(tuple(coord))  # Add each coordinate as a tuple to the set

    with open('white_pixel_coordinates.txt', 'a') as f:
        f.write(f"{start_time}:\n")
        for coord in sorted(white_pixel_coords):  # Sort coordinates for consistency
            f.write(f"{coord}\n")
        f.write("\n")


def plot_snr_traces(all_snapshots, start_times, end_times, r):
    plt.figure(figsize=(30, 40))  # Increase the figure size for better resolution
    for i, (snapshots, start_time, end_time) in enumerate(zip(all_snapshots, start_times, end_times)):
        base_image = np.zeros_like(snapshots[0])
        for snr_data in snapshots:
            base_image = np.maximum(base_image, snr_data)

        plt.subplot(r//2+1, 2, i + 1)  # Arrange plots in a grid
        plt.imshow(base_image, cmap='gray', origin='lower')
        plt.title(f'Interval {i+1}\n{start_time} to {end_time} UTC')
        plt.axis('off')

    plt.suptitle('Starlink Obstruction Map Traces (15 intervals of 14 seconds each)')
    plt.tight_layout(rect=[0, 0.03, 1, 0.95])  # Adjust layout for the main title
    plt.savefig('trajectory2.png')
    plt.show()


def save_white_pixel_coordinates_xor(snapshots, start_time):
    # Parse start_time back to a datetime object
    start_time_dt = datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")
    previous_snr_data = np.zeros_like(snapshots[0][1])
    white_pixel_coords = []

    with open('white_pixel_coordinates_xor.csv', 'a', newline='') as csvfile:
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

            # Add the timedelta to start_time_dt
            white_pixel_coords.append((start_time_dt + timedelta(seconds=i), tuple(coord)))
            previous_snr_data = snr_data
            i += 1

        for coord in white_pixel_coords:
            writer.writerow([coord[0].strftime("%Y-%m-%d %H:%M:%S"), coord[1][0], coord[1][1]])


def filter_unconnected_white_pixels(snapshots):
    final_snapshot = snapshots[-1]
    labeled_array, num_features = label(final_snapshot)
    connected_pixels = set()

    for i in range(1, num_features + 1):
        coords = np.argwhere(labeled_array == i)
        if len(coords) > 1:  # More than one pixel in the component
            for coord in coords:
                connected_pixels.add(tuple(coord))

    filtered_snapshot = np.zeros_like(final_snapshot)
    for coord in connected_pixels:
        filtered_snapshot[coord] = 1

    snapshots[-1] = filtered_snapshot
    return snapshots


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

    # Initialize the gRPC context
    context = starlink_grpc.ChannelContext(target="192.168.100.1:9200")

    all_snapshots = []
    start_times = []
    end_times = []
    r = 500

    for i in range(r):
        print("Round {}/{}".format(i, r))
        wait_until_target_time()
        starlink_grpc.reset_obstruction_map(context)
        duration_seconds = 14
        interval_seconds = 1  # Capture a snapshot every 1 second

        S = datetime.utcnow() - timedelta(seconds=1)
        start_time= S.strftime("%Y-%m-%d %H:%M:%S")
        snapshots = capture_snr_data(duration_seconds, interval_seconds, context)

        # Filter unconnected white pixels in the last snapshot
        # snapshots = filter_unconnected_white_pixels(snapshots)

        end_time = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

        all_snapshots.append(snapshots)
        start_times.append(start_time)
        end_times.append(end_time)

        # Save white pixel coordinates to a file
        # save_white_pixel_coordinates(snapshots, start_time)

        # Save white pixel coordinates with XOR to a CSV file
        save_white_pixel_coordinates_xor(snapshots, start_time)

    # Plot all the traces
    # plot_snr_traces(all_snapshots, start_times, end_times, r)


if __name__ == "__main__":
    main()
