# Extender Workspace

`extender_workspace` is the ROS 2 workspace entry point for the ISIR Extender
robot control stack. It brings together the robot abstraction layer,
controllers, robot-specific integrations, tooling, and operator input packages
needed to build and test Extender controller workflows from one checkout.

The core control architecture is:

```text
robot_interfaces
  -> controllers
  -> robot integrations, tools, and input_interfaces
```

For tablet-based integration tests, the current stable operator path is:

```text
extender_ui
  -> input_interfaces/tablet_interface
  -> controllers/sandbox_controller
  -> robot_interfaces + tools
```

New controller and teleoperation workflows should use **Sandbox V0.0** as the
reference integration setup. Petanque packages are kept as legacy/example
workflows and should not be used as the default template for new development.

<p align="center">
  <img alt="ROS 2" src="https://img.shields.io/badge/ROS%202-Humble-22314e?style=for-the-badge" />
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
- `visual_servoing` is included in the workspace manifest so the visual servoing
  UI/backend pipeline can be tested from the same local checkout.
- `extender_ui` is imported through `extender.repos` so frontend/backend work can
  be kept in one local workspace.
- Generated ROS folders (`build*`, `install*`, `log*`) are local artifacts and
  should never be committed.
- Ubuntu 24.04 and the next ROS 2 distribution are an active migration target,
  but the current documented baseline remains Ubuntu 22.04 with ROS 2 Humble.

## Repository Map

Repositories imported by `extender.repos`:

| Folder | Repository | Purpose |
| --- | --- | --- |
| `src/controllers` | `ISIR-EXTENDER/controllers` | Robot and sandbox controllers, including `sandbox_controller`. |
| `src/input_interfaces` | `ISIR-EXTENDER/input_interfaces` | Input/backend packages, including `tablet_interface`. |
| `src/robot_interfaces` | `ISIR-EXTENDER/robot_interfaces` | Shared robot abstractions and ROS messages. |
| `src/tools` | `ISIR-EXTENDER/tools` | Tools such as `apriltag_detector` and shared message packages. |
| `src/visual_servoing` | `ISIR-EXTENDER/visual_servoing` | Robin's visual servoing package and AprilTag-based control pipeline. |
| `src/qontrol_controllers` | `ISIR-EXTENDER/qontrol_controller` | Qontrol controller integration. |
| `src/explorer_stack` | `ISIR-EXTENDER/explorer_stack` | Explorer robot stack and `explorer_input_devices`. |
| `src/hub` | `ISIR-EXTENDER/hub` | Hub and digital output integration. |
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

Ubuntu 22.04 and ROS 2 Humble are the current expected baseline.

> Ubuntu 24.04 and the next ROS 2 upgrade are in progress. Do not assume that a
> fresh Ubuntu 24.04 machine is the reference setup until the migration is
> validated and this README is updated.

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
  ros-humble-cv-bridge \
  ros-humble-image-transport \
  ros-humble-apriltag \
  ros-humble-apriltag-ros \
  ros-humble-usb-cam
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
source /opt/ros/humble/setup.bash
rosdep install --from-paths src --ignore-src -r -y
```

### 6. Build

```bash
colcon build --symlink-install --packages-up-to robot_interfaces
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
source /opt/ros/humble/setup.bash
source install/setup.bash 2>/dev/null || true
colcon build --symlink-install --packages-select tablet_interface
```

### Run The Tablet Backend

```bash
source /opt/ros/humble/setup.bash
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

Use **Sandbox V0.0** for new integration tests.

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
colcon build --symlink-install --packages-select sandbox_controller
```

### A Camera Is Busy

Close browser tabs or ROS nodes using the same `/dev/video*` device. This matters
when switching between browser webcam widgets and ROS camera nodes such as
`usb_cam`.

## Bloom Migration

[`Bloom`](https://github.com/ISIR-EXTENDER/bloom) is the WIP next-generation
robot UI platform. It is being developed as a monorepo that combines frontend,
backend API, widget contracts, runtime safety rules, storage, and ROS adapters.

Until Bloom is accepted for the same robot workflows, this workspace remains the
stable integration target for `extender_ui`, `tablet_interface`, Sandbox V0.0,
and the current ROS packages.

## Contributing

- Write README content, comments, PR descriptions, and shared docs in English.
- Keep generated `build*`, `install*`, `log*`, `.venv/`, and local logs out of
  commits.
- Commit dependency changes as `pyproject.toml` + `uv.lock` together.
- Prefer Sandbox V0.0 for new integration work.
- Treat Petanque packages as legacy/example workflows unless the task is
  explicitly Petanque maintenance.
