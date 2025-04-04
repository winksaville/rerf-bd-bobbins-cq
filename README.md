# 3D Cube with Text - CadQuery App

This repository provides a simple Python application (`rerf-cubes`) that generates a 3D cube with text inscriptions on its faces using CadQuery. The application can be run on Windows, Mac, and Linux with minimal setup.

## Requirements

- Python 3.12+ (Anaconda or Miniconda recommended)
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
git clone https://github.com/winksaville/rerf-cubes-cq.git
cd rerf-cubes-cq
```

### 4. Setup the environment

```sh
make setup
```

This will create a `cq` environment with Python 3.12+ and CadQuery installed. Run this only once unless you delete the environment.

## Usage

### Activating the Environment

Activate the environment using:

```sh
conda activate cq
```

### Running the App

Ensure the environment is activated, see [Activating the Environment](#activating-the-environment). Then run the script directly with:

```sh
./rerf-cubes <filename> <format> <cube_number> <cube_size> <tube_size>
```

Example:

```sh
./rerf-cubes cube2 stl 5 2.397 0.595
```

### Cleaning Up

Remove generated files (`.stl`, `.step`) with:

```sh
make clean
```

## Exported Files

The generated files will be saved in the current directory with the specified format.

## Notes

- Ensure you are in the `cq` environment before running the script (`make activate`).
- Tested on Linux, Windows, and Mac.

## License

Licensed under either of

- Apache License, Version 2.0 ([LICENSE-APACHE](LICENSE-APACHE) or [http://apache.org/licenses/LICENSE-2.0](http://apache.org/licenses/LICENSE-2.0))
- MIT license ([LICENSE-MIT](LICENSE-MIT) or [http://opensource.org/licenses/MIT](http://opensource.org/licenses/MIT))

### Contribution

Unless you explicitly state otherwise, any contribution intentionally submitted
for inclusion in the work by you, as defined in the Apache-2.0 license, shall
be dual licensed as above, without any additional terms or conditions.
