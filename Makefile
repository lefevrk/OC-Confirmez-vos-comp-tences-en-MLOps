#################################################################################
# GLOBALS                                                                       #
#################################################################################

PROJECT_NAME = OC-Confirmez-vos-competences-en-MLOps
IMAGE_NAME = credit-scoring-api

#################################################################################
# COMMANDS                                                                      #
#################################################################################

## Install Python Dependencies (API + dev)
.PHONY: requirements
requirements:
	uv sync --extra api

## Run the API locally with autoreload
.PHONY: run
run:
	uv run uvicorn api.main:app --reload

## Build the API Docker image
.PHONY: docker-build
docker-build:
	docker build -t $(IMAGE_NAME) .

## Run the API Docker image locally
.PHONY: docker-run
docker-run:
	docker run --rm -p 7860:7860 --env-file .env $(IMAGE_NAME)

## Delete all compiled Python files
.PHONY: clean
clean:
	find . -type f -name "*.py[co]" -delete
	find . -type d -name "__pycache__" -delete

## Lint using ruff (check only)
.PHONY: lint
lint:
	uv run ruff check .
	uv run ruff format --check .

## Format source code with ruff
.PHONY: format
format:
	uv run ruff check --fix .
	uv run ruff format .

## Run tests (if pytest is installed)
.PHONY: test
test:
	uv run pytest

## Set up Python interpreter environment
.PHONY: create-environment
create-environment:
	uv venv
	@echo ">>> New uv virtual environment created. Activate with:"
	@echo ">>> Windows: .\\.venv\\Scripts\\activate"
	@echo ">>> Unix/macOS: source ./.venv/bin/activate"

#################################################################################
# PROJECT RULES                                                                 #
#################################################################################

## Git Hooks
.PHONY: setup-hooks
setup-hooks:
	uv run pre-commit install
	uv run pre-commit install --hook-type pre-push

#################################################################################
# Self Documenting Commands                                                     #
#################################################################################

.DEFAULT_GOAL := help

define PRINT_HELP_PYSCRIPT
import re, sys; \
lines = '\n'.join([line for line in sys.stdin]); \
matches = re.findall(r'\n## (.*)\n[\s\S]+?\n([a-zA-Z_-]+):', lines); \
print('Available rules:\n'); \
print('\n'.join(['{:25}{}'.format(*reversed(match)) for match in matches]))
endef
export PRINT_HELP_PYSCRIPT

help:
	@uv run python -c "${PRINT_HELP_PYSCRIPT}" < $(MAKEFILE_LIST)
