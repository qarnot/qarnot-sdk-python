
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

install-dev-requirements: install-requirements
	$(PYTHON) -m pip install -r requirements-test.txt

install-doc-requirements: install-requirements
	$(PYTHON) -m pip install -r requirements-doc.txt

install-optional-requirements: install-requirements
	$(PYTHON) -m pip install -r requirements-optional.txt

install-all-requirements: install-dev-requirements install-optional-requirements install-doc-requirements

############ Linting

flake8:
	flake8 --ignore E501,F405,F403,W503 setup.py qarnot

pylint:
	pylint --rcfile=setup.cfg qarnot/*.py --disable=C,R,W0212,W1620
# W0212: Access to a protected member "" of a client class (protected-access)
# W1620: Calling a dict.iter*() method

pylint-advice:
	pylint --rcfile=setup.cfg qarnot/*.py --disable=C,R --enable=C0114,C0115,R0205,C0103,R1720,R0801:

typing:
	mypy qarnot/ --no-strict-optional --ignore-missing-import --pretty --show-error-context --show-column-numbers --show-error-codes --tb --raise-exceptions --check-untyped-defs

lint: typing flake8 pylint

############ Testing area

quick-tests:
	pytest -v -m "not (slow)" test/

unit-tests:
	pytest -v test/

integration-tests:
	@echo "for intergration tests, see the internal simple"

quick-coverage:
	pytest  -v -m "not (slow)" --cov=qarnot --cov-report=html  test
	@echo "test index in ./htmlcov/index.html"

unit-test-coverage: lint
	pytest --cov --cov-report html test/
	@echo "test index in ./htmlcov/index.html"


full-tests: lint unit-tests integration-tests

tests: lint quick-tests integration-tests

coverage: lint quick-coverage

full-coverage: lint unit-test-coverage

############ Doc

doc:
	make -C doc html

clean-doc:
	rm -r doc/_build

re-doc: clean-doc doc

re: clean build


.PHONY: flake8 lint integration-tests unit-tests tests install clean build doc re-doc clean-doc
