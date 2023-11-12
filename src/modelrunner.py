"""
Runner module for ML models
"""
import cv2
from ultralytics import YOLO
from pathlib import Path
import multiprocessing as mp
from pose_estimation import pose_estimate
import time
from args import DARGS

from strongsort.yolov5 import detect as track


class ModelRunner:
    """
    Class for executing the YOLOV5 model on a specified video path.
    Returns 2 output files on player and ball detections
    """

    def __init__(self, args=DARGS) -> None:
        self.args = args

    def drop_frames(self) -> str:
        """
        Alters the input video fps to 1 / reduction_factor. Stores + returns new video in output_path.
        """
        output_path = self.args["video_file"]
        video = cv2.VideoCapture(self.args["video_file"])
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
            if i % self.args["frame_reduction_factor"] == 0:
                output_video.write(frame)

        video.release()
        output_video.release()
        # os.remove(input_path)
        # os.rename(output_path, input_path)
        return output_path

    def track_person(self):
        """tracks persons in video and puts data in out_queue"""

        print("==============Start Players and Rim tracking!============")

        _, vid_path = track.run(
            source=self.args["video_file"],
            logger_name="players",
            conf_thres=self.args["player_thres"]["conf_thres"],
            iou_thres=self.args["player_thres"]["iou_thres"],
            classes=[self.args["cls"]["player"], self.args["cls"]["rim"]],
            yolo_weights=Path(self.args["player_weights"]),
            save_vid=self.args["save_vid"],
            show_vid=self.args["show_vid"]["player"],
            ret=False,
            save_txt=True,
            write_to=self.args["people_file"],
            verbose=self.args["verbose"],
        )
        self.args["model_videos"]["player"] = vid_path
        print("==============Players and Rim tracked!============")

    def track_basketball(self):
        """tracks basketball in video and puts data in out_queue"""

        print("==============Start Ball tracking!============")

        _, bb_vid_path = track.run(
            source=self.args["video_file"],
            logger_name="ball",
            yolo_weights=Path(self.args["ball_weights"]),
            save_vid=self.args["save_vid"],
            show_vid=self.args["show_vid"]["ball"],
            skip_big=self.args["skip_big"],
            ret=False,
            save_txt=True,
            write_to=self.args["ball_file"],
            verbose=self.args["verbose"],
        )
        self.args["model_videos"]["ball"] = bb_vid_path
        print("==============Basketball tracked!============")

    def pose(self):
        print("==============Start pose estimation!============")
        model = YOLO(self.args["pose_weights"])
        results = model(
            source=self.args["video_file"],
            conf=self.args["pose_thres"]["conf"],
            stream=True,  # continuous output to results
            verbose=self.args["verbose"],
        )
        pose_estimate.write_to(self.args["pose_file"], results)
        print("==============Pose estimated!============")

    def run(self):
        """
        Runs both pose estimation and strongSORT simultaneously
        (2 strongsort passes for players/rim vs ball)
        """
        mp.set_start_method("spawn", force=True)  # fix hanging issue of git actions

        p1 = mp.Process(target=self.track_person)
        p2 = mp.Process(target=self.track_basketball)
        p3 = mp.Process(target=self.pose)

        start = time.time()

        p1.start()
        p2.start()
        p3.start()

        p1.join()
        p2.join()
        p3.join()

        end = time.time()
        total_frames = self.get_frame_count(self.args["video_file"])
        minutes = round((end - start) / 60, 2)
        ms_per_frame = round(1000 * (end - start) / total_frames, 4)

        print(
            f"=============Model Time Elapsed: {minutes} minutes, {ms_per_frame}ms per frame================="
        )

    def get_frame_count(self, video_path):
        cap = cv2.VideoCapture(video_path)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        cap.release()
        return frame_count
