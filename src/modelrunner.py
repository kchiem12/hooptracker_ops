"""
Runner module for ML models
"""
import os
import cv2
import pickle
import subprocess
from typing import Tuple
from pose_estimation.pose_estimate import PoseEstimator
from ultralytics import YOLO

class ModelRunner:
    """
    Class for executing the YOLOV5 model on a specified video path.
    Returns 2 output files on player and ball detections
    """
    def __init__(self, video_path, model_vars) -> None:
        self.video_path = video_path
        self.frame_reduction_factor = model_vars['frame_reduction_factor']
        self.pose_estimator = PoseEstimator(video_path=video_path)


    def drop_frames(self, input_path) -> str:
        """
        Alters the input video fps to 1 / reduction_factor. Stores + returns new video in output_path.
        """
        output_path = 'tmp/temp.mp4'
        video = cv2.VideoCapture(input_path)
        nframes = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
        output_video = cv2.VideoWriter(output_path, cv2.VideoWriter_fourcc(*'mp4v'),
                                    int(video.get(cv2.CAP_PROP_FPS)/2), (int(video.get(
            cv2.CAP_PROP_FRAME_WIDTH)), int(video.get(cv2.CAP_PROP_FRAME_HEIGHT))))
        for i in range(nframes):
            ret, frame = video.read()
            if not ret:
                break
            if i % self.frame_reduction_factor == 0:
                output_video.write(frame)

        video.release()
        output_video.release()
        #os.remove(input_path)
        #os.rename(output_path, input_path)
        return output_path


    def run(self):
        """
        Executes StrongSORT models and its related video pre- and post- processing.
        """
        # comment first two lines out to exclude running the model
        # self.drop_frames(self.video_path)
        subprocess.run(['bash', 'src/StrongSORT-YOLO/run_tracker.sh', self.video_path])
        with open('tmp/output.pickle', 'rb') as f:
            self.output_dict = pickle.load(f)

    def pose(self):
        model = YOLO('src/pose_estimation/best.pt')
        results = model(
            source = self.video_path,
            show=False,
            conf=0.3,
            verbose = False
        )
        self.pose_estimator.estimate_pose(results = results)

    def fetch_output(self) -> Tuple[str, str, str]:
        """
        Converts the people and ball model output in self.output.dict into txt files.
        Returns a tuple of the people and ball txt output paths.
        """
        ball_list = [tuple(round(num) for num in tup)
                     for tup in self.output_dict['basketball_data'][0]]
        people_list = [tuple(round(num) for num in tup)
                       for tup in self.output_dict['person_data'][0]]
        ball_data = [(' '.join(map(str, ball[0:7])) + ' -1 -1 -1 -1')
                     for ball in ball_list]
        people_data = [(' '.join(map(str, person[0:7])) + ' -1 -1 -1 -1')
                       for person in people_list]

        with open('tmp/ball.txt', 'w') as f:
            f.write('\n'.join(ball_data))

        with open('tmp/people.txt', 'w') as f:
            f.write('\n'.join(people_data))

        return 'tmp/people.txt', 'tmp/ball.txt', 'tmp/pose.txt'
