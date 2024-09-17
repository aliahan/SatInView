# Trajectory-based Serving Satellite Identification with User Terminal's Field-of-View

This repository contains the implementation and artifacts for the paper ***Trajectory-based Serving Satellite Identification with User Terminal's Field-of-View*** accepted in LEO-NET'24.

Table of Contents
=================

* [Prerequisites](#prerequisites)
* [Get new results](#get-new-results)
* [Re-generate paper results](#re-generate-paper-results)

## Prerequisites

Clone the repository.

```bash
git clone --recurse-submodules https://github.com/aliahan/SatInView.git
cd SatInView
```

Create a Python virtual environment and install dependencies.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -r starlink-grpc-tools/requirements.txt
```

Install `grpcurl` from https://github.com/fullstorydev/grpcurl.

### Set variables

1. Edit `dish_id` in `snr.py` to identify results from different dishes
2. The total execuation time of the script is defined by the number of `exp_rounds` in `snr.py` times 15 seconds.

## Get new results

```bash
bash status.sh
python3 snr.py
```

You can run `tail -f white_pixel_coordinates_xor-{dish_id}.csv`, if there is anything like

```
2024-08-31 16:43:30,31,54
2024-08-31 16:43:31,31,54
2024-08-31 16:43:32,31,55
2024-08-31 16:43:33,31,55
2024-08-31 16:43:34,31,56
2024-08-31 16:43:35,31,56
2024-08-31 16:43:36,31,57
2024-08-31 16:43:37,31,57
2024-08-31 16:43:38,31,58
```

then it's running normally.

Wait until the script finishes, you will get `gp.php`, `white_pixel_coordinates_xor-{dish_id}.csv`, and `get_status-{time}.txt` in the current directory.

## Re-generate paper results

Run `findmatch.ipynb` notebook to first create the `processed_observed_data.csv` containing the topocentric coordinates of the observed satellites and then to find
the matching satellites and have the `matched_satellite_data.csv` dataset.

Ensure you set your location, dish orientation, and the data collection time duration in the cade accordingly.

To re-generate the figures in the paper you can run the  `figure.ipynb` notebook.