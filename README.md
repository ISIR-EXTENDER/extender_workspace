# Extender Workspace

Extender Workspace is the top-level ROS 2 monorepo manager for the Extender project. It centralizes repository composition and dependency setup for all Extender packages, including motion controllers, input devices, kinematics libraries, simulation tools, and UIs.

## Quick install (recommended)

A helper script is included to automate setup from a clean Ubuntu + ROS2 environment. From the workspace root:

```bash
`git config --global credential.helper cache --timeout=3600`
chmod +x install_extender.sh
./install_extender.sh
```

Optional flags:

- `--no-uv` skip `uv` Python environment setup
- `--rosdistro <distro>` choose a ROS distribution (default: humble)
- `--workspace <path>` target workspace path (default: `~/ros2_humble_ws`)

## Quick overview

- Root path: `extender_workspace`
- VCS entrypoint: `extender.repos`
- Recommended ROS distribution: **ROS 2 Humble Hawksbill**
- Target Ubuntu release: **22.04 LTS**
- Build toolchain: `colcon` + `colcon-common-extensions`
- Optional Python environment manager: `uv`

## Repositories controlled by `extender.repos`

`extender.repos` imports:

- `input_interfaces` (main branch)
- `controllers` (main branch)
- `robot_interfaces` (main branch)
- `tools` (main branch)
- `qontrol_controllers` (branch: `refactor/chained_controller`)
- `explorer_stack` (main branch)
- `hub` (main branch)
- `extender-ui` (main branch)
- `sandbox_controller` (main branch)

These repositories are intended to be checked out under `extender_workspace/src/` via `vcs import`.

## Setup and installation

A helper script is included to automate setup from a clean Ubuntu + ROS2 environment. From the workspace root:

```bash
chmod +x install_extender.sh
./install_extender.sh
```

## Directory structure

```
extender_workspace/
├── extender.repos
├── pyproject.toml
├── uv.lock
├── src/  # imported repositories
│   ├── input_interfaces/
│   ├── controllers/
│   ├── robot_interfaces/
│   ├── tools/
│   ├── qontrol_controllers/
│   ├── explorer_stack/
│   ├── hub/
│   ├── extender-ui/
│   ├── sandbox_controller/
└── README.md
```

## Core components

- `robot_interfaces`: hardware-agnostic command/state layers, kinematics, path planning helpers.
- `controllers`: low-level and high-level control plugins (joint/cartesian, pick/place flow, etc.).
- `input_interfaces`: joystick, teleop, VR and interface bridging nodes (ROS topics/services).
- `tools`: perception bindings, calibration utilities, message packages, simulators.
- `qontrol_controllers`: chained controller to allow to use quadratic programming controller as low level controller.
- `explorer_stack`: integrated stack with explorer-specific launch and config.
- `hub`: docking and orchestration utilities.
- `extender-ui`: UI frontend for monitoring/control.
- `sandbox_controller`: development sandbox / quick prototyping controller.

## Development workflow

1. Checkout feature branch in each repository, maintain clean dependency graph.
2. Use `ros2 run` and `ros2 launch` from built workspace after sourcing.
3. Run tests per package:

```bash
colcon test --packages-select <package_name>
colcon test-result --verbose
```

4. Rebuild changed packages:

```bash
colcon build --symlink-install --packages-select <package_name>
```

5. Use `colcon graph` for dependency introspection if supported.

## Troubleshooting

- If your build fails with missing package, run `rosdep install --from-paths src --ignore-src -r -y` again.
- If it fails from conflicting versions or missing system libs, verify `apt` packages and ensure local branch matches `extender.repos` entries.
- For `.venv`/`uv` Python issues, remove and recreate env:

```bash
rm -rf .venv
uv venv
uv sync
```

- Use `colcon build --packages-select <package_name> --cmake-clean-cache` if stale CMake configuration seems stuck.

