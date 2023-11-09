"""
Runner module for ML models
"""
import cv2
from ultralytics import YOLO
from pathlib import Path
import multiprocessing as mp
import time
from args import DARGS
import logging

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
            conf_thres=self.args["player_thres"]["conf_thres"],
            iou_thres=self.args["player_thres"]["iou_thres"],
            classes=[self.args["cls"]["player"], self.args["cls"]["rim"]],
            yolo_weights=Path(self.args["player_weights"]),
            save_vid=self.args["save_vid"],
            show_vid=self.args["show_vid"]["player"],
            ret=False,
            save_txt=True,
            write_to=self.args["people_file"],
            verbose=self.args["model_verbose"],
        )
        self.args["model_videos"]["player"] = vid_path
        print("==============Players and Rim tracked!============")

    def track_basketball(self):
        """tracks basketball in video and puts data in out_queue"""

        print("==============Start Ball tracking!============")

        _, bb_vid_path = track.run(
            source=self.args["video_file"],
            yolo_weights=Path(self.args["ball_weights"]),
            save_vid=self.args["save_vid"],
            show_vid=self.args["show_vid"]["ball"],
            skip_big=self.args["skip_big"],
            ret=False,
            save_txt=True,
            write_to=self.args["ball_file"],
            verbose=self.args["model_verbose"],
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
            verbose=self.args["model_verbose"],
        )
        with open(self.args["pose_file"], "w") as f:
            f.write("")
        with open(self.args["pose_file"], "a") as f:
            frameno = 0
            for result in results:
                frameno += 1
                if result.boxes is None:
                    continue
                boxes = result.boxes
                xywh = boxes.xywh.numpy()
                xy = result.keypoints.xy.numpy()
                n, _, _ = xy.shape
                for j in range(n):
                    s = str(frameno)
                    s += " " + str(0)
                    s += " " + str(0)
                    for x in xywh[j, :]:
                        s += " " + str(int(x))
                    s += " " + " ".join(xy[j].astype(int).flatten().astype(str))
                    f.write(s + "\n")
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

        print(f"=============time elapsed: {end-start}=================")
