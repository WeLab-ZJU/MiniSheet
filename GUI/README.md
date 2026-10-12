# GUI Software

This directory contains the Python-based graphical user interface (GUI) for MiniSheet, including camera acquisition, ESP32 communication, scanning control, and system logging.

## 1. Install the Hikrobot MVS SDK

The GUI uses the Hikrobot MVS SDK to communicate with the machine vision camera.

1. Download the MVS SDK from the [official Hikrobot website](https://www.hikrobotics.com/).
2. Install the SDK according to the manufacturer's instructions.
3. Verify that the camera is recognized by the MVS software before running the MiniSheet GUI.

The MVS SDK must be installed separately from the Python environment.

## 2. Set Up the Python Environment

The GUI was developed using **Python 3.11.4**.

Create and activate a virtual environment in the `GUI` directory:

```bash
python -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
```

Install the main Python dependencies:

```bash
python -m pip install numpy==2.4.4 napari==0.7.0 tifffile==2026.3.3 PyQt5==5.15.11 pyserial==3.5
```

The GUI also relies on the MVS Python interface and SDK libraries provided in `MVS_sdk/`. Ensure that the SDK libraries are accessible to Python and compatible with the installed MVS SDK.

## 3. Run the GUI

Connect the camera and ESP32 controller, then run the following command from the `GUI` directory:

```bash
python main.py
```

The GUI provides controls for camera operation, ESP32 communication, scanning, and logging.

## Notes

- Install the MVS SDK before configuring camera acquisition.
- Upload the ESP32 firmware separately before using hardware control.
- The Python package versions listed above reflect the development environment. Compatibility with a clean installation should be verified if installation errors occur.
