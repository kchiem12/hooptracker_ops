"""
Runner module for ML models
"""
import cv2
from ultralytics import YOLO
from pathlib import Path
import multiprocessing as mp
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

        out_array_pr, vid_path = track.run(
            source=self.args["video_file"],
            logger_name="yolov5_person",
            conf_thres=self.args["player_thres"]["conf_thres"],
            iou_thres=self.args["player_thres"]["iou_thres"],
            classes=[self.args["cls"]["player"], self.args["cls"]["rim"]],
            yolo_weights=Path(self.args["player_weights"]),
            save_vid=self.args["save_vid"],
            show_vid=self.args["show_vid"]["player"],
            ret=True,
        )
        print("==============Players and Rim tracked!============")

        self.args["model_videos"]["player"] = vid_path
        people_list = [tuple(round(num) for num in tup) for tup in out_array_pr]
        people_data = [(" ".join(map(str, p[0:7]))) for p in people_list]
        with open(self.args["people_file"], "w") as f:
            f.write("\n".join(people_data))

        print("==============Players and Rim saved to file!============")

    def track_basketball(self):
        """tracks basketball in video and puts data in out_queue"""

        print("==============Start Ball tracking!============")

        out_array_bb, bb_vid_path = track.run(
            source=self.args["video_file"],
            logger_name="yolov5_ball",
            yolo_weights=Path(self.args["ball_weights"]),
            save_vid=self.args["save_vid"],
            show_vid=self.args["show_vid"]["ball"],
            ret=True,
            skip_big=self.args["skip_big"],
        )
        print("==============Basketball tracked!============")

        self.args["model_videos"]["ball"] = bb_vid_path
        ball_list = [tuple(round(num) for num in tup) for tup in out_array_bb]
        ball_data = [(" ".join(map(str, ball[0:7]))) for ball in ball_list]
        with open(self.args["ball_file"], "w") as f:
            f.write("\n".join(ball_data))

        print("==============Basketball saved to file!============")

    def pose(self):
        print("==============Start pose estimation!============")
        model = YOLO(self.args["pose_weights"])
        results = model(
            source=self.args["video_file"],
            conf=self.args["pose_thres"]["conf"],
            stream=False,
            verbose=True,
        )
        print("==============Pose estimated!============")

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
                n,_,_ = xy.shape
                for j in range(n):
                    s = str(frameno)
                    s += " " + str(0)
                    s += " " + str(0)
                    for x in xywh[j, :]:
                        s += " " + str(int(x))
                    s += " " + " ".join(xy[j].astype(int).flatten().astype(str))
                    f.write(s + "\n")

        print("==============Pose saved to file!============")

    def run(self):
        """
        Runs both pose estimation and strongSORT simultaneously
        (2 strongsort passes for players/rim vs ball)
        """
        mp.set_start_method("spawn", force=True)  # fix hanging issue of git actions

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
