import yaml
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
# returns outputs (original video + statistics) bacck to frontend TODO integrate 
# with a backend endpoint that also uploads results to aws
def load_config(path):
    """
    Loads the config yaml file to read in parameters and settings.
    """
    with open(path, 'r') as file:
        config = yaml.safe_load(file)
    return config


def main(video_path):
    modelrunner = ModelRunner(video_path)
    modelrunner.run()
    people_output, ball_output = modelrunner.fetch_output()
    output_video_path = 'tmp/court_video.mp4'
    processrunner = ProcessRunner(video_path, people_output, ball_output, output_video_path)
    processrunner.run()
    results = processrunner.get_results()
    print(results) # TODO change to be parsed into frontend


if __name__ == '__main__':
    main('data/training_data.mp4')
