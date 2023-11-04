import cv2
from state import GameState, Keypoint
import random


class VideoCreator:
    """Class for creating processed video"""

    # Define constants for team colors, ball color, rim color, and highlight color
    TEAM1_COLOR = (0, 255, 0)
    TEAM2_COLOR = (255, 0, 0)
    BALL_COLOR = (0, 0, 255)
    RIM_COLOR = (0, 255, 255)
    HIGHLIGHT_COLOR = (255, 255, 0)
    LINE_WIDTH = 1
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
            cv2.rectangle(frame, (box.xmin, box.ymin), (box.xmax, box.ymax), color, self.LINE_WIDTH)
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
    def get_player_color(self, player_id):
        if player_id not in self.player_colors:
            c = (255, 255, 255)
            if player_id in self.state.team1.players:
                c = self.vary_color(self.TEAM1_COLOR, 50)
            elif player_id in self.state.team2.players:
                c = self.vary_color(self.TEAM2_COLOR, 50)
            self.player_colors.update({player_id: c})
        else:
            return self.player_colors[player_id]

    # Determine the label for a player based on possession and shot attempts
    def get_player_label(self, player_id, frame_count):
        label = player_id  # Default label is the player's ID

        append = ""

        # Assign "In Possession" label if the player is in possession
        for possession in self.state.possessions:
            if (
                possession.start <= frame_count <= possession.end
                and possession.playerid == player_id
            ):
                append += " Possessor"

        # Assign "Shooter" label if the player is attempting a shot
        for shot_attempt in self.state.shot_attempts:
            if (
                shot_attempt.start <= frame_count <= shot_attempt.end
                and shot_attempt.playerid == player_id
            ):
                append += " Shooter"

        return label + append  # Return the label after checks

    # Highlight possessions on the frame
    def highlight_possessions(self, frame, frame_count, game_frame):
        # Only the player in possession gets highlighted
        for possession in self.state.possessions:
            if possession.start <= frame_count <= possession.end:
                player_id = possession.playerid
                if player_id in game_frame.players:
                    player_frame = game_frame.players[player_id]
                    self.draw_boxes(frame, [player_frame.box], self.HIGHLIGHT_COLOR)
                break  # Once the player in possession is found, no need to continue

    # Highlight shot attempts on the frame
    def highlight_shot_attempts(self, frame, current_frame, game_frame):
        self.shot_attempt_active = False  # Reset flag for each frame
        for shot_attempt in self.state.shot_attempts:
            if shot_attempt.start <= current_frame <= shot_attempt.end:
                self.shot_attempt_active = True  # Set flag if a shot attempt is active
                if game_frame and game_frame.ball:
                    self.draw_boxes(frame, [game_frame.ball.box], self.HIGHLIGHT_COLOR)
                player_id = shot_attempt.playerid
                if player_id in game_frame.players:
                    player_frame = game_frame.players[player_id]
                    self.draw_boxes(frame, [player_frame.box], self.HIGHLIGHT_COLOR)

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

        idx = 0
        while cap.isOpened():
            if not ret:
                break
            f = int(cap.get(cv2.CAP_PROP_POS_FRAMES))  # cv2 frame
            while idx < len(frames) and frames[idx].frameno < f:  # get to right frame
                idx += 1
            use_state = idx < len(frames) and frames[idx].frameno == f

            # Get the game frame data for the current frame count
            game_frame = frames[idx] if use_state else None

            if game_frame:
                # Draw boxes and labels for players
                for player_id, player_frame in game_frame.players.items():
                    player_label = self.get_player_label(
                        player_id, f
                    )  # Determine label
                    player_color = self.get_player_color(player_id)  # Determine color
                    self.draw_boxes(
                        frame, [player_frame.box], player_color, label=player_label
                    )
                    self.draw_keypoints(frame, player_frame.keypoints, player_color)

                # Draw box for the ball with or without label depending on shot attempt
                if game_frame.ball:
                    ball_label = "Ball" if not self.shot_attempt_active else ""
                    self.draw_boxes(
                        frame, [game_frame.ball.box], self.BALL_COLOR, label=ball_label
                    )

                # Draw box for the rim with label
                if game_frame.rim:
                    self.draw_boxes(
                        frame, [game_frame.rim], self.RIM_COLOR, label="Rim"
                    )

                # Process each frame to highlight possessions and shot attempts
                self.highlight_possessions(frame, f, game_frame)
                self.highlight_shot_attempts(frame, f, game_frame)

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
