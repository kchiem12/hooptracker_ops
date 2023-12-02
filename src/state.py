"""
Module containing state of game statistics
"""
from enum import Enum
from pose_estimation.pose_estimate import KeyPointNames, AngleNames
import sys
import math
from collections import deque, defaultdict


def format_results_for_api(self):
    # General statistics
    general_stats = {
        "Number of frames": len(self.frames),
        "Duration": self.calculate_game_duration(),
        "Highest scoring player": self.identify_highest_scoring_player(),
    }

    # Player statistics
    player_stats = {
        player_id: {
            "Points": player_state.points,
            # To be implemented
            "Rebounds": self.calculate_rebounds(player_id),
            "Assists": sum(player_state.passes.values()),
        }
        for player_id, player_state in self.players.items()
    }

    # Team statistics
    team_stats = {
        "Team 1": {
            "Score": self.team1.points,
            # To be implemented
            "Possession": self.calculate_possession_time("Team 1"),
        },
        "Team 2": {
            "Score": self.team2.points,
            # To be implemented
            "Possession": self.calculate_possession_time("Team 2"),
        },
    }

    # Combine all statistics into a single dictionary
    formatted_results = {
        "general_stats": general_stats,
        "player_stats": player_stats,
        "team_stats": team_stats,
    }

    return formatted_results


# maintains dictionary functionality, if desired:
def todict(obj):
    "to dictionary, recursively"
    if isinstance(obj, dict):
        result = {}
        for key, value in obj.items():
            result[key] = todict(value)  # Recursive call for dictionary values
        return result
    elif hasattr(obj, "__dict__"):
        return todict(obj.__dict__)  # Recursive call for objects with __dict__
    elif isinstance(obj, list):
        return [todict(item) for item in obj]  # Recursive call for list items
    else:
        return obj  # Base case: return the original value


# of importance for SORT object type enumerating
class ObjectType(Enum):
    "type of object detected in object tracking"
    BALL = 0
    PLAYER = 1
    RIM = 2


class Box:
    """
    Bounding box containing
        xmin, ymin, xmax, ymax of bounding box
        predicted: indicates if the box was predicted (default False)
    """

    def __init__(
        self, xmin: int, ymin: int, xmax: int, ymax: int, predicted=False
    ) -> None:
        """
        Initializes bounding box
        """
        # IMMUTABLE
        self.xmin: int = xmin
        self.ymin: int = ymin
        self.xmax: int = xmax
        self.ymax: int = ymax
        self.predicted: bool = predicted

    def center(self):
        return ((self.xmin + self.xmax) / 2, (self.ymin + self.ymax) / 2)

    def distance_between_boxes(box1, box2) -> float:
        # Calculate Euclidean distance between the centers of two boxes
        x1, y1 = box1.center()
        x2, y2 = box2.center()
        return (abs(x2 - x1) ** 2 + abs(y2 - y1) ** 2) ** 0.5

    def area(self) -> int:
        "area of bounding box"
        if self.check():
            return (self.xmax - self.xmin) * (self.ymax - self.ymin)
        else:
            return 0

    def point(self, xrel: float, yrel: float) -> tuple:
        "(x,y) point relative to scaling. Requires Well-Defined Box"
        if self.check():
            x = int(xrel * (self.xmax - self.xmin))
            y = int(yrel * (self.ymax - self.ymin))
            return (x, y)
        else:
            raise Exception("box not well-defined")

    def inbounds(self, x: int, y: int) -> bool:
        "if (x,y) within bounding box"
        return x >= self.xmin and x <= self.xmax and y >= self.ymin and y <= self.ymax

    def area_of_intersection(self, box):
        inter: Box = Box(
            xmin=max(box.xmin, self.xmin),
            ymin=max(box.ymin, self.ymin),
            xmax=min(box.xmax, self.xmax),
            ymax=min(box.ymax, self.ymax),
        )
        return inter.area()

    def contains(self, box) -> bool:
        return self.area_of_intersection(box) >= 0.5 * box.area()
        # self.area_of_intersection(box) == min(box.area(), self.area())

    def intersects(self, box) -> bool:
        return self.area_of_intersection(box) != 0

    def check(self) -> bool:
        "verifies if well-defined"
        try:
            assert self.xmin <= self.xmax and self.ymin <= self.ymax
            assert (
                self.xmin is not None
                and self.ymin is not None
                and self.xmax is not None
                and self.ymax is not None
            )
        except:
            return False
        return True


class ShotType(Enum):
    "Status of shot, paired with point value"
    MISS = 0
    TWO = 2
    THREE = 3


