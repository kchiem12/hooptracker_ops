from state import GameState, PlayerFrame, BallFrame, Box
from args import DARGS

class ActionRecognition:
    def __init__(self, state: GameState, args=DARGS) -> None:
        self.state = state
        self.THRESHOLD = args["shot_threshold"]
        self.ANGLE_THRESHOLD = args["angle_threshold"]

    def pose_shot(self, player_frame: PlayerFrame, ANGLE_THRESHOLD):
        """
        Takes in keypoint and angle data for a player in a frame and returns the
        weighted sum of the pose features. Currently uses a simple threshold
        heuristic.
        """
        keypoints = ["left_wrist", "right_wrist", "left_shoulder", "right_shoulder"]
        for keypoint in keypoints:
            if not keypoint in player_frame.keypoints:
                return False
        # Assuming keypoints are in the form {name: Keypoint}
        left_wrist_y = player_frame.keypoints["left_wrist"].y
        right_wrist_y = player_frame.keypoints["right_wrist"].y
        left_shoulder_y = player_frame.keypoints["left_shoulder"].y
        right_shoulder_y = player_frame.keypoints["right_shoulder"].y

        left_knee = player_frame.angles["left_knee"]
        right_knee = player_frame.angles["right_knee"]
        left_elbow = player_frame.angles["left_elbow"]
        right_elbow = player_frame.angles["right_elbow"]

        curr = 0
        if left_wrist_y < left_shoulder_y and right_wrist_y < right_shoulder_y:
            curr += 0.3
        angles = [left_knee, right_knee, left_elbow, right_elbow]
        for i in angles:
            if i > ANGLE_THRESHOLD:
                curr += 0.075
        return curr


    def ball_shot(self, ball_frame: BallFrame, rim: Box):
        """
        Takes in ball data at a frame and returns the weighted sum of the ball
        features. Currently uses a simple threshold heuristic.
        """
        # checks whether ball y coord is above rim y coord
        if ball_frame is None:
            return 0
        ball_pos = ball_frame.box
        mid_box = ball_pos.center()
        mid_rim = rim.center()
        y_weight = 0.3 if mid_box[1] < mid_rim[1] else 0

        # TODO may implement later if velocity is added
        # checks whether displacement between rim and ball decreases
        # displacement = tuple(map(lambda x, y: x - y, mid_rim, mid_box))
        # v_ball = (ball_frame.vx, -1 * ball_frame.vy)
        # inner_prod = sum(map(lambda x, y: x * y, displacement, v_ball))
        # displacement_weight = 0.1 if inner_prod > 0 else 0

        # return y_weight + displacement_weight
        return y_weight + 0.1


    def shot_detect(self):
        """
        Iterates through each frame and computes the classification of shots for each player.
        if the weighted sum is above the threshold, then the player is classified as shooting.
        """
        # shots_file = open("tmp/shots.txt", "w")

        for frame in self.state.frames:  # type: Frame
            ball_frame = frame.ball
            ball_shot = self.ball_shot(ball_frame, frame.rim)

            for player_id, player_frame in frame.players.items():  # type: PlayerFrame
                pose_shot = self.pose_shot(player_frame, self.ANGLE_THRESHOLD)
                if ball_shot + pose_shot >= self.THRESHOLD:
                    # shots_file.write(str(frame.frameno))
                    # shots_file.write(str(player_id))
                    # shots_file.write("\n")
                    for interval in self.state.possessions:
                        if (interval.start <= frame.frameno <= interval.end and 
                            interval not in self.state.shots):
                            self.state.shots.append(interval)
                    #shot_interval = (frame.frameno, player_id)
                    #self.state.shots.append(shot_interval)

        # shots_file.close()
