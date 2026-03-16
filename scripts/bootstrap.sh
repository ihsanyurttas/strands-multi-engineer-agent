#!/usr/bin/env bash
# bootstrap.sh — project setup for strands-multi-engineer-agent
#
# Usage:
#   bash scripts/bootstrap.sh                  # native runtime (default)
#   bash scripts/bootstrap.sh --runtime compose # also check Docker
#
# Behaviour:
#   - Creates a local venv (never installs into the global Python environment)
#   - Prefers uv if available, falls back to python -m venv + pip
#   - Copies .env.example → .env if .env does not yet exist
#   - Docker checks are only performed when --runtime compose is passed
#   - CLI smoke test checks venv/bin/agent directly, not just $PATH

set -euo pipefail

# ---------------------------------------------------------------------------
# Arguments
# ---------------------------------------------------------------------------
RUNTIME="native"
for arg in "$@"; do
  case "$arg" in
    --runtime) ;;
    native|compose) RUNTIME="$arg" ;;
    --runtime=native) RUNTIME="native" ;;
    --runtime=compose) RUNTIME="compose" ;;
    *)
      echo "Usage: $0 [--runtime native|compose]" >&2
      exit 1
      ;;
  esac
done

# ---------------------------------------------------------------------------
# Resolve project root
# ---------------------------------------------------------------------------
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

echo ""
echo "─────────────────────────────────────────────────"
echo "  strands-multi-engineer-agent — bootstrap"
echo "  runtime: ${RUNTIME}"
echo "─────────────────────────────────────────────────"
echo ""

# ---------------------------------------------------------------------------
# 1. Python version check
# ---------------------------------------------------------------------------
REQUIRED_MAJOR=3
REQUIRED_MINOR=11
PYTHON_BIN="${PYTHON_BIN:-python3}"

if ! command -v "$PYTHON_BIN" > /dev/null 2>&1; then
  echo "✗  '$PYTHON_BIN' not found. Install Python ${REQUIRED_MAJOR}.${REQUIRED_MINOR}+ first."
  exit 1
fi

python_version=$("$PYTHON_BIN" --version 2>&1 | awk '{print $2}')
python_major=$(echo "$python_version" | cut -d. -f1)
python_minor=$(echo "$python_version" | cut -d. -f2)

if [[ "$python_major" -lt "$REQUIRED_MAJOR" ]] || \
   [[ "$python_major" -eq "$REQUIRED_MAJOR" && "$python_minor" -lt "$REQUIRED_MINOR" ]]; then
  echo "✗  Python ${REQUIRED_MAJOR}.${REQUIRED_MINOR}+ required (found ${python_version})"
  exit 1
fi
echo "✓  Python ${python_version}"

# ---------------------------------------------------------------------------
# 2. Docker checks (compose runtime only)
# ---------------------------------------------------------------------------
if [[ "$RUNTIME" == "compose" ]]; then
  if ! command -v docker > /dev/null 2>&1; then
    echo "✗  docker not found — required for compose runtime"
    exit 1
  fi
  echo "✓  docker $(docker --version | awk '{print $3}' | tr -d ',')"

  if ! docker compose version > /dev/null 2>&1; then
    echo "✗  'docker compose' plugin not found — required for compose runtime"
    echo "   Install: https://docs.docker.com/compose/install/"
    exit 1
  fi
  echo "✓  docker compose $(docker compose version --short 2>/dev/null || echo 'available')"
fi

# ---------------------------------------------------------------------------
# 3. Create local virtual environment (venv — no dot prefix)
#
# NOTE: We intentionally use "venv" (not ".venv") to avoid a Python 3.14
# regression: macOS sets the UF_HIDDEN flag on files inside dotfile
# directories, and Python 3.14 skips .pth files that carry that flag.
# Using a non-dotfile directory sidesteps the issue entirely.
# ---------------------------------------------------------------------------
VENV_DIR="${ROOT_DIR}/venv"

if [[ -d "$VENV_DIR" ]]; then
  echo "→  venv already exists, skipping creation"
else
  if command -v uv > /dev/null 2>&1; then
    echo "→  Creating venv with uv"
    uv venv "$VENV_DIR" --python "$PYTHON_BIN"
  else
    echo "→  Creating venv with python -m venv"
    "$PYTHON_BIN" -m venv "$VENV_DIR"
  fi
  echo "✓  venv created at ${VENV_DIR}"
fi

# Resolve venv binaries regardless of activation state
VENV_PYTHON="${VENV_DIR}/bin/python"
VENV_PIP="${VENV_DIR}/bin/pip"

# ---------------------------------------------------------------------------
# 4. Install dependencies into venv
# ---------------------------------------------------------------------------
if command -v uv > /dev/null 2>&1; then
  echo "→  Installing dependencies with uv into venv"
  uv pip install --python "$VENV_PYTHON" -e ".[dev]"
else
  echo "→  Installing dependencies with pip into venv"
  "$VENV_PIP" install --upgrade pip --quiet
  "$VENV_PIP" install -e ".[dev]" --quiet
fi
echo "✓  Dependencies installed"

# ---------------------------------------------------------------------------
# 5. Copy .env.example → .env (skip if already present)
# ---------------------------------------------------------------------------
if [[ ! -f ".env" ]]; then
  cp .env.example .env
  echo "✓  Created .env from .env.example — fill in your API keys before running"
else
  echo "→  .env already exists, skipping copy"
fi

# ---------------------------------------------------------------------------
# 6. Ensure eval/results directory exists
# ---------------------------------------------------------------------------
mkdir -p eval/results
echo "✓  eval/results directory ready"

# ---------------------------------------------------------------------------
# 7. CLI smoke test — check venv/bin/agent directly
# ---------------------------------------------------------------------------
VENV_AGENT="${VENV_DIR}/bin/agent"
if [[ -x "$VENV_AGENT" ]]; then
  if "$VENV_AGENT" --help > /dev/null 2>&1; then
    echo "✓  CLI smoke test passed (${VENV_AGENT} --help)"
  else
    echo "⚠  CLI entrypoint exists but import failed — check install logs"
  fi
else
  echo "⚠  CLI entrypoint not found at ${VENV_AGENT}"
  echo "   Ensure the package installed correctly (check pyproject.toml [project.scripts])"
fi

# ---------------------------------------------------------------------------
# Done
# ---------------------------------------------------------------------------
echo ""
echo "─────────────────────────────────────────────────"
echo "  Bootstrap complete."
echo ""
echo "  Activate your environment:"
echo "    source venv/bin/activate"
echo ""
echo "  Next steps:"
echo "    1. Edit .env with your API keys"
echo "    2. agent doctor"
echo "    3. agent list-tasks"
echo "    4. agent run"

if [[ "$RUNTIME" == "compose" ]]; then
  echo ""
  echo "  Docker Compose (Ollama):"
  echo "    make compose-up"
  echo "    docker compose exec ollama ollama pull llama3"
  echo "    docker compose run --rm agent agent run --provider ollama"
fi

echo "─────────────────────────────────────────────────"
echo ""
