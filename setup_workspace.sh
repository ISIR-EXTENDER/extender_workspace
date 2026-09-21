#!/usr/bin/env bash
set -euo pipefail

SRC_DIR="${SRC_DIR:-src}"

mkdir -p "$SRC_DIR"

# Required dependencies
vcs import "$SRC_DIR" --skip-existing < extender.repos

# Optional Kortex stack
if [[ "${WITH_KORTEX:-0}" == "1" ]]; then
    echo "Importing ros2_kortex..."
    vcs import "$SRC_DIR" --skip-existing < kinova.repos

    echo "Importing ros2_kortex dependencies..."
    vcs import "$SRC_DIR" \
        --skip-existing \
        --input "$SRC_DIR/ros2_kortex/ros2_kortex-not-released.jazzy.repos"
fi