import cv2
import time
import imageio
import torch
import math
import json
from ultralytics import YOLO


class PoseEstimator:
    def __init__(self, model_path='yolov8m-pose.pt', video_path='test_video.mp4', combinations=None):
        self.model_path = model_path
        self.video_path = video_path
        self.model = YOLO(model_path)
        self.combinations = combinations if combinations is not None else [
                (5, 7, 9),    # Left arm: shoulder, elbow, wrist
                (6, 8, 10),   # Right arm: shoulder, elbow, wrist
                (11, 13, 15), # Left leg: hip, knee, ankle
                (12, 14, 16), # Right leg: hip, knee, ankle
                (5, 6, 8),    # Shoulder, right shoulder, right elbow (shoulder angle)
                (6, 5, 7),    # Right shoulder, left shoulder, left elbow
                (11, 12, 14), # Hip, right hip, right knee
                (12, 11, 13), # Right hip, left hip, left knee
                (5, 11, 12),  # Left shoulder, left hip, right hip
                (6, 12, 11)   # Right shoulder, right hip, left hip
                ]

    @staticmethod
    def compute_angle(p1, p2, p3):
      vector_a = p1 - p2
      vector_b = p3 - p2

      vector_a = vector_a / torch.norm(vector_a)
      vector_b = vector_b / torch.norm(vector_b)

      cosine_angle = torch.dot(vector_a, vector_b)
      angle_radians = torch.acos(cosine_angle)

      angle_degrees = angle_radians * 180 / math.pi

      return angle_degrees

    def estimate_pose(self):

        cap = cv2.VideoCapture(self.video_path)
        writer = imageio.get_writer("tmp/test_result.mp4", mode="I")

        pose_data = []

        angle_names = [
        "Left arm", "Right arm", "Left leg", "Right leg",
        "Shoulder (L-R-E)", "Right shoulder (R-L-E)", "Hip (L-R-K)",
        "Right hip (R-L-K)", "Left shoulder (L-H-RH)", "Right shoulder (R-H-LH)"
        ]

        while cap.isOpened():
            success, frame = cap.read()
            if success:
                start_time = time.time()
                results = self.model(frame, verbose=False)
                keypoints = results[0].keypoints.xy

                annotated_frame = results[0].plot()

                frame_pose_data = {'frame': cap.get(cv2.CAP_PROP_POS_FRAMES)}

                for idx, combination in enumerate(self.combinations):
                    p1 = keypoints[0][combination[0]]
                    p2 = keypoints[0][combination[1]]
                    p3 = keypoints[0][combination[2]]

                    angle_degrees = self.compute_angle(p1, p2, p3)

                    print(f"{angle_names[idx]} Angle: {angle_degrees.item():.2f}°")

                    frame_pose_data[f'angle_{idx}'] = angle_degrees.item()

                    cv2.putText(annotated_frame, f"{angle_degrees:.2f}°",
                                (int(p2[0]), int(p2[1])), cv2.FONT_HERSHEY_COMPLEX,
                                0.5, (255, 255, 0), 1, cv2.LINE_AA)

                pose_data.append(frame_pose_data)

                end_time = time.time()
                fps = 1 / (end_time - start_time)

                cv2.putText(annotated_frame, f"FPS: {int(fps)}", (10, 50),
                            cv2.FONT_HERSHEY_COMPLEX, 1.2, (255, 0, 255), 1, cv2.LINE_AA)

                annotated_frame = cv2.cvtColor(annotated_frame, cv2.COLOR_BGR2RGB)
                writer.append_data(annotated_frame)

                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
            else:
                break

        writer.close()
        cap.release()
        cv2.destroyAllWindows()

        with open("tmp/pose_data.json", "w") as f:
            json.dump(pose_data, f)
