PYTHON=python
PYTHON_VERSION="3.12"  # Make sure it's a string
ENV_NAME=cq
SHELL=/usr/bin/bash

.PHONY: help run setup clean activate

help:
	@echo "Usage:"
	@echo "  make setup                         - Sets up the environment"
	@echo "  make activate                      - Activates the environment (Doesn't work well)"
	@echo "  make clean                         - Removes generated files (e.g., .stl, .step)"
	@echo
	@echo "Note: Make sure to activate the environment first with: make activate"

setup:
	$(PYTHON) -c "import sys; major, minor = map(int, '$(PYTHON_VERSION)'.split('.')); assert sys.version_info >= (major, minor), f'Python {$(PYTHON_VERSION)}+ is required.'"
	mamba env list | grep -q "^$(ENV_NAME)\s" || mamba create -n $(ENV_NAME) python cadquery -c conda-forge --override-channels -y

activate:
	conda run -n $(ENV_NAME) $(SHELL)

#	mamba run -n $(ENV_NAME) $(SHELL)
#	mamba activate cq
#	conda run -n $(ENV_NAME) $(SHELL)

clean:
	@rm -f *.stl *.step *.pm4n
