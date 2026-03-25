#!/usr/bin/env bash
set -euo pipefail

ROSDISTRO="humble"

mkdir src

echo "[2/9] Cloning repositories from extender.repos"
if ! command -v vcs >/dev/null 2>&1; then
  echo "vcstool not installed. Installing..."
  sudo apt update && sudo apt install -y python3-vcstool
fi
vcs import src < extender.repos --workers 1

echo "[3/9] Installing system dependencies"
sudo apt update
sudo apt install -y \
  build-essential \
  cmake \
  git \
  python3-colcon-common-extensions \
  python3-rosdep \
  python3-vcstool \
  python3-pip \
  python3-rosdistro \
  python3-rosinstall \
  pkg-config \
  libeigen3-dev \
  libtbb-dev \
  libyaml-cpp-dev

# Node.js 20 from NodeSource
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt-get install -y nodejs

# Install uv via installer script as an extra fallback
curl -LsSf https://astral.sh/uv/install.sh | sh

sudo apt install -y \
  ros-${ROSDISTRO}-cv-bridge \
  ros-${ROSDISTRO}-image-transport \
  ros-${ROSDISTRO}-apriltag \
  ros-${ROSDISTRO}-apriltag-ros \
  ros-${ROSDISTRO}-usb-cam \
  ros-${ROSDISTRO}-robot-state-publisher \
  ros-${ROSDISTRO}-joint-state-publisher || true

echo "[4/9] Setup rosdep"
sudo rosdep init 2>/dev/null || true
rosdep update

echo "[5/9] Install rosdep package dependencies"
cd "$WORKSPACE"
rosdep install --from-paths src --ignore-src -r -y


echo "[6/9] Setup uv Python environment"
cd "$WORKSPACE/src/extender_workspace"
if ! command -v uv >/dev/null 2>&1; then
echo "Installing uv"
python3 -m pip install --user uv
export PATH="$HOME/.local/bin:$PATH"
fi
uv venv
uv sync
uv sync --extra dev --extra vision --extra ros-build || true

echo "[7/9] Bootstrap build - robot_interfaces first"
cd "$WORKSPACE"
colcon build --symlink-install --packages-select robot_interfaces extender_msgs explorer_command_controllers
source install/setup.zsh

echo "[8/9] Build full workspace"
colcon build --symlink-install --packages-skip explorer_command_controllers

echo "[9/9] Installation complete"
cat <<EOF
To use the workspace, run:
  source $WORKSPACE/install/setup.bash
If using uv venv:
  source $WORKSPACE/src/extender_workspace/.venv/bin/activate
EOF

exit 0
