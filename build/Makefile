
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
	@rm -f -r __pycache__ qarnot/__pycache__ qarnot/*.pyc

print-version:
	@$(PYTHON) main.py --version


install-requirements:
	$(PYTHON) -m pip install --upgrade pip
	$(PYTHON) -m pip install -r requirements.txt


############ Linting and testing area

flake8:
	flake8 --ignore $(PYLINT_IGNORES) setup.py qarnot

pylint:
	pylint --rcfile=setup.cfg qarnot/*.py --disable=all --enable=W,E,F -d W0212, W1620
	# W0212: Access to a protected member "" of a client class (protected-access)
	# W1620: Calling a dict.iter*() method

lint: flake8 pylint

unit-tests:
	pytest -v

integration-tests:
	@echo "for intergration tests, see the internal simple"

doc:
	make -C doc html

tests: unit-tests integration-tests

re: clean build


.PHONY: flake8 lint integration-tests unit-tests tests install clean build
