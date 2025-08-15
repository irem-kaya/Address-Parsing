import subprocess
import sys
import yaml


def sh(cmd: list[str]):
    print("[run]", " ".join(cmd))
    subprocess.run(cmd, check=True)


def main(cfg_path="configs/pipeline.yaml"):
    cfg = yaml.safe_load(open(cfg_path, "r", encoding="utf-8")) or {}

    # normalize left
    sh(
        [
            sys.executable,
            "-m",
            "addresskit.normalize",
            "--input",
            cfg["normalize"]["left_in"],
            "--output",
            cfg["normalize"]["left_out"],
            "--config",
            cfg["normalize"]["config"],
        ]
    )

    # normalize right
    sh(
        [
            sys.executable,
            "-m",
            "addresskit.normalize",
            "--input",
            cfg["normalize"]["right_in"],
            "--output",
            cfg["normalize"]["right_out"],
            "--config",
            cfg["normalize"]["config"],
        ]
    )

    # match
    sh(
        [
            sys.executable,
            "-m",
            "addresskit.match",
            "--left",
            cfg["match"]["left"],
            "--right",
            cfg["match"]["right"],
            "--out",
            cfg["match"]["out"],
            "--config",
            cfg["match"]["config"],
        ]
    )

    # preview (QC)
    sh(
        [
            sys.executable,
            "scripts/make_match_preview.py",
            "--left",
            cfg["normalize"]["left_out"],
            "--right",
            cfg["normalize"]["right_out"],
            "--match",
            cfg["match"]["out"],
            "--out",
            cfg["preview"]["out"],
        ]
    )


if __name__ == "__main__":
    main()