class ShotAttempt:
    "Shot Attempt object"

    def __init__(self, playerid: str, start: int, end: int) -> None:
        """
        A single shot attempt containing
            playerid: shot's player
            start: first frame
            end: last frame
            made: whether it was made
            frame: frameno if it was made
            type: MISS, TWO, or THREE
        """
        # IMMUTABLE
        self.playerid: str = playerid
        "player i of shot attempt"
        self.start: int = start
        "first frame"
        self.end: int = end
        "last frame"

        # MUTABLE
        self.made: bool = False
        self.frame: int = None
        "frame shot was made, if applicable"
        self.type: ShotType = ShotType.MISS
        "MISSED, TWO, or THREE"

    def value(self) -> int:
        "point value of shot attempt"
        return self.type.value

    def check(self) -> bool:
        "verifies if well-defined"
        try:
            assert self.start <= self.end
            assert (
                self.start is not None
                and self.end is not None
                and self.type is not None
            )
        except:
            return False
        return True


class BallType(Enum):
    """
    Indicates the status of the ball at any given frame.
    """

    IN_POSSESSION = 1  # hold/dribble
    IN_TRANSITION = 2  # pass/shot
    OUT_OF_PLAY = 3  # out of bounds, just after shot, etc.


class BallFrame:
    """
    Ball state containing
        box: bounding box
        playerid: of last possession
        type: IN_POSSESSION, IN_TRANSITION, or OUT_OF_PLAY
        vx: velocity in the x-direction
        vy: velocity in the y-direction
    """

    def __init__(self, xmin: int, ymin: int, xmax: int, ymax: int) -> None:
        # IMMUTABLE
        self.box: Box = Box(xmin, ymin, xmax, ymax)  # Bounding box

        # MUTABLE
        self.playerid: int = None  # Last player in possession
        self.type: BallType = None  # IN_POSSESSION, IN_TRANSITION, or OUT_OF_PLAY
        self.vx: float = None
        self.vy: float = None

    def check(self) -> bool:
        "Verifies if well-defined"
        try:
            assert self.box.check()
            assert self.playerid is not None and self.type is not None
            # Note: vx and vy are allowed to be None, so no check is needed for them
            return True
        except AssertionError:
            return False


class ActionType(Enum):
    "player actions type"
    NOTHING = 0  # assumption: NOTHING is only action not with ball
    DRIBBLE = 1
    PASS = 2
    SHOOT = 3


class PlayerFrame:
    """
    Player state containing
        box: bounding box
        playerid: of last posession
        type: NOTHING, DRIBBLE, PASS, SHOOT
    """

    def __init__(self, xmin: int, ymin: int, xmax: int, ymax: int) -> None:
        # IMMUTABLE
        self.box: Box = Box(xmin, ymin, xmax, ymax)
        "bounding box"

        # MUTABLE
        self.ballid: int = -1
        "ball in possession (-1) if not in possession"
        self.type: ActionType = None
        "NOTHING, DRIBBLE, PASS, SHOOT"
        self.keypoints: dict[str, Keypoint] = {}
        "keypoints of the player"
        self.angles: dict[str, int] = {}
        "angles of the player in degrees"

    def set_keypoints(self, keypoints: list) -> None:
        "Sets the keypoints for the player"
        try:
            assert len(keypoints) == len(KeyPointNames.list) * 2
        except Exception as e:
            print(len(keypoints))
            print(len(KeyPointNames.list) * 2)
            print("Could not load keypoints, list length error")
            return

        for i in range(len(KeyPointNames.list)):
            x, y = keypoints[2 * i: 2 * i + 2]
            confidence = 1  # can put into confidence later
            key = KeyPointNames.list[i]
            self.keypoints[key] = Keypoint(x, y, confidence)

    def set_angles(self, angles: list) -> None:
        "Sets the angles for the player"
        try:
            assert len(angles) == len(AngleNames.list)
        except Exception as e:
            print("Could not load angles, list length error")
            return

        for i in range(len(angles)):
            angle = angles[i]
            key = AngleNames.list[i]
            self.angles[key] = angle

    def check(self) -> bool:
        "verifies if well-defined"
        try:
            assert self.box.check()
            assert self.type is not None
            if self.type is ActionType.NOTHING:
                assert self.ballid == -1
            else:
                assert self.ballid != -1
            for keypoint in self.keypoints.values():
                assert keypoint.check()
        except AssertionError:
            return False
        return True


