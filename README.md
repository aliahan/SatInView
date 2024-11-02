# Trajectory-based Serving Satellite Identification with User Terminal's Field-of-View

This repository contains the implementation and artifacts for the paper ***Trajectory-based Serving Satellite Identification with User Terminal's Field-of-View*** accepted in LEO-NET'24.

Table of Contents
=================

* [Background](#background)
* [Prerequisites](#prerequisites)
* [Get new results](#get-new-results)
* [Re-generate paper results](#re-generate-paper-results)

## Background

Since the Starlink dish firmware update ([`286014e2-fea5-46e5-805f-85cd72450533.uterm_manifest.release`](https://github.com/clarkzjw/starlink-grpc-golang/commit/2979925ba64f82937c559b59673ae860b70edd7f)) in August 2024, a new `mapReferenceFrame` field was introduced to the output of the `dish_get_obstruction_map` gRPC call.

```go
type ObstructionMapReferenceFrame int32

const (
	ObstructionMapReferenceFrame_FRAME_UNKNOWN ObstructionMapReferenceFrame = 0
	ObstructionMapReferenceFrame_FRAME_EARTH   ObstructionMapReferenceFrame = 1
	ObstructionMapReferenceFrame_FRAME_UT      ObstructionMapReferenceFrame = 2
)

// Enum value maps for ObstructionMapReferenceFrame.
var (
	ObstructionMapReferenceFrame_name = map[int32]string{
		0: "FRAME_UNKNOWN",
		1: "FRAME_EARTH",
		2: "FRAME_UT",
	}
	ObstructionMapReferenceFrame_value = map[string]int32{
		"FRAME_UNKNOWN": 0,
		"FRAME_EARTH":   1,
		"FRAME_UT":      2,
	}
)
```

Example output from `grpcurl -plaintext -d {\"dish_get_obstruction_map\":{}} 192.168.100.1:9200 SpaceX.API.Device.Device/Handle`:

```
{
  "apiVersion": "26",
  "dishGetObstructionMap": {
    "numRows": 123,
    "numCols": 123,
    "snr": [
      -1,
...
      -1
    ],
    "minElevationDeg": 10,
    "maxThetaDeg": 80,
    "mapReferenceFrame": "FRAME_UT"
  }
}
```

Based on our measurement and observation, the `mapReferenceFrame` specifies the coordinate system used for the obstruction map data.

The possible values for `mapReferenceFrame` are:

- **FRAME_UNKNOWN (0)**: The reference frame is unspecified.
- **FRAME_EARTH (1)**: The obstruction map is aligned with the Earth and uses a fixed geographic coordinate system, with the top center pixel oriented toward the true north.
- **FRAME_UT (2)**: The obstruction map is aligned with the User Terminal, using a coordinate system relative to the dish's orientation. The bottom center pixel corresponds to the UT's boresight direction.


Our observation shows that most active Starlink dishes show `FRAME_EARTH`, most likely because they are in fixed, stationary locations and utilize a geographic coordinate system to track obstructions more efficiently, while dishes on `Roam`/`Mobile` or inactive dishes show `FRAME_UT`, partially because these dishes are often moved or relocated, requiring a coordinate system relative to the dish’s orientation to adapt dynamically to changing positions or conditions.

Thus, in addition to the method presented in the LEO-NET'24 paper, our post-processing involves an additional two-step process:

...

## Prerequisites

### Prepare the environment

+ Clone the repository.

    ```bash
    git clone --recurse-submodules https://github.com/aliahan/SatInView.git
    cd SatInView
    ```

+ Create a Python virtual environment and install dependencies.

    ```bash
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
    pip install -r starlink-grpc-tools/requirements.txt
    ```

    **Note**: On a dual-homed machine connected to an inactive Starlink dish (i.e., without an active Starlink subscription), the Starlink router still advertises an IPv6 address to the local network. `Pip` would prefer to use IPv6 when installing packages, while an inactive dish cannot reach the Internet, which could halt the installation process. In this case, you can force `pip` to use IPv4 by setting the IPv4 addresses for the following doamins in `/etc/hosts` or configure routing properly.

    ```
    151.101.0.223   pypi.org
    151.101.68.223  files.pythonhosted.org
    ```

+ Install `grpcurl` from https://github.com/fullstorydev/grpcurl to your `$PATH`.

### Set variables

1. Edit [`config.py`](./config.py), set `IFCE` to the interface connected to Starlink. Set `DISH_ID` to the ID of the dish.
2. If IRTT tests are used, set `ENABLE_IRTT` to `True`, set `LOCAL_IP` to the local IP address for the Starlink interface `IFCE`, and set `IRTT_SERVER_PORT` to the IRTT server address and port.
3. The gateway of inactive Starlink dishes can be reached at `fe80::200:5eff:fe00:101`, which requires the stock Starlink router to be set in the `bypass` mode.
4. You may need to install the `iputils-ping` package instead of the `inetutils-ping` package on Debian-based systems to use the `-D` timestamp option.
```bash
apt list --installed | grep ping
```
5. You may also need to assign root privileges to the `ping` command to use the packet intervals less than 200ms, or install [`iputils-ping>=20210722`](https://github.com/iputils/iputils/releases/tag/20210722), which [lowered the limit to 2ms](https://github.com/iputils/iputils/issues/317).

6. By default, the scheduling of tasks are defined in `main.py` as follows, which can be modified as needed.

```python
if ENABLE_IRTT:
    schedule.every(1).hours.at(":00").do(run, irtt_ping).tag("Latency")

schedule.every(1).hours.at(":00").do(run, icmp_ping).tag("Latency")
schedule.every(1).hours.at(":00").do(run, grpc_get_status).tag("gRPC")
schedule.every(6).hours.at(":00").do(run, load_satellites).tag("TLE")
schedule.every(1).hours.at(":00").do(run, collect_obstruction_data).tag("TLE")
```

### Dish GPS Location

You can get the GPS location of your dish by running the following command, which requires the `Allow access on local network` option to be enabled in the Starlink app at `Advanced` -> `Debug data` -> `Starlink location`.

```bash
grpcurl -plaintext -d {\"get_location\":{}} 192.168.100.1:9200 SpaceX.API.Device.Device/Handle
```

The GPS location is requied to calculate and estimate the selected and serving satellites in post-processing.

## Get new results

Run `main.py` to collect the latency data to Starlink gateway (`100.64.0.1`) and the satellite tragetory data from the obstruction map.

By default, the data structure of the collected data is as follows:

```
data
├── grpc
│   └── 2024-10-08
│       └── GetStatus-2024-10-08-19-10-00.txt
├── latency
│   └── 2024-10-08
│       ├── irtt-10ms-5m-2024-10-08-19-10-00.json
│       └── ping-10ms-5m-2024-10-08-19-10-00.txt
└── TLE
    └── 2024-10-08
        ├── obstruction-data-<dish_id>-2024-10-08-19-10-01.csv
        └── starlink-tle-2024-10-08-19-10-00.txt
```

+ The `grpc` directory contains the dish diagnostic and alignment data from Starlink dish's gRPC interface (`192.168.100.1:9200`).
+ The `latency` directory contains the ICMP ping RTT measurement to Starlink's gateway. When IRTT test is enabled, the IRTT measurement data is stored in the same directory after each round finishes.
+ The `TLE` directory contains the collected obstruction and satellite trajectory data and the TLE snapshots of all Starlink satellites from Celestrak.

## Re-generate paper results

Run `findmatch.ipynb` notebook to first create the `processed_observed_data.csv` containing the topocentric coordinates of the observed satellites and then to find
the matching satellites and have the `matched_satellite_data.csv` dataset.

Ensure you set your location, dish orientation, and the data collection time duration in the cade accordingly.

To re-generate the figures in the paper you can run the  `figure.ipynb` notebook.
