import matplotlib.pyplot as plt
import numpy as np
import math
import time as tm
from fastdtw import fastdtw
from scipy.spatial.distance import euclidean
from skyfield.api import Topos, load
import starlink_grpc

def polar_to_cartesian(r, theta):
    x = r * np.cos(theta)
    y = r * np.sin(theta)
    return np.array([x, y])

def cartesian_to_polar(x, y):
    r = math.sqrt(x**2 + y**2)
    theta = math.atan2(y, x)
    if theta < 0:
        theta += 2 * math.pi
    return r, theta

def diff(array1, array2):
    difference = []
    for i in range(len(array1)):
        for j in range(len(array1[0])):
            if array1[i][j] != array2[i][j]:
                y = 62 - i
                x = j - 62
                r, theta = cartesian_to_polar(y, x)
                difference.append((r, theta))
    return difference

def get_snr_data(current_time):
    context = starlink_grpc.ChannelContext()
    starlink_grpc.reset_obstruction_map(context)
    tm.sleep(1)
    snr_data = starlink_grpc.obstruction_map(context)
    return snr_data

def main():
    stations_url = 'https://celestrak.org/NORAD/elements/gp.php?GROUP=starlink&FORMAT=tle'
    satellites = load.tle_file(stations_url)
    print('Loaded', len(satellites), 'satellites')
    # satellites = load.tle_file(tle_file)
    context = starlink_grpc.ChannelContext()

    location = starlink_grpc.get_location(context)
    my_location = Topos(location.lla.lat, location.lla.lon, elevation_m=location.lla.alt)

    ts = load.timescale()

    snr_data_array = []
    timeline = []

    while True:
        current_time = tm.localtime()
        if current_time.tm_sec % 15 == 0:
            t = ts.now()
            snr_data = get_snr_data(current_time)
            print("SNR data collected at UTC time:", t.utc_datetime())  # Print the UTC time
            timeline.append(t)
            snr_data_array.append(snr_data)

            if len(snr_data_array) >= 2:
                measure_trace = diff(snr_data_array[-2], snr_data_array[-1])

                fig, ax0 = plt.subplots(subplot_kw={'polar': True}, figsize=(6, 6))

                ax0.set_theta_zero_location("N")
                ax0.set_theta_direction(-1)
                ax0.set_rlim(90, 0)
                ax0.grid(True)

                measure_trace = np.array(measure_trace)
                ax0.scatter(measure_trace[0, 1], 90 - measure_trace[0, 0], label="measure_trace")

                ax0.set_title('SNR Difference')
                ax0.legend(loc='upper right')

                plt.show()

                break  # Exit after the first plot

        tm.sleep(1)

if __name__ == "__main__":
    main()