class Keypoint:
    """
    Keypoint class containing the coordinates and confidence of a keypoint
    """

    def __init__(self, x: float, y: float, confidence: float) -> None:
        # IMMUTABLE
        self.x: int = math.trunc(x)
        "x-coordinate of the keypoint"
        self.y: int = math.trunc(y)
        "y-coordinate of the keypoint"
        self.confidence: float = round(confidence, 3)
        "confidence score of the keypoint detection"

    def __repr__(self) -> str:
        return f"Keypoint(x={self.x}, y={self.y})"

    def check(self) -> bool:
        "verifies if well-defined"
        try:
            # assert 0 <= self.confidence <= 1
            assert (
                self.x >= 0
                and self.y >= 0
                and self.confidence >= 0
                and self.confidence <= 1
            )
        except AssertionError:
            return False
        return True


class Angle:
    """
    Angle class containing the angle of the player limbs
    """

    def __init__(self, angle: float) -> None:
        self.angle: int = math.trunc(angle)
        "angle of the keypoint"

    def __repr__(self) -> str:
        return f"Angle(angle={self.angle})"

    def check(self) -> bool:
        "verifies if well-defined"
        try:
            assert self.angle >= 0
        except AssertionError:
            return False
        return True


class Frame:
    "Frame class containing frame-by-frame information"

    def __init__(self, frameno: int) -> None:
        """ "
        Instantiates Frame containing fields
            frameno: frame number
            players: dictionary of players info during frame
            balls: dictionary of balls info during frame
            rim: bounding box of rim
            possession: player in possession of ball
        """
        # IMMUTABLE
        self.frameno: int = frameno
        "frame number, Required: non-negative integer"

        # MUTABLE
        # ASSUMPTION: MULITPLE PEOPLE
        self.players: dict[str, PlayerFrame] = {}
        "dictionary of form {player_[id] : PlayerFrame}"
        self.ball: BallFrame = None  # ASSUMPTION: SINGLE BALLS
        "dictionary of form {ball_[id] : BallFrame}"
        self.rim: Box = None  # ASSUMPTION: SINGLE RIM
        "bounding box of rim"
        self.possessions: list[str] = []
        "player in possession of ball, area of intersection"

    def add_player_frame(self, id: int, xmin: int, ymin: int, xmax: int, ymax: int):
        "update players in frame given id and bounding boxes"
        pf = PlayerFrame(xmin, ymin, xmax, ymax)
        id = "player_" + str(id)
        self.players.update({id: pf})

    def set_ball_frame(self, id: int, xmin: int, ymin: int, xmax: int, ymax: int):
        "set ball in frame given id and bounding boxes"
        bf = BallFrame(xmin, ymin, xmax, ymax)
        id = "ball_" + str(id)
        self.ball = bf

    def set_rim_box(self, id: int, xmin: int, ymin: int, xmax: int, ymax: int):
        "set rim box given bounding boxes"
        r = Box(xmin, ymin, xmax, ymax)
        self.rim = r

    def calculate_possesions(self):
        "calculate player in possession of ball, set to possession, None is none"
        bbox: Box = self.ball.box
        max_p: set = set()
        max_a = 1
        for p, pf in enumerate(self.players):
            a = bbox.area_of_intersection(pf.box)
            if a == max_a:
                max_p.add(p)
            elif a > max_a:
                max_a = a
                max_p = set()
                max_p.add(p)
        self.possessions = max_p

    def check(self) -> bool:
        "verifies if well-defined"
        try:
            assert (
                self.frameno is not None
                and self.players is not None
                and self.ball is not None
                and self.rim is not None
            )
            for pf in self.players.values():
                assert pf.check()
            assert self.ball.check()
            assert self.rim.check()
        except:
            return False
        return True


class PlayerState:
    "State object containing player information throughout whole game"

    def __init__(self) -> None:
        """
        Player state containing
            frames: number frames player appeared in
            field_goals_attempted: number of shots a player made
            field_goals: number of made shots by a player
            points: points scored by a player
            field_goal_percentage: percentage of shots made by the player
        """

        # MUTABLE
        self.frames: int = 0
        self.field_goals_attempted: int = 0
        self.field_goals: int = 0
        self.points: int = 0
        self.field_goal_percentage: float = 0.0
        self.passes: dict[int] = {}
        self.assists: int = 0
        self.rebounds: int = 0


class TeamStats:
    "Object of storing team statistics"

    def __init__(self) -> None:
        """ """
        self.players: set = set()
        self.shots_attempted: int = 0
        self.shots_made: int = 0
        self.points: int = 0
        self.field_goal_percentage: float = 0.0

    def compute_field_goal_percentage(self):
        if self.shots_attempted == 0:
            self.field_goal_percentage = 0
        else:
            self.field_goal_percentage = self.shots_made / self.shots_attempted


class BallState:
    "State object containing ball information throughout whole game"

    def __init__(self) -> None:
        """
        Ball state containing ball stuff

        """
        # MUTABLE
        self.frames: int = 0


