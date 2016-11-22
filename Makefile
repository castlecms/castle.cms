.PHONY: nosetests test flake8

all: bin/python test
test: nosetests flake8

bin/python:
	@virtualenv .
	@bin/python setup.py dev

nosetests:
	@echo "==== Running nosetests ===="
	@bin/nosetests

flake8:
	@echo "==== Running Flake8 ===="
	@bin/flake8 castle.cms *.py
