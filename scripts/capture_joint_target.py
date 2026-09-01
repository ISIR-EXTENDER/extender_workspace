#!/usr/bin/env python3
"""Capture a named joint target for ``cartesian_manager`` from the live robot.

Move the arm to the pose you want, run this, and it prints the complete
``behaviours.joint_targets`` block to paste into
``cartesian_manager/bringup/config/explorer_params.yaml``.

Why a tool rather than editing the YAML by hand:

- ``positions`` is a single **flattened** array across every entry in
  ``target_names``, in that order. Adding a target means appending exactly
  ``len(joint_names)`` values in the right place, and the manager rejects the
  config unless ``len(positions) == len(joint_names) * len(target_names)``.
  That is easy to get wrong by hand and the failure is a node that will not
  start.
- ``/joint_states`` is not guaranteed to publish joints in the manager's
  ``joint_names`` order, so values must be matched by name, not by index.

Usage::

    ros2 run ...                                  # manager running
    python3 scripts/capture_joint_target.py boire

    # keep existing targets and append the new one
    python3 scripts/capture_joint_target.py boire --merge

    # read the joint order from a config file instead of the running node
    python3 scripts/capture_joint_target.py boire --params-file <path>
"""

from __future__ import annotations

import argparse
import sys
from typing import Sequence

DEFAULT_NODE = "/cartesian_manager"
DEFAULT_TIMEOUT = 5.0


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("target_name", help="Name for the captured pose, such as 'boire'.")
    parser.add_argument(
        "--merge",
        action="store_true",
        help="Append to the targets already configured on the running manager.",
    )
    parser.add_argument(
        "--params-file",
        default=None,
        help="Read joint_names and existing targets from a YAML file instead of the running node.",
    )
    parser.add_argument("--node", default=DEFAULT_NODE, help=f"Manager node name (default {DEFAULT_NODE}).")
    parser.add_argument(
        "--joint-states-topic",
        default="/joint_states",
        help="Topic carrying the current joint positions.",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=DEFAULT_TIMEOUT,
        help=f"Seconds to wait for a joint state message (default {DEFAULT_TIMEOUT}).",
    )
    return parser.parse_args(argv)


def read_config_from_file(path: str) -> tuple[list[str], list[str], list[float]]:
    import yaml

    with open(path, encoding="utf-8") as handle:
        document = yaml.safe_load(handle)

    node = document.get("cartesian_manager", {})
    params = node.get("ros__parameters", {})
    targets = params.get("behaviours", {}).get("joint_targets", {})
    joint_names = [str(name) for name in targets.get("joint_names", [])]
    target_names = [str(name) for name in targets.get("target_names", [])]
    positions = [float(value) for value in targets.get("positions", [])]
    return joint_names, target_names, positions


def read_config_from_node(node, manager_node_name: str, timeout: float):
    """Read the manager's joint-target parameters over the ROS parameter service."""
    from rcl_interfaces.srv import GetParameters

    client = node.create_client(GetParameters, f"{manager_node_name}/get_parameters")
    if not client.wait_for_service(timeout_sec=timeout):
        raise RuntimeError(
            f"No parameter service at {manager_node_name}/get_parameters. "
            "Is cartesian_manager running? Use --params-file to work offline."
        )

    request = GetParameters.Request()
    request.names = [
        "behaviours.joint_targets.joint_names",
        "behaviours.joint_targets.target_names",
        "behaviours.joint_targets.positions",
    ]
    import rclpy

    future = client.call_async(request)
    rclpy.spin_until_future_complete(node, future, timeout_sec=timeout)
    response = future.result()
    if response is None:
        raise RuntimeError("Timed out reading joint-target parameters from the manager.")

    joint_names = list(response.values[0].string_array_value)
    target_names = list(response.values[1].string_array_value)
    positions = list(response.values[2].double_array_value)
    return joint_names, target_names, positions