class Interval:
    "Object of interval when certain player contains a ball"

    def __init__(self, playerid, start, end) -> None:
        """
        Interval obj containing
            playerid: id of player in possession
            start: start frame (inclusive)
            end: end frame (inclusive)
            frames: iterable range over interval
        """
        # IMMUTABLE
        self.playerid: str = playerid
        self.start: int = start
        self.end: int = end
        self.length: int = end - start
        self.frames = range(start, end)  # when want to iterate through frames

    def check(self) -> bool:
        "verifies if well-defined"
        try:
            assert (
                self.playerid is not None
                and self.start is not None
                and self.frames is not None
                and self.frames is not None
            )
            assert self.start <= self.end
        except:
            return False
        return True


class GameState:
    """
    State class holding: player positions, ball position, and team scores
    """

    def __init__(self) -> None:
        """
        Initialises state; contains the following instance variables:
            frames: list of PlayerFrame
            players: dictionary of PlayerState
            ball: BallState
            possessions: list of PossessionInterval
            passes: dictionary of passes
            shots: list of shots by player
            team1: object TeamStats for team1
            team2: object TeamStats for team2
        """
        # MUTABLE

        self.frames: list[Frame] = []
        "list of frames: [Frame], each frame has player, ball, and rim info"

        self.players: dict[str, PlayerState] = {}
        "Global player data: {player_0 : PlayerState, player_1 : PlayerState}"

        self.ball: BallState = BallState()
        "Global ball data"

        self.possessions: list[Interval] = []
        "[PossessionInterval]"

        self.passes: dict[str, dict[int]] = {}
        "dictionary of passes {player_0 : {player_0 : 3}}"

        self.shots: list[Interval] = []
        " list of shots: [(player_[id],start,end)]"

        self.shot_attempts: list[ShotAttempt] = []
        "list of ShotAttempts: [ShotAttempt]"

        self.team1: TeamStats = TeamStats()
        self.team2: TeamStats = TeamStats()

    def populate_team_stats(self):
        """
        Populates the scores and shots made/attempted for each team
        """
        for shot in self.shot_attempts:
            if shot.made:
                if shot.playerid in self.team1.players:
                    self.team1.shots_made += 1
                    self.team1.points += shot.value()
                else:
                    self.team2.shots_made += 1
                    self.team2.points += shot.value()

            if shot.playerid in self.team1.players:
                self.team1.shots_attempted += 1
            else:
                self.team2.shots_attempted += 1

        self.team1.compute_field_goal_percentage()
        self.team2.compute_field_goal_percentage()

    def populate_players_stats(self):
        """
        Iterates through all self.shot_attempts and updates the PlayerState with
        their respective shot attempts (whether made or not) and points scored
        """
        for shot in self.shot_attempts:
            if shot.made:
                self.players[shot.playerid].field_goals += 1
                self.players[shot.playerid].points += shot.value()

            self.players[shot.playerid].field_goals_attempted += 1

            if self.players[shot.playerid].field_goals_attempted == 0:
                self.players[shot.playerid].field_goal_percentage = 0
            else:
                self.players[shot.playerid].field_goal_percentage = (
                    self.players[shot.playerid].field_goals
                    / self.players[shot.playerid].field_goals_attempted
                )

        # populates the player pass dictionary for each Player
        for p in self.passes:
            for c in self.passes[p]:
                self.players[p].passes.update({c: self.passes[p][c]})

    def recompute_frame_count(self):
        """
        Recompute the frame count for each player ID in the video frames.
        This count represents the total number of frames each player ID appears in the video
        and can be used to adjust for noise in reassigned player IDs.
        """
        for ps in self.players.values():  # Reset frame count to 0 for all players
            ps.frames = 0
        for frame in self.frames:
            for pid in frame.players:
                if pid not in self.players:
                    self.players.update({pid: PlayerState()})
                self.players.get(pid).frames += 1

    def filter_players(self, threshold: int):
        "removes all players which appear for less than [threshold] frames"
        self.recompute_frame_count()
        for k in list(self.players.keys()):
            v: PlayerState = self.players.get(k)
            if v.frames < threshold:
                self.players.pop(k, None)
                for frame in self.frames:
                    frame.players.pop(k, None)

    def recompute_pass_from_possession(self):
        "Recompute passes naively from possession list"
        self.passes: dict = {}  # reset pass dictionary
        for p in self.players:
            self.passes.update({p: {}})
            for c in self.players:
                self.passes.get(p).update({c: 0})

        i = 0
        for i in range(len(self.possessions) - 1):
            p1 = self.possessions[i].playerid
            p2 = self.possessions[i + 1].playerid
            self.passes[p1][p2] += 1
