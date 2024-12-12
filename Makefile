all:
	@echo "Run your commands here"

run:
	python -m app

test:
	pytest

lint:
	python -m flake8 .
