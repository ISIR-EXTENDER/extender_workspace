# Extender Workspace

`extender_workspace` is the ROS 2 workspace entry point for the ISIR Extender
robot control stack. It brings together the robot abstraction layer,
the active controller, manager layer, robot-specific integrations, tooling, and
operator input packages needed to build and test Extender workflows from one
checkout.

The core control architecture is:

```text
operator inputs and robot integrations
  -> cartesian_manager
  -> qontrol_controller
```

For tablet-based integration tests, the current stable operator path is:

```text
extender_ui
  -> input_interfaces/tablet_interface
  -> cartesian_manager
  -> qontrol_controller
```

New teleoperation workflows should go through `cartesian_manager` and keep robot
control authority in `qontrol_controller`. Older standalone controller packages
and Petanque packages are kept as legacy/example workflows and should not be
used as the default template for new development.

<p align="center">
  <img alt="ROS 2" src="https://img.shields.io/badge/ROS%202-Jazzy-22314e?style=for-the-badge" />
  <img alt="uv" src="https://img.shields.io/badge/uv-Python%20env-4b5563?style=for-the-badge" />
  <img alt="colcon" src="https://img.shields.io/badge/colcon-build-2563eb?style=for-the-badge" />
</p>

<p align="center">
  <a href="#current-state">Current State</a> ·
  <a href="#repository-map">Repository Map</a> ·
  <a href="#quick-start">Quick Start</a> ·
  <a href="#uv-how-to">uv How-To</a> ·
  <a href="#build-and-run">Build And Run</a> ·
  <a href="#common-issues">Common Issues</a> ·
  <a href="#bloom-migration">Bloom Migration</a>
</p>

## Current State

- VCS manifest for the Extender ROS 2 repositories.
- Workspace-level `pyproject.toml` and `uv.lock`.
- Shared Python dependencies for `tablet_interface`, ROS build helpers, tests,
  and optional vision tools.
- `extender_ui` is imported through `extender.repos` so frontend/backend work can
  be kept in one local workspace.
- `qontrol_controller` is the active robot controller integration.
- `cartesian_manager` is the coordination layer between operator command sources
  and `qontrol_controller`.
- Generated ROS folders (`build*`, `install*`, `log*`) are local artifacts and
  should never be committed.
- Ubuntu 24.04 with ROS 2 Jazzy is the documented baseline. The Extender and
  Kinova computers both run it.

## Repository Map

Repositories imported by `extender.repos`:

| Folder | Repository | Purpose |
| --- | --- | --- |
| `src/input_interfaces` | `ISIR-EXTENDER/input_interfaces` | Input/backend packages, including `tablet_interface`. |
| `src/tools` | `ISIR-EXTENDER/tools` | Tools such as `apriltag_detector` and shared message packages. |
| `src/qontrol_controllers` | `ISIR-EXTENDER/qontrol_controller` | Active controller integration for robot motion. |
| `src/cartesian_manager` | `ISIR-EXTENDER/cartesian_manager` | Manager layer that routes Cartesian commands and named joint targets to `qontrol_controller`. |
| `src/explorer_stack` | `ISIR-EXTENDER/explorer_stack` | Explorer robot stack and `explorer_input_devices`. |
| `src/extender-ui` | `ISIR-EXTENDER/extender_ui` | React tablet frontend and screen builder. |

Local-only generated folders:

| Folder | Meaning |
| --- | --- |
| `build/`, `build.*` | Colcon build outputs. |
| `install/`, `install.*` | Colcon install outputs. |
| `log/`, `log.*` | Colcon logs. |
| `.venv/` | uv-managed Python virtual environment. |

## Quick Start

### 1. Install System Tools

Ubuntu 24.04 and ROS 2 Jazzy are the expected baseline.

