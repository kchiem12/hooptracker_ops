import os
import yaml


def _set_filepaths(args):
    """
    Set up remaining args; should have all paramters except strings.
    Requires: output and video_file fields
    """
    args["people_file"] = os.path.join(args["output"], args["basename"] + "people.txt")
    args["ball_file"] = os.path.join(args["output"], args["basename"] + "ball.txt")
    args["pose_file"] = os.path.join(args["output"], args["basename"] + "pose.txt")
    args["minimap_file"] = os.path.join(
        args["output"], args["basename"] + "minimap.mp4"
    )
    args["minimap_temp_file"] = os.path.join(
        args["output"], args["basename"] + "minimap_temp.mp4"
    )
    args["processed_file"] = os.path.join(
        args["output"], args["basename"] + "processed.mp4"
    )
    args["results_file"] = os.path.join(
        args["output"], args["basename"] + "results.txt"
    )


def setup_args(args) -> None:
    "set up args, making sure variables exist"
    if all(k in args for k in ["video_file", "output"]):
        _set_filepaths(args)
    else:
        raise ValueError("video_file and output must be specified")


def set_basename(args, basename):
    args["basename"] = basename
    setup_args(args)


def _default_args() -> dict:
    "returns default args. Raises error if config.yaml no yet up correctly"
    with open("config.yaml", "r") as file:
        config = yaml.safe_load(file)
    with open(config["default_config"], "r") as file:
        config = yaml.safe_load(file)
    setup_args(config)
    _set_filepaths(config)
    return config


DARGS = _default_args()
