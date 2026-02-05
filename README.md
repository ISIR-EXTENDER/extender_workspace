# Extender Workspace

This is the main workspace for the extender project.

## Installation

### Prerequisites (Ubuntu + ROS 2 Humble)

- Ubuntu 22.04 LTS
- ROS 2 Humble (installed via official instructions)
- Python 3.10+
- uv (Python package manager)
- Tools: `python3-rosdep`, `vcs`, `git`, `colcon-common-extensions`

1) Create the workspace and clone this repo

```bash
# from the src folder of your ROS 2 workspace
cd ~/ros2_humble_ws/src
git clone https://github.com/ISIR-EXTENDER/extender_workspace.git
cd ..
```

2) Configure git access (optional, for private repos)

```bash
# cache credentials temporarily for 1 hour
git config --local credential.helper 'cache --timeout=3600'
```

3) Clone all sub-repositories

```bash
cd src/extender_workspace
# imports repos listed in extender.repos
vcs import --input extender.repos --workers 1
```

4) Install system and ROS dependencies

```bash
# minimal installation (adjust based on your packages)
sudo apt update
sudo apt install -y \
	build-essential \
	cmake \
	python3-colcon-common-extensions \
	python3-rosdep \
	python3-vcstool \
	git \
	pkg-config \
	libeigen3-dev \
	ros-humble-cv-bridge \
	ros-humble-image-transport \
	ros-humble-apriltag \
	ros-humble-apriltag-ros \
	ros-humble-usb-cam

# initialize rosdep if not already done
sudo rosdep init || true
rosdep update

cd ~/ros2_humble_ws
rosdep install --from-paths src --ignore-src -r -y
```

4b) Set up Python dependencies with uv

```bash
# from workspace root
cd ~/ros2_humble_ws/src/extender_workspace

# create venv and install base deps from pyproject.toml
uv venv
uv sync

# optional extras
uv sync --extra dev
uv sync --extra vision
uv sync --extra ros-build --extra dev --extra vision
```

5) Build robot_interfaces first (other packages depend on it)

```bash
colcon build --symlink-install --packages-up-to robot_interfaces
source install/setup.zsh  # or source install/setup.bash if using bash
```

6) Build all remaining packages

```bash
colcon build --symlink-install
```

## Submodules

Main submodules and directories in `extender_workspace`:

- **`controllers/`** — ROS2 controller implementations (components and plugins) for robot control (e.g., `cartesian_velocity`, `joint_position_interpolator`, `kinematic_guides_cartesian_velocity`).
- **`input_interfaces/`** — Input device nodes and interfaces (joystick, teleoperation) that convert user commands into robot messages/commands.
- **`robot_interfaces/`** — Robot abstraction library (command/state interfaces, kinematics algorithms) used by controllers to support different robot types.
- **`tools/`** — Utility packages (e.g., `apriltag_detector`, `mediapipe_mocap`, `offline_media_publisher`, `extender_msgs` for shared message definitions).
- **`extender.repos`** — VCS configuration file listing repositories to import (used by `vcs import`).

For package-specific details, see each local README (e.g., `tools/apriltag_detector/Readme.md`) for specific instructions and optional dependencies.

## Folder architecture

```
extender_workspace/
├── controllers/
├── input_interfaces/
├── robot_interfaces/
├── tools/
├── extender.repos
├── pyproject.toml      # uv dependency definition
├── uv.lock             # locked Python environment
```

## Notes & Tips

- Use `install/setup.zsh` for zsh shell or `install/setup.bash` for bash.
- If you use `uv venv`, activate it with `source .venv/bin/activate` before running Python tools.
- Some optional packages (e.g., Franka support) require external dependencies; enable them in CMake options if needed.
- If `rosdep install` fails for pip packages not in apt, install them manually (`pip3 install --user <package>`).
- To rebuild a single package after modifications: `colcon build --packages-select <package_name>`.

### Using uv

- Create a virtual environment: `uv venv`
- Install/sync dependencies: `uv sync`
- Install with extras: `uv sync --extra ros-build --extra dev --extra vision`
- Update dependencies: `uv sync --upgrade`
- Add a dependency: `uv add <package>`
- Add a dev dependency: `uv add --dev <package>`
