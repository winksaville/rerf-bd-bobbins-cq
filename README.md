# 3D Cube with Text - CadQuery App

This repository provides a simple Python application (`cube.py`) that generates a 3D cube with text inscriptions on its faces using CadQuery. The application can be run on Windows, Mac, and Linux with minimal setup.

## Requirements

- Python (Anaconda or Miniconda recommended)
- Mamba (Installed via conda)

## Setup

### 1. Install Miniconda or Anaconda (if not already installed)
- **Miniconda (Recommended):** [https://docs.conda.io/en/latest/miniconda.html](https://docs.conda.io/en/latest/miniconda.html)
- **Anaconda:** [https://www.anaconda.com/products/distribution](https://www.anaconda.com/products/distribution)

### 2. Install `mamba`
If you already have `conda` installed, you can install `mamba` with:
```sh
conda install -c conda-forge mamba
```

### 3. Clone this repository
```sh
git clone https://github.com/your-username/your-repo-name.git
cd your-repo-name
```

### 4. Setup the environment
```sh
make setup
```

This will create a `cq` environment with Python 3.10 and CadQuery installed. Run this only once unless you delete the environment.

## Usage

### Activating the Environment
Ensure you have activated the environment before running the app:
```sh
mamba activate cq
```

### Running the App
Use the `Makefile` to run the app by specifying arguments:
```sh
make run my_cube stl 1 2.397 0.595
```

Alternatively, you can run the script directly:
```sh
python src/cube.py my_cube stl 1 2.397 0.595
```

### Cleaning Up
Remove generated files (`.stl`, `.step`) with:
```sh
make clean
```

## Exported Files
The generated files will be saved in the current directory with the specified format.

## Notes
- Ensure you are in the `cq` environment before running the script (`mamba activate cq`).
- Tested on Linux, Windows, and Mac.

## License

Licensed under either of

- Apache License, Version 2.0 ([LICENSE-APACHE](LICENSE-APACHE) or http://apache.org/licenses/LICENSE-2.0)
- MIT license ([LICENSE-MIT](LICENSE-MIT) or http://opensource.org/licenses/MIT)

### Contribution

Unless you explicitly state otherwise, any contribution intentionally submitted
for inclusion in the work by you, as defined in the Apache-2.0 license, shall
be dual licensed as above, without any additional terms or conditions.