def capture_joint_positions(node, topic: str, joint_names: Sequence[str], timeout: float) -> list[float]:
    """Return current positions ordered to match ``joint_names``.

    Matching is by name because /joint_states publishes in its own order.
    """
    import rclpy
    from sensor_msgs.msg import JointState

    received: dict[str, float] = {}
    done = {"ok": False}

    def on_joint_state(message: JointState) -> None:
        if not message.name or not message.position:
            return
        for name, position in zip(message.name, message.position):
            received[str(name)] = float(position)
        if all(name in received for name in joint_names):
            done["ok"] = True

    subscription = node.create_subscription(JointState, topic, on_joint_state, 10)
    try:
        deadline = node.get_clock().now().nanoseconds + int(timeout * 1e9)
        while not done["ok"] and node.get_clock().now().nanoseconds < deadline:
            rclpy.spin_once(node, timeout_sec=0.1)
    finally:
        node.destroy_subscription(subscription)

    missing = [name for name in joint_names if name not in received]
    if missing:
        raise RuntimeError(
            f"No position on {topic} for: {', '.join(missing)}. "
            f"Seen: {', '.join(sorted(received)) or '<nothing>'}"
        )

    return [received[name] for name in joint_names]


def build_targets_block(
    joint_names: Sequence[str],
    target_names: Sequence[str],
    positions: Sequence[float],
) -> str:
    """Render the YAML block, and refuse to emit an invalid one."""
    expected = len(joint_names) * len(target_names)
    if len(positions) != expected:
        raise ValueError(
            f"positions has {len(positions)} values but {len(joint_names)} joints "
            f"x {len(target_names)} targets needs {expected}"
        )

    lines = ["      joint_targets:", "        joint_names:"]
    lines += [f"          - {name}" for name in joint_names]
    lines.append("        target_names:")
    lines += [f"          - {name}" for name in target_names]
    lines.append("        positions:")

    for index, target in enumerate(target_names):
        chunk = positions[index * len(joint_names) : (index + 1) * len(joint_names)]
        lines.append(f"          # {target}")
        lines += [f"          - {value:.4f}" for value in chunk]

    return "\n".join(lines)


def compose(
    joint_names: Sequence[str],
    existing_targets: Sequence[str],
    existing_positions: Sequence[float],
    target_name: str,
    captured: Sequence[float],
    merge: bool,
) -> tuple[list[str], list[float]]:
    if not merge:
        return [target_name], list(captured)

    if target_name in existing_targets:
        index = list(existing_targets).index(target_name)
        positions = list(existing_positions)
        positions[index * len(joint_names) : (index + 1) * len(joint_names)] = list(captured)
        return list(existing_targets), positions

    return list(existing_targets) + [target_name], list(existing_positions) + list(captured)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)

    try:
        import rclpy
        from rclpy.node import Node
    except ModuleNotFoundError:
        print("ROS 2 Python packages not found. Source the workspace first.", file=sys.stderr)
        return 1

    rclpy.init()
    node = Node("capture_joint_target")
    try:
        if args.params_file:
            joint_names, target_names, positions = read_config_from_file(args.params_file)
        else:
            joint_names, target_names, positions = read_config_from_node(node, args.node, args.timeout)

        if not joint_names:
            print("The manager reports no joint_names. Nothing to capture against.", file=sys.stderr)
            return 1

        print(f"Joint order: {', '.join(joint_names)}", file=sys.stderr)
        print(f"Existing targets: {', '.join(target_names) or '<none>'}", file=sys.stderr)
        print(f"Reading {args.joint_states_topic} ...", file=sys.stderr)

        captured = capture_joint_positions(node, args.joint_states_topic, joint_names, args.timeout)

        next_targets, next_positions = compose(
            joint_names, target_names, positions, args.target_name, captured, args.merge
        )
        block = build_targets_block(joint_names, next_targets, next_positions)
    except (RuntimeError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    finally:
        node.destroy_node()
        rclpy.shutdown()

    print(f"\n# Paste under cartesian_manager.ros__parameters.behaviours", file=sys.stderr)
    print(block)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
