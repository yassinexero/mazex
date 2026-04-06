PYTHON     = python3
MAIN       = a_maze_ing.py
CONFIG     = config.txt
PDB        = $(PYTHON) -m pdb

.PHONY: install run debug clean lint lint-strict

install:
	pip install --break-system-packages flake8 mypy

run:
	$(PYTHON) $(MAIN) $(CONFIG)

debug:
	$(PDB) $(MAIN) $(CONFIG)

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	find . -type f -name "*.pyc"       -delete
	find . -type f -name "*.pyo"       -delete

lint:
	flake8 .
	mypy . \
		--warn-return-any \
		--warn-unused-ignores \
		--ignore-missing-imports \
		--disallow-untyped-defs \
		--check-untyped-defs

lint-strict:
	flake8 .
	mypy . --strict