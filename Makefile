.PHONY: setup test lint run


setup:
python -m venv .venv && . .venv/Scripts/activate && pip install -U pip && pip install -e .
pre-commit install


lint:
pre-commit run --all-files


test:
pytest -q


run:
spagent weekend
