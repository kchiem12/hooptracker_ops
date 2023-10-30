"""
Main control loop module
"""
import yaml
import sys
from modelrunner import ModelRunner
from processrunner import ProcessRunner

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


def main(video_path: str, results_out: str = "tmp/results.txt") -> None:
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

    modelrunner = ModelRunner(video_path, model_vars)
    modelrunner.run()
    people_output, ball_output, pose_output = modelrunner.fetch_output()
    output_video_path = "tmp/court_video.mp4"
    output_video_path_reenc = "tmp/court_video_reenc.mp4"

    processrunner = ProcessRunner(
        video_path,
        people_output,
        ball_output,
        output_video_path,
        output_video_path_reenc,
    )

    processrunner.run()
    results = processrunner.get_results()
    with open(results_out, "w") as file:
        file.write(results)


if __name__ == "__main__":
    if len(sys.argv) == 2:
        print("got here")
        main(sys.argv[1])
    else:
        print("versus got here")
        main(
            "data/training_data.mp4"
        )  # Pass the first command-line argument to the main function
