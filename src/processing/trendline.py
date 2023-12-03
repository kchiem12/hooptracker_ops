from state import GameState, BallFrame, Box
import cv2
import numpy as np

class LinearTrendline:
    def __init__(self, state: GameState, args):
        self.args = args
        self.state = state
        self.video_path = args["video_file"]
        self.fps = 30
        self.velocity_smoothing = 3

    def calculate_velocity(self):
        velocities = []
        for i in range(1, len(self.state.frames)):
            frame1 = self.state.frames[i - 1]
            frame2 = self.state.frames[i]

            if frame1.ball and frame2.ball:
                x_center1, y_center1 = frame1.ball.box.center()
                x_center2, y_center2 = frame2.ball.box.center()

                time_diff = 1 / self.fps
                vx = (x_center2 - x_center1) / time_diff
                vy = (y_center2 - y_center1) / time_diff

                velocities.append((vx, vy))

                if len(velocities) > self.velocity_smoothing:
                    velocities.pop(0)

                avg_vx = sum(v[0] for v in velocities) / len(velocities)
                avg_vy = sum(v[1] for v in velocities) / len(velocities)

                frame2.ball.vx = avg_vx
                frame2.ball.vy = avg_vy

    def estimate_missing_positions(self):
        for i in range(len(self.state.frames)):
            current_frame = self.state.frames[i]

            if not current_frame.ball:
                # Find the nearest previous frame with the ball
                prev_index = None
                next_index = None

                for j in range(i - 1, -1, -1):
                    if self.state.frames[j].ball:
                        prev_index = j
                        break

                # Find the nearest next frame with the ball
                for j in range(i + 1, len(self.state.frames)):
                    if self.state.frames[j].ball:
                        next_index = j
                        break

                # Only interpolate if both previous and next frames with the ball are found
                if prev_index is not None and next_index is not None:
                    prev_ball = self.state.frames[prev_index].ball
                    next_ball = self.state.frames[next_index].ball

                    prev_pos = prev_ball.box.center()
                    next_pos = next_ball.box.center()

                    # Linear interpolation
                    t = (i - prev_index) / (next_index - prev_index)
                    x_pred = prev_pos[0] + (next_pos[0] - prev_pos[0]) * t
                    y_pred = prev_pos[1] + (next_pos[1] - prev_pos[1]) * t

                    # Create a new BallFrame with estimated position
                    predicted_box = self.create_predicted_box(x_pred, y_pred)
                    current_frame.ball = BallFrame(predicted_box.xmin, predicted_box.ymin, predicted_box.xmax, predicted_box.ymax)

    def create_predicted_box(self, x_center, y_center, ball_size=20):
        # Assuming a fixed size for the ball for simplicity
        xmin_pred = x_center - ball_size / 2
        ymin_pred = y_center - ball_size / 2
        xmax_pred = x_center + ball_size / 2
        ymax_pred = y_center + ball_size / 2

        return Box(xmin_pred, ymin_pred, xmax_pred, ymax_pred, predicted=True)

    def calculate_acceleration(self):
        for i in range(2, len(self.state.frames)):
            frame0 = self.state.frames[i - 2]
            frame1 = self.state.frames[i - 1]
            frame2 = self.state.frames[i]

            if frame0.ball and frame1.ball and frame2.ball:
                vx1 = frame1.ball.vx
                vy1 = frame1.ball.vy

                vx2 = frame2.ball.vx
                vy2 = frame2.ball.vy

                time_diff = 1 / self.fps

                ax = (vx2 - vx1) / time_diff
                ay = (vy2 - vy1) / time_diff

                frame2.ball.ax = ax
                frame2.ball.ay = ay

    def detect_abrupt_changes(self, acceleration_threshold=500):
        for i in range(len(self.state.frames)):
            frame = self.state.frames[i]
            if frame.ball and hasattr(frame.ball, 'ax') and hasattr(frame.ball, 'ay'):
                # Dynamic threshold
                dynamic_threshold = acceleration_threshold * (1 + (abs(frame.ball.vx) + abs(frame.ball.vy)) / 100)
                if abs(frame.ball.ax) > dynamic_threshold or abs(frame.ball.ay) > dynamic_threshold:
                    frame.ball = None

    def is_spatial_change_abrupt(self, frame1, frame2, spatial_threshold=30):
        if frame1.ball and frame2.ball:
            x1, y1 = frame1.ball.box.center()
            x2, y2 = frame2.ball.box.center()

            distance = ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5
            return distance > spatial_threshold

    # def track_optical_flow(self):
    #     # Initialize variables for optical flow
    #     prev_frame = None
    #     prev_ball_position = None

    #     # Process each frame
    #     for i, current_frame in enumerate(self.state.frames):
    #         if current_frame.ball:
    #             current_ball_position = np.array([[current_frame.ball.box.center()]], dtype=np.float32)

    #             if prev_frame is not None and prev_ball_position is not None:
    #                 # Calculate optical flow
    #                 new_position, status, error = cv2.calcOpticalFlowPyrLK(prev_frame, current_frame.image, prev_ball_position, None)

    #                 if status[0][0] == 1:  # Check if the flow was found
    #                     current_frame.ball.box.update_center(new_position[0][0])

    #             # Update the previous frame and ball position
    #             prev_frame = current_frame.image.copy()
    #             prev_ball_position = current_ball_position.copy()

    def process(self):
        self.calculate_velocity()
        self.calculate_acceleration()
        for i in range(1, len(self.state.frames)):
            if self.is_spatial_change_abrupt(self.state.frames[i - 1], self.state.frames[i]):
                self.state.frames[i].ball = None
        # self.track_optical_flow()
        self.detect_abrupt_changes()
        self.estimate_missing_positions()
        return self.state
