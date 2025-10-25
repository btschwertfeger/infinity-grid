#!make
# -*- mode: make; coding: utf-8 -*-
#
# Copyright (C) 2023 Benjamin Thomas Schwertfeger
# All rights reserved.
# https://github.com/btschwertfeger
#

UV ?= uv
PYTHON := python
PYTEST := pytest
PYTEST_OPTS := -vv --junit-xml=pytest.xml -n auto
PYTEST_COV_OPTS := $(PYTEST_OPTS) -x --cov=infinity_grid --cov-report=xml:coverage.xml --cov-report=term-missing --cov-report=html
TEST_DIR := tests

## ======= H E L P =============================================================
## help		Show this help message
.PHONY: help
help:
	@grep "^##" Makefile | sed -e "s/##//"

## ======= B U I L D I N G =====================================================
## build		Builds the package
##
.PHONY: build
build: check-uv
	$(UV) build .

.PHONY: rebuild
rebuild: clean build

## doc		Build the documentation
##
.PHONY: doc
doc:
	cd doc && make html

## image	Build the Docker image
##
image: rebuild
	docker build \
	--build-arg VERSION=dev \
	--build-arg CREATE_TIME=$(shell date -u +"%Y-%m-%dT%H:%M:%SZ") \
	-t btschwertfeger/infinity-grid:dev .

## ======= I N S T A L L A T I O N =============================================
## install	Install the package
##
.PHONY: install
install: check-uv
	$(UV) pip install .

## dev		Installs the extended package in edit mode
##
.PHONY: dev
dev: check-uv
	$(UV) pip install --compile -e . -r requirements-dev.txt -r doc/requirements.txt

## ======= T E S T I N G =======================================================
## test		Run the unit tests
##
.PHONY: test
test:
	$(PYTEST) $(PYTEST_OPTS) $(TEST_DIR)

.PHONY: tests
tests: test

## retest		Run only the tests that failed last time
##
.PHONY: retest
retest:
	$(PYTEST) $(PYTEST_OPTS) --lf $(TEST_DIR)

## wip		Run tests marked as 'wip'
##
.PHONY: wip
wip:
	@rm .cache/tests/*.log || true
	$(PYTEST) -m "wip" -vv $(TEST_DIR)

## coverage       Run all tests and generate the coverage report
##
.PHONY: coverage
coverage:
	@rm .cache/tests/*.log || true
	$(PYTEST) $(PYTEST_COV_OPTS) $(TEST_DIR)

## doctest	Run the documentation related tests
##
.PHONY: doctest
doctest:
	cd docs && make doctest

## ======= M I S C E L L A N I O U S ===========================================
## pre-commit	Run the pre-commit targets
##
.PHONY: pre-commit
pre-commit:
	@pre-commit run -a

## clean		Clean the workspace
##
.PHONY: clean
clean:
	rm -rf \
		.cache \
		.vscode \
		dist/ \
		doc/_build \
		src/infinity_grid.egg-info \
	    build/ \
		htmlcov/

	rm -f \
		.coverage \
		*.csv \
		*.log \
		*.zip \
		coverage.xml \
		src/infinity_grid/_version.py \
		mypy.xml \
		pytest.xml \
		infinity_grid-*.whl \
		uv.lock

	find src/infinity_grid -name "__pycache__" | xargs rm -rf
	find tests -name "__pycache__" | xargs rm -rf
	find tools -name ".ipynb_checkpoints" | xargs rm -rf
	find tools -name "__pycache__" | xargs rm -rf
	find tests -name "*.log" | xargs rm -rf

## check-uv       Check if uv is installed
##
.PHONY: check-uv
check-uv:
	@if ! command -v $(UV) >/dev/null; then \
		echo "Error: uv is not installed. Please visit https://github.com/astral-sh/uv for installation instructions."; \
		exit 1; \
	fi
