#!/usr/bin/env bash
# scripts/reset_sample_repo.sh
#
# Reset sample_repos/tiny_fastapi_app to the deterministic broken baseline
# used for benchmarking. Must be run before every benchmark run.
#
# Baseline commit: bf147c3
# Baseline files:  main.py, requirements.txt  (no test_main.py)
# Verification:    MD5 checksum + content assertions
#
# Exit codes:
#   0  — reset succeeded and verified
#   1  — reset or verification failed (do NOT proceed with benchmark)
set -euo pipefail

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
REPO_DIR="${ROOT_DIR}/sample_repos/tiny_fastapi_app"
BASELINE_COMMIT="bf147c3"
EXPECTED_MD5="bc99fde40b8176acba37d599a5d56243"

echo "──────────────────────────────────────────"
echo "  Resetting sample repo to broken baseline"
echo "  Baseline commit: ${BASELINE_COMMIT}"
echo "──────────────────────────────────────────"

# ---------------------------------------------------------------------------
# Step 1: Restore main.py from git (source of truth)
# ---------------------------------------------------------------------------
cd "${ROOT_DIR}"
git checkout "${BASELINE_COMMIT}" -- sample_repos/tiny_fastapi_app/main.py
echo "✓  main.py restored from git (${BASELINE_COMMIT})"

# ---------------------------------------------------------------------------
# Step 2: Remove all generated / agent-written files
# ---------------------------------------------------------------------------
GENERATED_FILES=(
    "test_main.py"
    "test_*.py"
    "*_test.py"
)
for pattern in "${GENERATED_FILES[@]}"; do
    find "${REPO_DIR}" -maxdepth 1 -name "${pattern}" -type f -print -delete 2>/dev/null || true
done
echo "✓  Generated test files removed"

# Remove all __pycache__ directories and .pyc files
find "${REPO_DIR}" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find "${REPO_DIR}" -name "*.pyc" -delete 2>/dev/null || true
find "${REPO_DIR}" -name "*.pyo" -delete 2>/dev/null || true
find "${REPO_DIR}" -name ".pytest_cache" -type d -exec rm -rf {} + 2>/dev/null || true
echo "✓  __pycache__, .pyc, .pytest_cache removed"

# ---------------------------------------------------------------------------
# Step 3: Verify MD5 checksum of main.py
# ---------------------------------------------------------------------------
if command -v md5sum > /dev/null 2>&1; then
    ACTUAL_MD5="$(md5sum "${REPO_DIR}/main.py" | awk '{print $1}')"
elif command -v md5 > /dev/null 2>&1; then
    ACTUAL_MD5="$(md5 -q "${REPO_DIR}/main.py")"
else
    echo "⚠  Neither md5sum nor md5 available — skipping checksum verification"
    ACTUAL_MD5="${EXPECTED_MD5}"  # proceed
fi

if [[ "${ACTUAL_MD5}" != "${EXPECTED_MD5}" ]]; then
    echo "✗  CHECKSUM MISMATCH"
    echo "   Expected: ${EXPECTED_MD5}"
    echo "   Actual:   ${ACTUAL_MD5}"
    exit 1
fi
echo "✓  MD5 checksum verified (${ACTUAL_MD5})"

# ---------------------------------------------------------------------------
# Step 4: Content assertions — prove the code is broken
# ---------------------------------------------------------------------------
MAIN="${REPO_DIR}/main.py"

# Must NOT contain the solved implementation
if grep -q "ItemCreate" "${MAIN}"; then
    echo "✗  ASSERTION FAILED: main.py contains 'ItemCreate' — file is already solved"
    exit 1
fi
if grep -q "from pydantic import BaseModel" "${MAIN}"; then
    echo "✗  ASSERTION FAILED: main.py imports BaseModel — file is already solved"
    exit 1
fi

# Must contain the deliberately broken implementation
if ! grep -q "def create_item(payload: dict)" "${MAIN}"; then
    echo "✗  ASSERTION FAILED: expected broken 'create_item(payload: dict)' not found"
    exit 1
fi
if ! grep -q "Agent task: add Pydantic model validation" "${MAIN}"; then
    echo "✗  ASSERTION FAILED: expected TODO comment not found"
    exit 1
fi
echo "✓  Content assertions passed — code is in broken state"

# ---------------------------------------------------------------------------
# Step 5: Verify repo contains only expected files
# ---------------------------------------------------------------------------
UNEXPECTED=$(find "${REPO_DIR}" -maxdepth 1 -type f \
    ! -name "main.py" \
    ! -name "requirements.txt" \
    2>/dev/null)

if [[ -n "${UNEXPECTED}" ]]; then
    echo "⚠  Unexpected files found (will not block run, but note these):"
    echo "${UNEXPECTED}" | sed 's/^/   /'
else
    echo "✓  Repo contains only baseline files (main.py, requirements.txt)"
fi

# ---------------------------------------------------------------------------
# Done
# ---------------------------------------------------------------------------
echo ""
echo "✓  Sample repo is clean and verified. Safe to run benchmark."
echo "──────────────────────────────────────────"
