"""
Runner module for ML models
"""
import sys
import os
import cv2

class ModelRunner:
    """
    Class for executing the YOLOV5 model on a specified video path.
    Returns 2 output files on player and ball detections
    """
    def __init__(self, video_path) -> None:
        self.video_path = video_path
        # TODO model configs
        self.frame_reduction_factor = 2


    def drop_frames(self, input_path) -> None:
        """
        Alters the input video fps to 1 / reduction_factor. Irreversible operation.
        """
        dummy_path = 'tmp/temp.mp4'
        video = cv2.VideoCapture(input_path)
        nframes = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
        output_video = cv2.VideoWriter(dummy_path, cv2.VideoWriter_fourcc(*'mp4v'),
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
        os.remove(input_path)
        os.rename(dummy_path, input_path)


    def run(self):
        """
        Executes StrongSORT models and its related video pre- and post- processing.
        """
        # self.drop_frames(self.video_path)

    def get_outputs(self):
        pass
