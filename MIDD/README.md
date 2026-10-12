# MIDD: Self-Supervised Image Restoration

This directory contains the implementation of MIDD, a self-supervised image restoration method designed to reduce noise and stripe artifacts in light-sheet fluorescence microscopy images.

## 1. Set Up the Python Environment

The code requires Python and PyTorch. The following setup uses a virtual environment:

```bash
python -m venv .venv
```

Activate the environment on Windows:

```bash
.venv\Scripts\activate
```

On macOS or Linux:

```bash
source .venv/bin/activate
```

Upgrade `pip` and install the required packages:

```bash
python -m pip install --upgrade pip
python -m pip install numpy tifffile matplotlib
```

Install **PyTorch** following the instructions on the [official PyTorch website](https://pytorch.org/get-started/locally/). A CUDA-compatible PyTorch installation and a supported NVIDIA GPU are required by the current implementation, which calls `.cuda()` during training.

## 2. Prepare the Input Data

Place the input TIFF stack at:

```text
MIDD/
├── data/
│   └── org.tif
├── result/
├── main.py
├── self_learn_base.py
├── utils.py
└── zs_n2n.py
```

The script reads the image stack from `data/org.tif` and selects a single slice for restoration. Make sure that the `data` and `result` directories exist before running the script.

## 3. Configure the Parameters

The main parameters are defined in `main.py`:

| Parameter | Default value | Description |
|---|---:|---|
| `z_slice` | `50` | Index of the slice selected from the input stack |
| `angle` | `[10, 0, -10]` | Angle settings defined for the forward model |
| `stripe_amplitude` | `0.8` | Stripe-artifact amplitude |
| `noise_level` | `0.02` | Noise level |
| `background` | `0.1` | Background offset added to the selected slice |
| `channel` | `32` | Base channel width of the neural network |
| `epochs` | `1000` | Number of training epochs |

Adjust these parameters in `main.py` as needed for your data and experiments.

## 4. Run MIDD

From the `MIDD` directory, run:

```bash
python main.py
```

The script loads the selected slice, generates three simulated measurements using the forward model, trains the self-supervised CNN, and saves the resulting images.

The current implementation uses CUDA for training. Before running the script, verify that PyTorch can access a compatible GPU.

## 5. Output Files

The restored image and the three simulated input measurements are saved in the `result/` directory:

- `result.tif` — Restored image.
- `raw1.tif` — First simulated measurement.
- `raw2.tif` — Second simulated measurement.
- `raw3.tif` — Third simulated measurement.

## Notes

- Run the script from the `MIDD` directory so that the relative paths to `data/org.tif` and `result/` resolve correctly.
- The default script generates simulated measurements from the selected input slice. To process experimentally acquired images, the data-loading and measurement-generation sections may need to be adapted to the format of your input data.
- The Python package versions should be pinned after the environment has been tested successfully.
