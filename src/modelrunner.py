"""
Runner module for ML models
"""
import cv2
from typing import Tuple
from pose_estimation.pose_estimate import PoseEstimator
from ultralytics import YOLO

from pathlib import Path
import multiprocessing as mp

import time
import sys

FILE = Path(__file__).resolve()
ROOT = FILE.parents[0] / "strongsort"  # yolov5 strongsort root directory
WEIGHTS = ROOT / "weights"
TORCHREID = ROOT / "strong_sort" / "deep" / "reid"
for path in [ROOT, ROOT / "yolov5", TORCHREID]:
    p = str(path)
    if p not in sys.path:
        sys.path.append(p)

from strongsort.yolov5 import detect as track


class ModelRunner:
    """
    Class for executing the YOLOV5 model on a specified video path.
    Returns 2 output files on player and ball detections
    """

    def __init__(self, video_path, model_vars) -> None:
        self.video_path = video_path
        self.frame_reduction_factor = model_vars["frame_reduction_factor"]
        self.pose_estimator = PoseEstimator(video_path=video_path)
        self.people_out = "tmp/people.txt"
        self.ball_out = "tmp/ball.txt"
        self.pose_out = "tmp/pose.txt"

    def drop_frames(self, input_path) -> str:
        """
        Alters the input video fps to 1 / reduction_factor. Stores + returns new video in output_path.
        """
        output_path = "tmp/temp.mp4"
        video = cv2.VideoCapture(input_path)
        nframes = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
        output_video = cv2.VideoWriter(
            output_path,
            cv2.VideoWriter_fourcc(*"mp4v"),
            int(video.get(cv2.CAP_PROP_FPS) / 2),
            (
                int(video.get(cv2.CAP_PROP_FRAME_WIDTH)),
                int(video.get(cv2.CAP_PROP_FRAME_HEIGHT)),
            ),
        )
        for i in range(nframes):
            ret, frame = video.read()
            if not ret:
                break
            if i % self.frame_reduction_factor == 0:
                output_video.write(frame)

        video.release()
        output_video.release()
        # os.remove(input_path)
        # os.rename(output_path, input_path)
        return output_path

    def track_person(self):
        """tracks persons in video and puts data in out_queue"""
        print("==============Start Players and Rim tracking!============")
        out_array_pr, vid_path = track.run(
            source=self.video_path,
            logger_name="yolov5_person",
            classes=[1, 2],
            yolo_weights=WEIGHTS / "best.pt",
            save_vid=False,
            ret=True,
        )
        print("==============Players and Rim tracked!============")

        people_list = [tuple(round(num) for num in tup) for tup in out_array_pr]
        people_data = [
            (" ".join(map(str, p[0:7])) + " -1 -1 -1 -1") for p in people_list
        ]
        with open(self.people_out, "w") as f:
            f.write("\n".join(people_data))
        print("==============Players and Rim saved to file!============")

    def track_basketball(self):
        """tracks basketball in video and puts data in out_queue"""
        print("==============Start Ball tracking!============")
        out_array_bb, bb_vid_path = track.run(
            source=self.video_path,
            logger_name="yolov5_ball",
            yolo_weights=WEIGHTS / "best_basketball.pt",
            save_vid=False,
            ret=True,
            skip_big=True,
        )
        print("==============Basketball tracked!============")
        ball_list = [tuple(round(num) for num in tup) for tup in out_array_bb]
        ball_data = [
            (" ".join(map(str, ball[0:7])) + " -1 -1 -1 -1") for ball in ball_list
        ]
        with open(self.ball_out, "w") as f:
            f.write("\n".join(ball_data))

        print("==============Basketball saved to file!============")

    def pose(self):
        print("==============Start pose estimation!============")
        model = YOLO("src/pose_estimation/best.pt")
        print("model", type(model))
        results = model(
            source=self.video_path, show=False, conf=0.3, verbose=True, stream=False
        )
        print("results", type(results))

        self.pose_estimator.estimate_pose(results=results)
        print("==============Pose estimated!============")

    def run(self):
        """
        Runs both pose estimation and strongSORT simultaneously
        (2 strongsort passes for players/rim vs ball)
        """

        # p1 = mp.Process(target=self.track_person)
        # p2 = mp.Process(target=self.track_basketball)
        p3 = mp.Process(target=self.pose)

        start = time.time()

        # p1.start()
        # p2.start()
        p3.start()

        # p1.join()
        # p2.join()
        p3.join()

        end = time.time()

        print(f"=============time elapsed: {end-start}=================")

    def fetch_output(self) -> Tuple[str, str, str]:
        """
        Returns a tuple of the people and ball txt output paths.
        """
        return self.people_out, self.ball_out, self.pose_out
