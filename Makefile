# Greedy Metasearch Makefile

PYTHON := .venv/bin/python
PIP := .venv/bin/python -m pip

.PHONY: help install build test run-api docker-build docker-up upgrade

help:
	@echo "Available commands:"
	@echo "  install      - Setup virtual environment and install dependencies"
	@echo "  build        - Compile Rust native extensions"
	@echo "  test         - Run pytest suite"
	@echo "  run-api      - Start the FastAPI server locally"
	@echo "  docker-build - Build the Docker image locally"
	@echo "  docker-up    - Run the API via Docker Compose"
	@echo "  upgrade      - Pull latest changes and rebuild everything"

install:
	python3 -m venv .venv
	$(PIP) install --upgrade pip
	$(PIP) install -e .[dev,api,mcp,dht]

build:
	$(PYTHON) native/build.py

test:
	$(PYTHON) -m pytest

run-api:
	$(PYTHON) -m uvicorn ddgs.api_server:fastapi_app --host 0.0.0.0 --port 8000

docker-build: build
	docker build -t ghcr.io/rustxpy/greedy:main .

docker-up: build
	cd docker_test && docker-compose up --build -d

upgrade:
	git pull origin main
	$(MAKE) install
	$(MAKE) build
	@echo "✅ Upgrade complete!"
