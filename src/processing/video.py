import cv2
from state import GameState, Keypoint, ShotAttempt, Interval
import random


class VideoCreator:
    """Class for creating processed video"""

    # Define constants for team colors, ball color, rim color, and highlight color
    TEAM1_COLOR = (0, 255, 0)
    TEAM2_COLOR = (255, 0, 0)
    BALL_COLOR = (0, 0, 255)
    RIM_COLOR = (0, 255, 255)
    POSSESSION_COLOR = (100, 100, 0)
    SHOOTING_COLOR = (255, 255, 0)
    LINE_WIDTH = 2
    LABEL_SIZE = 2
    CIRCLE_RADIUS = 3

    def __init__(
        self, game_state: GameState, video_path: str, output_path: str
    ) -> None:
        # Initialize with game state, input video path, and output video path
        self.state = game_state
        self.video_path = video_path
        self.output_path = output_path
        self.shot_attempt_active = False
        self.player_colors = {}

    # Function to draw bounding boxes on the frame
    def draw_boxes(self, frame, boxes, color, label=""):
        for box in boxes:
            # Draw rectangle around each box with the specified color
            cv2.rectangle(
                frame,
                (box.xmin, box.ymin),
                (box.xmax, box.ymax),
                color,
                self.LINE_WIDTH,
            )
            # If a label is provided, put the label on the frame above the box
            if label:
                cv2.putText(
                    frame,
                    label,
                    (box.xmin, box.ymin - 10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.9,
                    color,
                    self.LABEL_SIZE,
                )

    # Function to draw keypoints on the frame
    def draw_keypoints(self, frame, keypoints, color):
        for k in keypoints:
            kp: Keypoint = keypoints.get(k)
            x, y = kp.x, kp.y
            cv2.circle(frame, (int(x), int(y)), self.CIRCLE_RADIUS, color, -1)

    def vary_color(self, color, delta: int):
        "Generates random color within delta var"

        def rand():
            return random.randint(-delta, delta)

        def bound(x):
            return min(max(0, x), 255)

        return tuple([bound(x + rand()) for x in color])

    # Determine the color of a player's box based on their team
    def get_player_color(self, player_id, shot: ShotAttempt, poss: Interval):
        if shot and player_id == shot.playerid:
            return self.SHOOTING_COLOR
        if poss and player_id == poss.playerid:
            return self.POSSESSION_COLOR

        if not player_id in self.player_colors:
            c = (255, 255, 255)
            if player_id in self.state.team1.players:
                c = self.vary_color(self.TEAM1_COLOR, 50)
            elif player_id in self.state.team2.players:
                c = self.vary_color(self.TEAM2_COLOR, 50)
            self.player_colors.update({player_id: c})
            return c
        else:
            return self.player_colors[player_id]

    def get_player_label(self, player_id: str, shot: ShotAttempt, poss: Interval):
        "Determine the label for a player based on possession and shot attempts"
        label = player_id  # Default label is the player's ID
        append = ""
        if shot and shot.playerid == player_id:
            append += " Shoot"
        if poss and poss.playerid == player_id:
            append += " Poss"
        return label + append  # Return the label after checks

    def run(self):
        # Capture video from the video path
        cap = cv2.VideoCapture(self.video_path)
        if not cap.isOpened():
            print("Error: Could not open video.")
            return

        # Get video properties
        fps = cap.get(cv2.CAP_PROP_FPS)
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")

        # Read the first frame to establish video size
        ret, frame = cap.read()
        if not ret:
            print("Error: Couldn't read the first frame.")
            return

        # Set up the output video writer with the same size as the input video
        height, width, _ = frame.shape
        out = cv2.VideoWriter(self.output_path, fourcc, fps, (width, height))

        # Read frames from GameState
        frames = self.state.frames
        idx = 0  # for frames list

        shots = self.state.shot_attempts
        shot_idx = 0  # for shot list

        posses = self.state.possessions
        poss_idx = 0  # for possession list
        while cap.isOpened():
            if not ret:
                break
            f = int(cap.get(cv2.CAP_PROP_POS_FRAMES))  # cv2 frame
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            if f % 100 == 0:
                print(f"Processed video render frame {f}/{total_frames}.")

            # catch up state frame
            while idx < len(frames) and frames[idx].frameno < f:
                idx += 1
            game_frame = (
                frames[idx] if idx < len(frames) and frames[idx].frameno == f else None
            )

            # catch up shot_attempt
            while shot_idx < len(shots) and shots[shot_idx].end < f:
                shot_idx += 1
            shot = (
                shots[shot_idx]
                if shot_idx < len(shots) and shots[shot_idx].start <= f
                else None
            )

            # catch up possession interval
            while poss_idx < len(posses) and posses[poss_idx].end < f:
                poss_idx += 1
            poss = (
                posses[poss_idx]
                if poss_idx < len(posses) and posses[poss_idx].start <= f
                else None
            )

            # Get the game frame data for the current frame count

            if game_frame:
                # Draw boxes and labels for players
                for player_id, player_frame in game_frame.players.items():
                    player_label = self.get_player_label(
                        player_id, shot, poss
                    )  # Determine label
                    player_color = self.get_player_color(
                        player_id, shot, poss
                    )  # Determine color
                    self.draw_boxes(
                        frame, [player_frame.box], player_color, label=player_label
                    )
                    self.draw_keypoints(frame, player_frame.keypoints, player_color)

                # Draw box for the ball with or without label depending on shot attempt
                if game_frame.ball:
                    ball_label = "Ball"
                    self.draw_boxes(
                        frame, [game_frame.ball.box], self.BALL_COLOR, label=ball_label
                    )

                # Draw box for the rim with label
                if game_frame.rim:
                    self.draw_boxes(
                        frame, [game_frame.rim], self.RIM_COLOR, label="Rim"
                    )

            # Display the current frame count on the frame
            cv2.putText(
                frame,
                f"Frame: {f}",
                (width - 150, height - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (255, 255, 255),
                2,
            )

            # Write the processed frame to the output video
            out.write(frame)

            # Read the next frame from the video
            ret, frame = cap.read()

        # Release resources
        cap.release()
        out.release()
        cv2.destroyAllWindows()

        # Print completion message
        print(f"Video processing complete. Output saved to: {self.output_path}")
