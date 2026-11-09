#!/usr/bin/env bash
set -euo pipefail
root=$(pwd)
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
python -m pip wheel --no-deps --wheel-dir "$tmp/wheels" .
python -m venv "$tmp/env"
"$tmp/env/bin/pip" install --no-deps "$tmp"/wheels/*.whl
cd "$tmp"
"$tmp/env/bin/python" "$root/tools/verify_installed.py" "$root/docs/controls.json" "$tmp/env/bin/dfalab" "$root/docs/conformance-controls.json" "$tmp/env/bin/dfalab-conformance" "$root/docs/fault-atlas-controls.json" "$tmp/env/bin/dfalab-fault-atlas"
