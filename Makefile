PYTHON=python
ENV_NAME=cq

.PHONY: help run setup clean

help:
	echo "Usage:"
	echo "  make setup                         - Sets up the environment"
	echo "  make run <args>                    - Runs the cube.py script (requires active environment)"
	echo "                                       Example: make run my_cube stl 1 2.397 0.595"
	echo "  make clean                         - Removes generated files (e.g., .stl, .step)"
	echo "Note: Make sure to activate the environment first with: mamba activate cq"

setup:
	mamba env list | grep -q "^$(ENV_NAME)\s" || mamba create -n $(ENV_NAME) python=3.10 cadquery -c conda-forge -y

run:
	$(PYTHON) src/cube.py $(filter-out $@,$(MAKECMDGOALS))

clean:
	rm -f *.stl *.step

