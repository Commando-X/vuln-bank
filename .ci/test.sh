#!/usr/bin/env bash
set -eux -o pipefail

mkdir -p reports

pytest tests/ --junitxml=reports/unit-test-results.xml
