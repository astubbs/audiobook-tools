.PHONY: install test lint type clean format

install:
	pip install -e ".[dev]"
	pip install tox

test:
	tox -e py38

lint:
	tox -e lint

type:
	tox -e type

clean:
	rm -rf .tox
	rm -rf *.egg-info
	rm -rf build
	rm -rf dist
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

format:
	black audiobook_tools tests
	isort audiobook_tools tests

check: lint type test 