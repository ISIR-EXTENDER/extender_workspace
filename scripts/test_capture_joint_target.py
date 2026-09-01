from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

from capture_joint_target import build_targets_block, compose, read_config_from_file

JOINTS = ["joint_1", "joint_2", "joint_3", "joint_4", "joint_5", "joint_6"]
HOME = [2.5, 0.3, -2.4, 2.97, 1.2, -0.5]
BOIRE = [1.0, -0.2, 0.5, 1.5, -1.0, 0.25]


def test_replace_mode_keeps_only_the_new_target() -> None:
    targets, positions = compose(JOINTS, ["home"], HOME, "boire", BOIRE, merge=False)

    assert targets == ["boire"]
    assert positions == BOIRE


def test_merge_appends_a_new_target_after_the_existing_ones() -> None:
    targets, positions = compose(JOINTS, ["home"], HOME, "boire", BOIRE, merge=True)

    assert targets == ["home", "boire"]
    # positions is one flat array in target_names order
    assert positions == HOME + BOIRE


def test_merge_overwrites_a_target_in_place() -> None:
    # Recapturing 'home' must replace its slice, not append a duplicate name.
    updated = [9.0] * 6
    targets, positions = compose(JOINTS, ["home", "boire"], HOME + BOIRE, "home", updated, merge=True)

    assert targets == ["home", "boire"]
    assert positions == updated + BOIRE


def test_block_refuses_an_inconsistent_flattening() -> None:
    # The manager will not start if this invariant is broken, so the tool must
    # never emit it.
    with pytest.raises(ValueError, match="needs 12"):
        build_targets_block(JOINTS, ["home", "boire"], HOME)


def test_block_renders_one_commented_chunk_per_target() -> None:
    block = build_targets_block(JOINTS, ["home", "boire"], HOME + BOIRE)

    assert "        target_names:\n          - home\n          - boire" in block
    assert "          # home" in block
    assert "          # boire" in block
    # 6 joint names + 2 target names + 12 position values
    assert block.count("          - ") == len(JOINTS) + 2 + len(JOINTS) * 2
    assert "- 2.5000" in block
    assert "- 0.2500" in block


def test_reads_the_real_explorer_params(tmp_path: Path) -> None:
    config = tmp_path / "explorer_params.yaml"
    config.write_text(
        "cartesian_manager:\n"
        "  ros__parameters:\n"
        "    behaviours:\n"
        "      joint_targets:\n"
        "        joint_names: [joint_1, joint_2]\n"
        "        target_names: [home]\n"
        "        positions: [1.0, 2.0]\n",
        encoding="utf-8",
    )

    joint_names, target_names, positions = read_config_from_file(str(config))

    assert joint_names == ["joint_1", "joint_2"]
    assert target_names == ["home"]
    assert positions == [1.0, 2.0]
