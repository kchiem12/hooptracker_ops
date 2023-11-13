import torch
from state import GameState, Frame, PlayerFrame, Keypoint
from pose_estimation.pose_estimate import KeyPointNames, AngleNames

COMBINATIONS = AngleNames.combinations
ANGLE_NAMES = AngleNames.list

class ActionRecognition:
    def __init__(self, state: GameState):
        self.state = state

    @staticmethod
    def is_shot(player_frame: PlayerFrame):
        """
        Takes in keypoint and angle data for a player in a frame and returns whether
        or not the player is shooting. Currently uses a simple threshold heuristic.
        """
        # Assuming keypoints are in the form {name: Keypoint}
        left_wrist = torch.tensor([player_frame.keypoints['left_wrist'].x, player_frame.keypoints['left_wrist'].y])
        right_wrist = torch.tensor([player_frame.keypoints['right_wrist'].x, player_frame.keypoints['right_wrist'].y])
        left_shoulder = torch.tensor([player_frame.keypoints['left_shoulder'].x, player_frame.keypoints['left_shoulder'].y])
        right_shoulder = torch.tensor([player_frame.keypoints['right_shoulder'].x, player_frame.keypoints['right_shoulder'].y])

        left_knee = player_frame.angles('left_knee')
        right_knee = player_frame.angles('right_knee')
        left_elbow = player_frame.angles('left_elbow')
        right_elbow = player_frame.angles('right_elbow')

        THRESHOLD = 0.7 # TODO abstract into config file
        ANGLE_THRESHOLD = 150
        curr = 0
        if left_wrist[1] < left_shoulder[1] and right_wrist[1] < right_shoulder[1]:
            curr += 0.6
        angles = [left_knee, right_knee, left_elbow, right_elbow]
        for i in angles:
            if i > ANGLE_THRESHOLD:
                curr += 0.1
        return curr >= THRESHOLD

    def shot_detect(self):
        for frame in self.state.frames:  # type: Frame
            for player_id, player_frame in frame.players.items():  # type: PlayerFrame
                if self.is_shot(player_frame):
                    shot_interval = (frame.frameno, player_id)
                    self.state.shots.append(shot_interval)
