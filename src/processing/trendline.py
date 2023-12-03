from state import GameState, BallFrame, Box


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
                time_diff = 1
                vx = (x_center2 - x_center1) / time_diff
                vy = (y_center2 - y_center1) / time_diff

                velocities.append((vx, vy))

                if len(velocities) > self.velocity_smoothing:
                    velocities.pop(0)

                avg_vx = sum(v[0] for v in velocities) / len(velocities)
                avg_vy = sum(v[1] for v in velocities) / len(velocities)
                # print(f"Frame {i}: Velocity - vx: {avg_vx:.2f}, vy: {avg_vy:.2f}")

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
                    current_frame.ball = BallFrame(
                        predicted_box.xmin,
                        predicted_box.ymin,
                        predicted_box.xmax,
                        predicted_box.ymax,
                    )

    def create_predicted_box(self, x_center, y_center, ball_size=20):
        # Assuming a fixed size for the ball for simplicity
        xmin_pred = x_center - ball_size / 2
        ymin_pred = y_center - ball_size / 2
        xmax_pred = x_center + ball_size / 2
        ymax_pred = y_center + ball_size / 2

        return Box(xmin_pred, ymin_pred, xmax_pred, ymax_pred, predicted=True)

    # tried using acceleration, didn't work
    # def calculate_acceleration(self):
    #     for i in range(2, len(self.state.frames)):
    #         frame0 = self.state.frames[i - 2]
    #         frame1 = self.state.frames[i - 1]
    #         frame2 = self.state.frames[i]

    #         if frame0.ball and frame1.ball and frame2.ball:
    #             vx1 = frame1.ball.vx
    #             vy1 = frame1.ball.vy

    #             vx2 = frame2.ball.vx
    #             vy2 = frame2.ball.vy

    #             time_diff = 1 / self.fps
    #             time_diff = 1

    #             ax = (vx2 - vx1) / time_diff
    #             ay = (vy2 - vy1) / time_diff
    #             # print(f"Frame {i}: Acceleration - ax: {ax:.2f}, ay: {ay:.2f}")

    #             frame2.ball.ax = ax
    #             frame2.ball.ay = ay

    # def detect_abrupt_changes(self, acceleration_threshold=500):
    #     for i in range(len(self.state.frames)):
    #         frame = self.state.frames[i]
    #         if frame.ball and hasattr(frame.ball, 'ax') and hasattr(frame.ball, 'ay'):
    #             # Dynamic threshold
    #             dynamic_threshold = acceleration_threshold * (1 + (abs(frame.ball.vx) + abs(frame.ball.vy)) / 100)
    #             if abs(frame.ball.ax) > dynamic_threshold or abs(frame.ball.ay) > dynamic_threshold:
    #                 frame.ball = None

    def is_spatial_change_abrupt(
        self, current_frame, spatial_threshold=70, window_size=15
    ):
        if current_frame.ball:
            x2, y2 = current_frame.ball.box.center()

            # Look back up to 30 frames
            for j in range(1, min(window_size + 1, current_frame.frameno)):
                prev_frame = self.state.frames[current_frame.frameno - j]
                if prev_frame.ball:
                    x1, y1 = prev_frame.ball.box.center()

                    distance = ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5
                    if distance > spatial_threshold:
                        # print(f"Frame {current_frame.frameno}: Abrupt spatial change detected. Distance: {distance:.2f}")
                        return True
                    break

        return False

    def process(self):
        self.calculate_velocity()
        for i in range(len(self.state.frames)):
            if self.is_spatial_change_abrupt(self.state.frames[i]):
                self.state.frames[i].ball = None
        self.estimate_missing_positions()
        return self.state
