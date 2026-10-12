# MiniSheet

**MiniSheet: A Low-Cost, Open-Source, Multimode Light-Sheet Fluorescence Microscopy System**

MiniSheet is a low-cost, multimode light-sheet fluorescence microscopy system designed to make light-sheet imaging more accessible. This repository provides the system control software, ESP32 firmware, mechanical design files, and self-supervised image restoration algorithms developed for MiniSheet.

The system supports three imaging configurations—horizontal, vertical, and slice modes—to accommodate different sample types and imaging requirements. An accompanying self-supervised image restoration method, MIDD, enables image denoising and destriping using multiple independently degraded measurements.

## Features

- **Multimode imaging:** Three configurable imaging modes for different samples and experimental requirements.
- **Integrated system control:** A Python-based graphical user interface for camera operation, system control, scanning, and communication with the ESP32 controller.
- **Open mechanical designs:** SolidWorks assembly and component files for reproducing and customizing the microscope.
- **Self-supervised image restoration:** MIDD for denoising and destriping fluorescence microscopy images without requiring clean ground-truth images.

## Repository Structure

```text
MiniSheet/
├── ESP32/                 # ESP32 firmware and motor control
├── GUI/                   # Python-based graphical user interface
├── Mechanical design/     # SolidWorks assemblies and components
├── MIDD/                  # Self-supervised image restoration
└── README.md
```

## Getting Started

MiniSheet consists of four main components. Refer to the documentation in each directory for installation instructions, configuration details, and usage examples.

- **System control software:** [`GUI/`](GUI/) — Camera operation, graphical interface, scanning, and system control.
- **ESP32 firmware:** [`ESP32/`](ESP32/) — Firmware for hardware control and stepper motor operation.
- **Mechanical designs:** [`Mechanical design/`](Mechanical%20design/) — SolidWorks assembly and component files for the three imaging configurations.
- **Image restoration:** [`MIDD/`](MIDD/) — Source code for self-supervised image denoising and destriping.

The GUI, ESP32 firmware, and mechanical components are intended to work together as an integrated imaging system. The MIDD image restoration code can be used separately for image processing.

## Mechanical Designs

The repository includes SolidWorks assembly files for the three imaging configurations:

- `Assembly_body_horizontal.SLDASM`
- `Assembly_body_vertical.SLDASM`
- `Assembly_body_slice.SLDASM`

Individual component files are provided in the `Mechanical design/Components/` directory.

## Image Restoration

MIDD is provided as a Python implementation for self-supervised image restoration. The source code and associated files are available in the `MIDD/` directory.

Please refer to [`MIDD/`](MIDD/) for details on environment setup, input data preparation, execution, and output generation.

## Citation

If you use MiniSheet in your research, please cite the associated publication:

*Citation information will be added upon publication.*

## License

No license has currently been specified for this repository. Unless a license is added, the source code and design files remain subject to applicable copyright law. Public availability does not, by itself, grant permission to reuse, modify, or redistribute these materials.