> Ubuntu 22.04 with ROS 2 Humble is retired. To move an existing Humble machine
> over, see [Upgrading From Humble](#upgrading-from-humble).

```bash
sudo apt update
sudo apt install -y \
  build-essential \
  cmake \
  git \
  pkg-config \
  python3-colcon-common-extensions \
  python3-rosdep \
  python3-vcstool \
  libeigen3-dev \
  ros-jazzy-cv-bridge \
  ros-jazzy-image-transport \
  ros-jazzy-apriltag \
  ros-jazzy-apriltag-ros \
  ros-jazzy-usb-cam
```

Initialize rosdep once per machine:

```bash
sudo rosdep init || true
rosdep update
```

### 2. Clone The Workspace

```bash
mkdir -p ~/workspace/extender
cd ~/workspace/extender
git clone https://github.com/ISIR-EXTENDER/extender_workspace.git
cd extender_workspace
```

### 3. Import Repositories

Run `vcs import` from the workspace repository root:

```bash
vcs import src < extender.repos --workers 1
```

This populates `src/` with the repositories listed in `extender.repos`.

### 4. Install Python Dependencies With uv

```bash
uv sync --extra ros-build --extra dev
```

Use `--extra vision` only when working on vision/MediaPipe workflows:

```bash
uv sync --extra ros-build --extra dev --extra vision
```

### 5. Install ROS Dependencies

```bash
source /opt/ros/jazzy/setup.bash
rosdep install --from-paths src --ignore-src -r -y
```

### 6. Build

```bash
colcon build --symlink-install --packages-up-to cartesian_manager
source install/setup.bash
colcon build --symlink-install
```

Use `install/setup.zsh` instead of `install/setup.bash` when working in zsh.

## uv How-To

Use `uv` only from the `extender_workspace` repository root, where
`pyproject.toml` and `uv.lock` live.

### Install uv

If `uv` is not installed:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Restart the shell or make sure the uv binary is on `PATH`, then verify:

```bash
uv --version
```

### Create Or Refresh The Environment

Most developers should run:

```bash
uv sync --extra ros-build --extra dev
```

This creates `.venv/` if needed and installs:

- runtime Python packages for `tablet_interface`;
- ROS build helper packages such as `empy`, `catkin-pkg`, and `lark`;
- development/test packages such as `pytest`.

Use the vision extra only when needed:

```bash
uv sync --extra vision
```

### Run Python Commands

Preferred pattern:

```bash
uv run python -m pytest src/input_interfaces/tablet_interface/test
uv run python -m tablet_interface.main --help
```

Alternative pattern:

```bash
source .venv/bin/activate
python -m pytest src/input_interfaces/tablet_interface/test
```

Do not mix random global `pip install` commands into the workspace when a
dependency belongs in this repository. Add it to `pyproject.toml`, refresh
`uv.lock`, and commit both files.

### Add Or Update Dependencies

Runtime dependency:

```bash
uv add <package>
```

Development-only dependency:

```bash
uv add --dev <package>
```

After dependency changes, review both files:

```bash
git diff -- pyproject.toml uv.lock
```

Commit `pyproject.toml` and `uv.lock` together. A dependency PR with only one of
those files is incomplete.

### Common uv Mistakes

| Mistake | Fix |
| --- | --- |
| Running `uv sync` from a sub-repository | Go back to the `extender_workspace` root first. |
| Activating an old `.venv` from another project | Run `deactivate`, then use `uv run ...` or `source .venv/bin/activate` from this repo. |
| Installing backend packages globally with `pip` | Use `uv add` for real dependencies, or `uv run` for commands. |
| Forgetting extras before ROS builds | Use `uv sync --extra ros-build --extra dev`. |
| Committing generated folders | Keep `build*`, `install*`, `log*`, `.venv/`, and cloned `src/*` repos out of commits. |

## Build And Run

### Build One Package

```bash
source /opt/ros/jazzy/setup.bash
source install/setup.bash 2>/dev/null || true
colcon build --symlink-install --packages-select tablet_interface
```

### Run The Tablet Backend

```bash
source /opt/ros/jazzy/setup.bash
source install/setup.bash
cd src/input_interfaces/tablet_interface
make run-node
```

The frontend connects to:

```text
ws://127.0.0.1:8765/ws/control
```

### Run The Frontend

```bash
cd src/extender-ui
npm install
npm run dev
```

Use `cartesian_manager` plus `qontrol_controller` for new integration tests.

### Run Backend Tests

```bash
cd src/input_interfaces/tablet_interface
make test
```

## Common Issues

### `ModuleNotFoundError: yaml`

Refresh the workspace Python environment:

```bash
cd /path/to/extender_workspace
uv sync --extra ros-build --extra dev
```

`PyYAML` is part of the base workspace dependencies because
`tablet_interface` uses it for typed ROS message payloads.

### `vcs import` Clones In The Wrong Place

Run from the workspace repository root:

```bash
cd /path/to/extender_workspace
vcs import src < extender.repos --workers 1
```

Do not run the command from inside `src/`.

### Colcon Builds Too Much

Build only what you need:

```bash
colcon build --symlink-install --packages-select tablet_interface
colcon build --symlink-install --packages-select cartesian_manager
```

### Upgrading From Humble

A `do-release-upgrade` to 24.04 leaves the Humble stack unusable rather than
merely outdated: its Python packages target 3.10 while the system moves to 3.12,
so `ros2` stops working even though the C++ libraries still resolve. After the
release upgrade completes:

```bash
# repoint the ROS, robotpkg, and kitware sources at noble
sudo sed -i 's/^Suites: jammy/Suites: noble/' /etc/apt/sources.list.d/ros2.sources
sudo sed -i 's/ jammy / noble /' \
  /etc/apt/sources.list.d/robotpkg.list \
  /etc/apt/sources.list.d/kitware.list
sudo apt update

sudo apt purge -y 'ros-humble-*'
sudo apt autoremove -y
sudo apt install -y ros-jazzy-desktop ros-dev-tools \
  python3-colcon-common-extensions python3-rosdep python3-vcstool
```

Three things must then be rebuilt from scratch, because all of them are tied to
the old Python and the old ROS prefix:

- every `build*`, `install*`, and `log*` folder in the workspace;
- `.venv` (`rm -rf .venv && uv sync --extra ros-build --extra dev`), since a venv
  created under Python 3.10 keeps pointing at an interpreter that no longer
  matches its `site-packages`;
- any `source /opt/ros/humble/setup.bash` line in your shell rc.

### `colcon build` Fails With A CMake Policy Error

Kitware's apt repository ships CMake 4.x, which turns a pre-3.5
`cmake_minimum_required` into a hard error instead of a warning. Vendored
third-party trees still trigger it, for example `qpmad`, which
`qontrol_controller` pulls in through FetchContent:

```text
CMake Error at build/qontrol_controller/_deps/qpmad-src/CMakeLists.txt:2
  Compatibility with CMake < 3.5 has been removed from CMake.
```

Pass the policy escape hatch on every build:

```bash
colcon build --symlink-install --cmake-args -DCMAKE_POLICY_VERSION_MINIMUM=3.5
```

Ubuntu 24.04's own CMake (3.28.3) does not need this. Only machines using the
Kitware repository do.

### A Camera Is Busy

Close browser tabs or ROS nodes using the same `/dev/video*` device. This matters
when switching between browser webcam widgets and ROS camera nodes such as
`usb_cam`.

## Bloom Migration

[`Bloom`](https://github.com/ISIR-EXTENDER/bloom) is the WIP next-generation
robot UI platform. It is being developed as a monorepo that combines frontend,
backend API, widget contracts, runtime safety rules, storage, and ROS adapters.

Until Bloom is accepted for the same robot workflows, this workspace remains the
stable integration target for `extender_ui`, `tablet_interface`,
`cartesian_manager`, `qontrol_controller`, and the current ROS packages.

## Contributing

- Write README content, comments, PR descriptions, and shared docs in English.
- Keep generated `build*`, `install*`, `log*`, `.venv/`, and local logs out of
  commits.
- Commit dependency changes as `pyproject.toml` + `uv.lock` together.
- Prefer `cartesian_manager` and `qontrol_controller` for new integration work.
- Treat Petanque packages as legacy/example workflows unless the task is
  explicitly Petanque maintenance.
