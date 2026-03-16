.PHONY: help setup setup-compose install lint format typecheck test run list-tasks doctor \
        ollama-up ollama-pull ollama-run \
        compose-up compose-down compose-logs clean

VENV     := venv
PYTHON   := $(VENV)/bin/python
PIP      := $(VENV)/bin/pip
AGENT    := $(VENV)/bin/agent
MODEL    ?= llama3.2

# ---------------------------------------------------------------------------
# Default target
# ---------------------------------------------------------------------------
help:
	@echo ""
	@echo "strands-multi-engineer-agent — available targets"
	@echo "─────────────────────────────────────────────────"
	@echo "  setup            Bootstrap: create venv, copy .env, install deps"
	@echo "  setup-compose    Bootstrap + Docker/Docker Compose checks"
	@echo "  install          Re-install deps into venv (pip or uv)"
	@echo ""
	@echo "  doctor           Validate environment and config"
	@echo "  list-tasks       List available engineering tasks"
	@echo "  run              Run the agent with DEFAULT_PROVIDER"
	@echo ""
	@echo "  ollama-up        Start Ollama container (Docker Compose)"
	@echo "  ollama-pull      Pull a model into Ollama  [MODEL=llama3]"
	@echo "  ollama-run       Run agent against Ollama  [MODEL=llama3]"
	@echo ""
	@echo "  compose-up       Build agent image + start all services"
	@echo "  compose-down     Stop all Docker Compose services"
	@echo "  compose-logs     Tail Ollama container logs"
	@echo ""
	@echo "  lint             Run ruff linter"
	@echo "  format           Run ruff formatter"
	@echo "  typecheck        Run mypy"
	@echo "  test             Run pytest"
	@echo "  clean            Remove build artifacts and caches"
	@echo ""

# ---------------------------------------------------------------------------
# Bootstrap
# ---------------------------------------------------------------------------
setup:
	@bash scripts/bootstrap.sh --runtime native

setup-compose:
	@bash scripts/bootstrap.sh --runtime compose

install:
	@if command -v uv > /dev/null 2>&1; then \
		echo "→ Installing with uv into venv"; \
		uv pip install --python $(PYTHON) -e ".[dev]"; \
	else \
		echo "→ Installing with pip into venv"; \
		$(PIP) install -e ".[dev]"; \
	fi

# ---------------------------------------------------------------------------
# Agent CLI shortcuts
# ---------------------------------------------------------------------------
doctor:
	$(AGENT) doctor

list-tasks:
	$(AGENT) list-tasks

run:
	$(AGENT) run

# ---------------------------------------------------------------------------
# Ollama (Docker Compose)
#
# Three steps to run the agent against a local Ollama model:
#   1. make ollama-up          — start the Ollama container
#   2. make ollama-pull        — download the model (first time only)
#   3. make ollama-run         — run the agent workflow against Ollama
#
# MODEL defaults to llama3. Override: make ollama-pull MODEL=mistral
# ---------------------------------------------------------------------------
ollama-up:
	docker compose up ollama -d
	@echo "→ Waiting for Ollama to be ready…"
	@until curl -sf http://localhost:11434/api/tags > /dev/null 2>&1; do \
	  printf '.'; sleep 2; \
	done
	@echo ""
	@echo "✓ Ollama is ready"

ollama-pull:
	docker compose exec ollama ollama pull $(MODEL)

ollama-run:
	docker compose build agent
	docker compose run --rm agent run --provider ollama

# ---------------------------------------------------------------------------
# Docker Compose (full stack)
# ---------------------------------------------------------------------------
compose-up:
	docker compose up ollama -d --build

compose-down:
	docker compose down

compose-logs:
	docker compose logs -f ollama

# ---------------------------------------------------------------------------
# Code quality
# ---------------------------------------------------------------------------
lint:
	$(VENV)/bin/ruff check .

format:
	$(VENV)/bin/ruff format .

typecheck:
	$(VENV)/bin/mypy agent providers tools tasks eval

# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------
test:
	$(VENV)/bin/pytest -v

# ---------------------------------------------------------------------------
# Clean
# ---------------------------------------------------------------------------
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	rm -rf dist/ build/
	@echo "→ Clean done"
