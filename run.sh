#!/usr/bin/env bash
# Deprecated wrapper. The original single-app docker build/run and the
# log_parser/LaTeX post-processing were replaced by the unified pipeline.
# Everything (adapt -> fit with 5 tools -> score -> report) is driven by
# run_pipeline.sh, so this just forwards to it.
exec bash "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/run_pipeline.sh" "$@"
