import torch
import math
import json
from ultralytics import YOLO


class KeyPointNames:
    list = [
        "nose",
        "left_eye",
        "right_eye",
        "left_ear",
        "right_ear",
        "left_shoulder",
        "right_shoulder",
        "left_elbow",
        "right_elbow",
        "left_wrist",
        "right_wrist",
        "left_hip",
        "right_hip",
        "left_knee",
        "right_knee",
        "left_ankle",
        "right_ankle",
    ]


class AngleNames:
    list = [
        "left_elbow",
        "right_elbow",
        "left_knee",
        "right_knee",
        "right_shoulder",
        "left_shoulder",
        "right_hip",
        "left_hip",
    ]


class PoseEstimator:
    def __init__(
        self,
        model_path="src/pose_estimation/best.pt",
        video_path="res/pose_results/test_multiple_people.mp4",
        combinations=None,
    ):
        # Initialize paths, model, and combinations of keypoints to calculate angles
        self.model_path = model_path
        self.video_path = video_path
        self.model = YOLO(model_path)  # Load the YOLO model

        # Combinations of points to calculate 8 angles
        self.combinations = (
            combinations
            if combinations is not None
            else [
                (5, 7, 9),
                (6, 8, 10),
                (11, 13, 15),
                (12, 14, 16),
                (5, 6, 8),
                (6, 5, 7),
                (11, 12, 14),
                (12, 11, 13),
            ]
        )

        # Names corresponding to the adjusted 8 angle types
        self.angle_names = AngleNames.list

    @staticmethod
    def compute_angle(p1, p2, p3):
        # Calculate angle given 3 points using the dot product and arc cosine
        vector_a = p1 - p2
        vector_b = p3 - p2

        # Normalize the vectors (to make them unit vectors)
        vector_a = vector_a / torch.norm(vector_a)
        vector_b = vector_b / torch.norm(vector_b)

        # Compute the angle
        cosine_angle = torch.sum(vector_a * vector_b)
        angle_radians = torch.acos(cosine_angle)
        angle_degrees = angle_radians * 180 / math.pi

        return angle_degrees

    def estimate_pose(self, results):
        model = YOLO(self.model_path)

        # Initialize an empty list to store pose data
        pose_data = []

        # empty list for shots
        shots = []

        for frame_idx, result in enumerate(results):
            keypoints = result.keypoints.data[
                :, :, :2
            ].numpy()  # Extracting the (x, y) coordinates
            confidences = (
                result.keypoints.conf.numpy().tolist()
            )  # Extracting the confidences
            boxes = result.boxes.xyxy.numpy().tolist()  # Extracting bounding boxes
            frame_pose_data = {
                "frame": frame_idx + 1, # ASSUME NO FRAMES DROPPED TODO keep track with openCV
                "persons": [],
                "boxes": boxes,
                "keypoints": keypoints.tolist(),
                "confidences": confidences,
            }

            for person_idx, (person_keypoints, person_confidences, box) in enumerate(
                zip(keypoints, confidences, boxes)
            ):
                person_data = {
                    "keypoints": person_keypoints.tolist(),
                    "confidences": person_confidences,
                    "box": box,
                    "angles": {},
                }

                # Calculate and display angles based on keypoint combinations
                for idx, combination in enumerate(self.combinations):
                    if all(idx < len(person_keypoints) for idx in combination):
                        p1, p2, p3 = (person_keypoints[i] for i in combination)
                        angle_degrees = self.compute_angle(
                            torch.tensor(p1), torch.tensor(p2), torch.tensor(p3)
                        )
                        person_data["angles"][
                            self.angle_names[idx]
                        ] = angle_degrees.item()

                frame_pose_data["persons"].append(person_data)

                # naive check shot: if wrists above shoulders
                left_wrist_y = person_keypoints[9][1]
                right_wrist_y = person_keypoints[10][1]
                left_shoulder_y = person_keypoints[5][1]
                right_shoulder_y = person_keypoints[6][1]

                if left_wrist_y < left_shoulder_y and right_wrist_y < right_shoulder_y:
                    shots.append(
                        "SHOT TAKEN: person "
                        + str(person_idx)
                        + ", frame "
                        + str(frame_idx)
                    )
                # end naive check shot

            pose_data.append(frame_pose_data)

        with open("tmp/pose_data.json", "w") as f:
            json.dump(pose_data, f)

        # write to shots file
        with open("tmp/shots.txt", "w") as f:
            for line in shots:
                f.write(line)
                f.write("\n")
