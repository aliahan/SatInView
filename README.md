# Trajectory-based Serving Satellite Identification with User Terminal's Field-of-View

This repository contains the implementation and artifacts for the paper ***Trajectory-based Serving Satellite Identification with User Terminal's Field-of-View*** submitted to LEO-NET'24.

Table of Contents
=================

* [Prerequisites](#prerequisites)
* [Re-generate paper results](#re-generate-paper-results)
* [Collect new data](#collect-new-data)

## Prerequisites

Clone the repository.

```bash
git clone --recurse-submodules https://github.com/<REDACTED>/SatInView.git
cd SatInView
```

Create a Python virtual environment and install dependencies.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -r starlink-grpc-tools/requirements.txt
```

## Re-generate paper results

...

## Collect new data

Run `python3 ./snr.py` to collect new traces for Starlink satellite obstruction data.
