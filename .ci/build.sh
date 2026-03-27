#!/usr/bin/env bash
set -eux -o pipefail

pip install vendor/swigdojo-target/
pip install -r requirements.txt
pip install pytest pytest-asyncio
