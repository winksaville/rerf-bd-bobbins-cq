# 3D Cube with Text - CadQuery App

This repository provides a simple Python application (`rerf-cubes-cq`) that generates 4 3D cubes in
the 4 corners of the build plate. The are marked with the number 1 at the origin, 2 at +Y
3 at +X and 4 at +X, +Y. Printing that didn't work out well, I manually fiddled with the
base with 1 layer and 3 second exposure. That didn't produce any completed prints.

I've now added base and standoffs using Lychee and we'll see if that's any better and it's file
boxes-at-corners-lychee-supports.pm4n.

My next step is to add the supports in this app as eventually I'll have quite a few cubes and
adding supports manually won't be practical.


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

### Help

To see the help message for the script, run:
```sh
$ ./rerf-cubes.py -h
usage: rerf-cubes.py [-h] [-c CUBE_SIZE] [-t TUBE_SIZE] [-r RESOLUTION] [-l LAYER_HEIGHT] [-s SUPPORT_LEN] [-bl BASE_LAYERS] [-pbsp width height] [-pbl x y] filename {stl,step} row_count col_count

Generate 3D cubes with text inscriptions.

positional arguments:
  filename              Name of the output file (without extension)
  {stl,step}            Format to export the model ('stl' or 'step')
  row_count             Number of rows to create (>= 1)
  col_count             Number of columns to create (>= 1)

options:
  -h, --help            show this help message and exit
  -c CUBE_SIZE, --cube_size CUBE_SIZE
                        Cube size engraved on the +X face, defaults to 2.397
  -t TUBE_SIZE, --tube_size TUBE_SIZE
                        Tube size engraved on the -X face, defaults to 0.629
  -r RESOLUTION, --resolution RESOLUTION
                        resolution of the printer, defaults to 0.017
  -l LAYER_HEIGHT, --layer_height LAYER_HEIGHT
                        Layer height of the printer, defaults to 0.050
  -s SUPPORT_LEN, --support_len SUPPORT_LEN
                        Length of the support structure, defaults to 5.000
  -bl BASE_LAYERS, --base_layers BASE_LAYERS
                        Number of layers for the base, defaults to 10
  -pbsp width height, --position_box_size_pixels width height
                        Size of box to place the cubes, defaults to (5000.006, 2500.003)
  -pbl x y, --position_box_location x y
                        Location of placement box, defaults to (0, 0)
```


### Running the App

Ensure the environment is activated, see [Activating the Environment](#activating-the-environment). Then run the script directly with:

```sh
./rerf-cubes.py <filename> <format> <row_count> <col_count> [options]
```

Example:

```sh
./rerf-cubes.py cube2 stl 1
```

### Cleaning Up

Remove generated files (`.stl`, `.step`, `pm4n`) with:

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
