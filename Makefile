init:
	pip install -r requirements-dev.txt --require-virtualenv
	pre-commit install --install-hooks
