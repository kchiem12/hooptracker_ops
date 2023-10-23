"""
Module containing state of game statistics
"""
from enum import Enum
import sys


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
    """

    def __init__(self, xmin: int, ymin: int, xmax: int, ymax: int) -> None:
        """
        Initializes bounding box
        """
        # IMMUTABLE
        self.xmin: int = xmin
        self.ymin: int = ymin
        self.xmax: int = xmax
        self.ymax: int = ymax

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
        return self.area_of_intersection(box) == box.area()

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
        playerid: of last posession
        type: IN_POCESSION, IN_TRANSITION, or OUT_OF_PLAY
    """

    def __init__(self, xmin: int, ymin: int, xmax: int, ymax: int) -> None:
        # IMMUTABLE
        self.box: Box = Box(xmin, ymin, xmax, ymax)
        "bounding box"

        # MUTABLE
        self.playerid: int = None
        "last player in possession"
        self.type: BallType = None
        "IN_POCESSION, IN_TRANSITION, or OUT_OF_PLAY"

    def check(self) -> bool:
        "verifies if well-defined"
        try:
            assert self.box.check() is True
            assert self.playerid is not None and self.type is not None
        except:
            return False
        return True


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

    def check(self) -> bool:
        "verifies if well-defined"
        try:
            assert self.box.check() is True
            assert self.type is not None
            if self.type is ActionType.NOTHING:
                assert self.ballid == -1
            else:
                assert self.ballid != -1
        except:
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
        self.players: dict[str, PlayerFrame] = {}  # ASSUMPTION: MULITPLE PEOPLE
        "dictionary of form {player_[id] : PlayerFrame}"
        self.ball: BallFrame = None  # ASSUMPTION: SINGLE BALLS
        "dictionary of form {ball_[id] : BallFrame}"
        self.rim: Box = None  # ASSUMPTION: SINGLE RIM
        "bounding box of rim"
        self.possesions: list[str] = []
        "player in possession of ball"

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
        self.possesions = max_p

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

        """
        # MUTABLE
        self.frames: int = 0


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
            team1: set of players on one team
            team2: est of players on other team
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

        self.team1: set = set()
        self.team2: set = set()

    def recompute_frame_count(self):
        "recompute frame count of all players in frames"
        for ps in self.players.values():  # reset to 0
            ps.frames = 0
        for frame in self.frames:
            for pid in frame.players:
                if pid not in self.players:
                    self.players.update({pid: PlayerState()})
                self.players.get(pid).frames += 1

    def recompute_possession_list(self, threshold=20, join_threshold=20):
        """
        Recompute posssession list with frame possession minimum [threshold].
        Requires at least one frame
        """
        lst = []
        prev = None
        while lst != prev:  # until lists have converged
            prev = lst.copy()
            self.grow_poss(lst)
            self.join_poss(lst, threshold)
            self.filter_poss(lst, join_threshold)
        self.possessions = lst

    def grow_poss(self, lst: list) -> None:
        """
        modifies posssession list [lst] with more possession, if avaiable

        """
        i = 0
        fi = 0
        while fi < len(self.frames):
            f: Frame = self.frames[fi]
            frame = f.frameno
            poss = f.possesions

            if i >= len(lst):
                s = sys.maxsize  # ensures new poss frame added
            else:
                pi: Interval = lst[i]  # assume well-defined
                s = pi.start

            if len(poss) == 0 or s <= frame:  # skip when nothing
                fi += 1  # next frame
                continue
            else:  # frame < start
                p = poss.pop()  # arbitrary player
                lst.insert(i, (p, frame, frame))
                i += 1  # next interval

    def join_poss(self, lst: list, threshold: int = 20):  # possiblility of mapreduce
        "modifies posssession list to join same player intervals within threshold frames"
        i = 0
        while i < len(lst) - 1:
            p1: Interval = lst[i]
            p2: Interval = lst[i + 1]

            if p1.playerid is p2.playerid and p2.start - p1.end <= threshold:
                lst.pop(i)
                lst.pop(i)
                p = Interval(p1.playerid, p1.start, p2.end)
                lst.insert(i, p)
            else:
                i += 1  # next interval pair

    def filter_poss(self, lst: list, threshold: int = 20):
        "modifies posssession list to join same player intervals within threshold frames"
        i = 0
        while i < len(lst):
            p: Interval = lst[i]
            if p.length < threshold or p.playerid not in self.players:
                lst.pop(i)
            else:
                i += 1  # next interval

    def filter_players(self, threshold: int):
        "removes all players which appear for less than [threshold] frames"
        self.recompute_frame_count()
        for k in list(self.players.keys()):
            v: PlayerState = self.players.get(k)
            if v.frames < threshold:
                self.players.pop(k)

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

    ## TODO Update for backend
    def update_scores(self, madeshot_list):
        """
        TODO check for correctness + potentially move out of state.py
        Description:
            Returns a list of made shots with each shot represented as a tuple
            and updates each team's and individual's scores.
        Input:
            madeshot_list [list]: list of made shot tuples
            (frame, 0 if missed, 1 if made)
        Effect:
            Updates self.score1, self.score2.
        """
        madeshots = []
        mdsh_lst = []
        # Set counter to first made shot (where madeshot_list[counter][1] != 0)
        counter = 0
        for shot in madeshot_list:
            if shot[1] != 0:
                mdsh_lst.append(shot)

        # Iterate through possession list and find who made the shot
        # TODO what if madeshot_lst is empty?
        for pos in self.possession_list:
            if pos[2] >= mdsh_lst[counter][0]:
                madeshots.append((pos[0], mdsh_lst[counter][0]))
                counter += 1
                if counter >= len(mdsh_lst):
                    break
        # For each shot made update the player's and team's score
        for shot in madeshots:
            self.players[shot[0]]["shots"] += 1
            self.players[shot[0]]["points"] += 2
            if shot[0] in self.team1:
                self.score1 += 2
            else:
                self.score2 += 2

    # def __repr__(self) -> str:
    #     result_dict = {
    #         "Rim coordinates": str(self.rim) if len(self.rim) > 0 else "None",
    #         "Backboard coordinates": str(self.backboard)
    #         if len(self.rim) > 0
    #         else "None",
    #         "Court lines coordinates": "None",
    #         "Number of frames": str(len(self.frames)),
    #         "Number of players": str(len(self.players)),
    #         "Number of passes": str(len(self.passes)),
    #         "Team 1": str(self.team1),
    #         "Team 2": str(self.team2),
    #         "Team 1 Score": str(self.score1),
    #         "Team 2 Score": str(self.score2),
    #         "Team 1 Possession": str(self.team1_pos),
    #         "Team 2 Possession": str(self.team2_pos),
    #     }
    #     for player in self.players:
    #         result_dict[player] = str(self.players[player])

    #     return str(result_dict)
