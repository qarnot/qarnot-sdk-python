
# bad number of blank lines, annoying
PYLINT_IGNORES := E301,E302,E303,E306
# line too long
PYLINT_IGNORES := $(PYLINT_IGNORES),E501
# line break before/after binary operator
PYLINT_IGNORES := $(PYLINT_IGNORES),W503,W504

PYTHON=python3

all: build


build:

clean:
	@rm -f -r __pycache__

print-version:
	@$(PYTHON) main.py --version


install-requirements:
	$(PYTHON) -m pip install --upgrade pip
	$(PYTHON) -m pip install -r requirements.txt


############ Linting and testing area

flake8:
	flake8 --ignore $(PYLINT_IGNORES) main.py qarnot

lint: flake8

unit-tests:
	pytest -v

integration-tests:
	@echo "for intergration tests, see the internal simple"

tests: unit-tests integration-tests

re: clean build


.PHONY: flake8 lint integration-tests unit-tests tests install clean build
