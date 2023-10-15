import cv2
import time
import imageio
import torch
import math
import json
from ultralytics import YOLO  # Ensure ultralytics is installed and configured

class PoseEstimator:
    def __init__(self, model_path='yolov8m-pose.pt', video_path='test_video.mp4', combinations=None):
        # Initialize paths, model, and combinations of keypoints to calculate angles
        self.model_path = model_path
        self.video_path = video_path
        self.model = YOLO(model_path)  # Load the YOLO model

        # Adjusted combinations of points to calculate 8 angles
        self.combinations = combinations if combinations is not None else [
            (5, 7, 9), (6, 8, 10), (11, 13, 15), (12, 14, 16),
            (5, 6, 8), (6, 5, 7), (11, 12, 14), (12, 11, 13)
        ]

        # Names corresponding to the adjusted 8 angle types for better understanding
        self.angle_names = [
            "left_arm", "right_arm", "left_leg", "right_leg",
            "shoulder_left_right_elbow", "shoulder_right_left_elbow",
            "hip_left_right_knee", "hip_right_left_knee"
        ]

    @staticmethod
    def compute_angle(p1, p2, p3):
        # Calculate angle given 3 points using the dot product and arc cosine
        vector_a = p1 - p2
        vector_b = p3 - p2

        # Normalize the vectors (to make them unit vectors)
        vector_a = vector_a / torch.norm(vector_a)
        vector_b = vector_b / torch.norm(vector_b)

        # Compute the angle
        cosine_angle = torch.dot(vector_a, vector_b)
        angle_radians = torch.acos(cosine_angle)
        angle_degrees = angle_radians * 180 / math.pi

        return angle_degrees

    def estimate_pose(self):
        # Start video capture
        cap = cv2.VideoCapture(self.video_path)

        # Initialize video writer
        writer = imageio.get_writer("tmp/test_result.mp4", mode="I")

        # Initialize an empty list to store pose data
        pose_data = []

        # Names corresponding to angle types for better understanding
        angle_names = [
            "left_arm", "right_arm", "left_leg", "right_leg",
            "shoulder_left_right_elbow", "shoulder_right_left_elbow",
            "hip_left_right_knee", "hip_right_left_knee",
            "shoulder_left_hip_right_hip", "shoulder_right_hip_left_hip"
        ]

        while cap.isOpened():
            # Read frame-by-frame
            success, frame = cap.read()
            if success:
                # Measure start time (to calculate FPS later)
                start_time = time.time()

                # Run pose estimation model on the frame
                results = self.model(frame, verbose=False)

                # Extract the keypoints
                keypoints = results[0].keypoints.xy

                # Create annotated frame visualization
                annotated_frame = results[0].plot()

                # Store frame number in data
                frame_pose_data = {'frame': cap.get(cv2.CAP_PROP_POS_FRAMES)}

                # Calculate and display angles based on keypoint combinations
                for idx, combination in enumerate(self.combinations):
                    p1, p2, p3 = keypoints[0][combination[0]], keypoints[0][combination[1]], keypoints[0][combination[2]]
                    angle_degrees = self.compute_angle(p1, p2, p3)

                    # Add angle data to frame_pose_data
                    frame_pose_data[angle_names[idx]] = angle_degrees.item()

                    # Display angle on the annotated frame
                    cv2.putText(annotated_frame, f"{angle_degrees:.2f}°",
                                (int(p2[0]), int(p2[1])), cv2.FONT_HERSHEY_COMPLEX,
                                0.5, (255, 255, 0), 1, cv2.LINE_AA)

                # Append frame's pose data to the list
                pose_data.append(frame_pose_data)

                # Calculate and display FPS
                end_time = time.time()
                fps = 1 / (end_time - start_time)
                cv2.putText(annotated_frame, f"FPS: {int(fps)}", (10, 50),
                            cv2.FONT_HERSHEY_COMPLEX, 1.2, (255, 0, 255), 1, cv2.LINE_AA)

                # Write annotated frame to output video
                annotated_frame = cv2.cvtColor(annotated_frame, cv2.COLOR_BGR2RGB)
                writer.append_data(annotated_frame)

                # Break loop on 'q' key press
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
            else:
                break

        # Cleanup and save data
        writer.close()
        cap.release()
        cv2.destroyAllWindows()

        with open("tmp/pose_data.json", "w") as f:
            json.dump(pose_data, f)