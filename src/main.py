"""
Main control loop module
"""
import yaml
from modelrunner import ModelRunner
from processrunner import ProcessRunner
import argparse


# before main is called:
# frontend boots up, awaits user to upload a video
# upload button triggers backend call to upload video to s3
# fetch the video from cloud and download to tmp/uploaded_video.mp4
# calls main


# load in configs from config.yaml
# initialise modelrunner and processrunner
# feed video into the yolo model, pass into modelrunner
# get output from modelrunner, feed into statrunner
# returns outputs (original video + statistics) back to frontend TODO integrate
# with a backend endpoint that also uploads results to aws
def load_config(path):
    """
    TODO Loads the config yaml file to read in parameters and settings.
    """
    with open(path, "r") as file:
        config = yaml.safe_load(file)
    return config


def main(source: str, results_out: str, results_folder=None) -> None:
    """
    Sequentially initialises and runs model running and processing tasks.
    Input:
        video_path: relative path to video to process
        results_out: relative path to write results
    Side Effect:
        Writes to results [results_out]
    """
    config = load_config("config.yaml")
    model_vars = config["model_vars"]

    modelrunner = ModelRunner(source, model_vars, out=results_folder)
    if not results_folder:
        modelrunner.run()
    people_output, ball_output, pose_output = modelrunner.fetch_output()
    output_video_path = "tmp/court_video.mp4"
    output_video_path_reenc = "tmp/court_video_reenc.mp4"
    processed_video_path = "tmp/processed_video.mp4"

    processrunner = ProcessRunner(
        source,
        people_output,
        ball_output,
        pose_output,
        output_video_path,
        output_video_path_reenc,
        processed_video_path,
    )

    processrunner.run()
    results = processrunner.get_results()
    with open(results_out, "w") as file:
        file.write(results)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Runs backend loop")
    parser.add_argument("-s", "--source", help="runs backend on specified file ")
    parser.add_argument("-o", "--out", help="specify where to save file")
    parser.add_argument(
        "-p",
        "--process_only",
        help="skips model running and runs from results stored tmp/save. specifiy processed results directory",
    )
    args = parser.parse_args()
    s = "data/training_data.mp4"
    p = None
    o = "tmp/results.txt"

    if args.source:
        if args.process_only:
            p = args.process_only
        s = args.source
    else:
        print("============Running default script for backend...==============")
    if args.out:
        o = args.out
    print(
        f"============Running backend on {s}, results saved to {o}, results folder: {p}...=============="
    )

    main(source=s, results_out=o, results_folder=p)
