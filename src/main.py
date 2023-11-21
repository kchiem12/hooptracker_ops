"""
Main control loop module
"""
from modelrunner import ModelRunner
from processrunner import ProcessRunner
import argparse
from args import DARGS, setup_args


def main(args=DARGS) -> None:
    """
    Sequentially initialises and runs model running and processing tasks.
    Input:
        args: dict of arguments, as specified in config.yaml
    Side Effect:
        Writes to args['results_file']
    """
    print(
        "==============Starting backend loop with following inputs!======================"
    )
    for key, value in args.items():
        print(f"              {key}: {value}")
    print(
        "================================================================================"
    )

    modelrunner = ModelRunner(args=args)
    if not args["skip_model"]:
        modelrunner.run()

    processrunner = ProcessRunner(args=args)
    if not args["skip_process"]:
        processrunner.run()

    results = processrunner.get_results()
    with open(args["results_file"], "w") as f:
        f.write(results)

    print(
        f"==============Backend complete! Results stored in {args['output']}======================"
    )
    if not args["skip_model"]:
        print(f"              player/rim output stored in {args['people_file']}")
        print(f"              ball output stored in {args['ball_file']}")
        print(f"              pose output stored in {args['pose_file']}")
    if not args["skip_process"]:
        print(f"              processed video stored in {args['processed_file']}")
        print(f"              results file stored in {args['results_file']}")
        if not args["skip_court"]:
            print(f"              minimap stored in {args['minimap_file']}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Runs backend loop")
    parser.add_argument("--video_file", help="path to video file")
    parser.add_argument("--output", help="path to output directory")
    parser.add_argument(
        "--skip_model", action="store_true", help="skips model, runs from [output]"
    )
    parser.add_argument("--skip_process", action="store_true", help="skips processing")
    parser.add_argument(
        "--skip_court", action="store_true", help="skips court and minimap processing"
    )
    parser.add_argument(
        "--skip_player_filter", action="store_true", help="skips player filters"
    )
    parser.add_argument(
        "--verbose", action="store_true", help="prints model output to console"
    )
    parser.add_argument("--basename", help="name of output file")
    parser.add_argument(
        "--player_weights", help="path to player/rim weights for yolov5"
    )
    parser.add_argument("--ball_weights", help="path to ball weights for yolov5")
    parser.add_argument("--pose_weights", help="path to pose weights for yolov8-pose")

    args = parser.parse_args()
    args = vars(args)
    dargs0 = DARGS.copy()
    for k in args:
        if args.get(k) is not None:
            dargs0[k] = args[k]
    setup_args(dargs0)
    main(dargs0)
