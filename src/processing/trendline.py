from state import GameState, BallFrame, Box

class LinearTrendline:
    def __init__(self, state: GameState, args):
        self.args = args
        self.state = state
        self.video_path = args["video_file"]
        self.fps = 30  # Assume FPS is 30

    def calculate_velocity(self):
        # Calculate the velocity between each pair of frames
        for i in range(1, len(self.state.frames)):
            frame1 = self.state.frames[i - 1]
            frame2 = self.state.frames[i]

            if frame1.ball and frame2.ball:
                x_center1, y_center1 = frame1.ball.box.center()
                x_center2, y_center2 = frame2.ball.box.center()

                # Time difference in seconds (assuming fps is 30)
                time_diff = 1 / self.fps

                # Velocity components
                vx = (x_center2 - x_center1) / time_diff
                vy = (y_center2 - y_center1) / time_diff

                # Store these velocities in frame2's ball
                frame2.ball.vx = vx
                frame2.ball.vy = vy

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

    def process(self):
        self.calculate_velocity()
        self.estimate_missing_positions()
        return self.state