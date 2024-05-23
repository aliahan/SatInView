import math
import starlink_grpc
from datetime import datetime
import matplotlib.pyplot as plt
import numpy as np
import time

def calculate_azimuth_elevation(image_width, image_height):
    # Ensure the image is square
    assert image_width == image_height, "Image must be square"
    
    center_x = image_width // 2
    center_y = image_height // 2
    
    azimuth_elevation_map = []

    for y in range(image_height):
        row = []
        for x in range(image_width):
            # Convert pixel (x, y) to Cartesian coordinates with the center as (0, 0)
            dx = x - center_x
            dy = center_y - y  # Adjust dy to invert y-axis

            # Calculate azimuth
            azimuth = (math.degrees(math.atan2(dx, dy)) + 360) % 360
            
            # Calculate elevation
            distance_from_center = math.sqrt(dx**2 + dy**2)
            max_distance = center_x  # max distance in pixels
            elevation = 10 + 80 * (1 - (distance_from_center / max_distance))  # Minimum elevation is 0 degrees

            if distance_from_center > max_distance:
                # Pixels outside the circle represent "no data"
                row.append((None, None))
            else:
                row.append((azimuth, elevation))
        
        azimuth_elevation_map.append(row)
    
    return azimuth_elevation_map

def find_closest_white_pixel(snr_data, azimuth_elevation_map):
    center_x = len(snr_data[0]) // 2
    center_y = len(snr_data) // 2
    closest_distance = float('inf')
    closest_azimuth = None
    closest_elevation = None
    closest_x = None
    closest_y = None

    for y in range(len(snr_data)):
        for x in range(len(snr_data[y])):
            if snr_data[y][x] == 1:  # Check if the pixel is white
                dx = x - center_x
                dy = y - center_y  # Do not invert dy for distance calculation
                distance = math.sqrt(dx**2 + dy**2)

                if distance < closest_distance:
                    closest_distance = distance
                    closest_azimuth, closest_elevation = azimuth_elevation_map[y][x]
                    closest_x = x
                    closest_y = y

    return closest_azimuth, closest_elevation, closest_x, closest_y,closest_distance

def main():
    # Assuming this function gets snr_data from the dish
    context = starlink_grpc.ChannelContext(target="192.168.100.1:9200")  # Example target
    try:
        starlink_grpc.reset_obstruction_map(context)
        current_utc_time = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        print(f"Current UTC time: {current_utc_time}")
        time.sleep(5)
        snr_data = starlink_grpc.obstruction_map(context)
        current_utc_time = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        print(f"Current UTC time: {current_utc_time}")
    except starlink_grpc.GrpcError as e:
        print("Failed getting obstruction map data:", str(e))
        return

    if not snr_data or not snr_data[0]:
        print("Invalid SNR map data: Zero-length")
        return

    image_width = len(snr_data[0])
    image_height = len(snr_data)
    print(len(snr_data[0]) // 2)
    print(len(snr_data) // 2)
    azimuth_elevation_map = calculate_azimuth_elevation(image_width, image_height)
    closest_azimuth, closest_elevation, closest_x, closest_y,closest_distance = find_closest_white_pixel(snr_data, azimuth_elevation_map)

    current_utc_time = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

    if closest_azimuth is not None and closest_elevation is not None:
        print(f"closest_distance: {closest_distance}")
        print(f"Closest white pixel coordinates: (x={closest_x}, y={closest_y})")
        print(f"Closest white pixel azimuth: {closest_azimuth}, elevation: {closest_elevation}, Zenith: {90-closest_elevation}")
    else:
        print(f"Current UTC time: {current_utc_time}")
        print("No white pixel found.")

    # Plotting the image
    plt.figure(figsize=(8, 8))
    plt.imshow(snr_data, cmap='gray', origin='upper')  # Adjust origin to 'upper' to correct orientation

    if closest_x is not None and closest_y is not None:
        plt.scatter([closest_x], [closest_y], color='red', marker='o', s=2)
        plt.text(closest_x, closest_y, f'Az: {closest_azimuth:.2f}, El: {90-closest_elevation:.2f}', 
                 color='red', fontsize=12, ha='right', va='bottom')

    plt.title(f'Starlink Obstruction Map\n{current_utc_time}')
    # plt.xlabel('Azimuth (degrees)')
    # plt.ylabel('Elevation (degrees)')
    plt.show()

if __name__ == "__main__":
    main()
