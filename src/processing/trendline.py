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
        for i in range(1, len(self.state.frames)):
            current_frame = self.state.frames[i]
            previous_frame = self.state.frames[i - 1]

            if not current_frame.ball and previous_frame.ball:
                j = i
                while j < len(self.state.frames) and not self.state.frames[j].ball:
                    if previous_frame.ball.vx is not None and previous_frame.ball.vy is not None:
                        # Calculate predicted position based on velocity
                        x_center_prev, y_center_prev = previous_frame.ball.box.center()
                        x_pred = x_center_prev + (j - i + 1) * previous_frame.ball.vx / self.fps
                        y_pred = y_center_prev + (j - i + 1) * previous_frame.ball.vy / self.fps

                        # Create a new BallFrame with estimated position
                        predicted_box = self.create_predicted_box(x_pred, y_pred)
                        self.state.frames[j].ball = BallFrame(predicted_box.xmin, predicted_box.ymin, predicted_box.xmax, predicted_box.ymax)

                    j += 1

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