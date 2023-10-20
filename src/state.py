"""
Module containing state of game statistics
"""
from enum import Enum

class ShotType(Enum):
        "Status of shot, paired with point value"
        MISS = 0
        TWO = 2
        THREE = 3

class ShotAttempt:
    """
    A single shot attempt containing
        start: first frame
        end: last frame
        playerid: shot's player
        type: MISSED, TWO, or THREE
    """
    def __init__(self, start:int, end:int) -> None:
        """
        Initializes shot attempt containing
        
        """
        #IMMUTABLE
        self.start : int = start
        "first frame"
        self.end : int = end
        "last frame"

        #MUTABLE
        self.playerid : int = None
        "shot's player"
        self.type : ShotType = None
        "MISSED, TWO, or THREE"
    
    def check(self) -> bool:
        "verifies if well-defined"
        try:
            assert (self.start <= self.end)
            assert (self.start is not None and self.end is not None
                    and self.playerid is not None and self.type is not None)
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

class BallState:
    """
    Ball state containing
        xmin, ymin, xmax, ymax of bounding box
        playerid: of last posession
        type: IN_POCESSION, IN_TRANSITION, or OUT_OF_PLAY
    """
    def __init__(self, xmin:int, ymin:int, xmax:int, ymax:int) -> None:
        """
        Initializes shot attempt containing
        """
        #IMMUTABLE
        self.xmin:int = xmin
        self.ymin:int = ymin
        self.xmax:int = xmax
        self.ymax:int = ymax

        #MUTABLE
        self.playerid : int = None
        "last player in possession"
        self.type : BallType = None
        "IN_POCESSION, IN_TRANSITION, or OUT_OF_PLAY"
    
    def check(self) -> bool:
        "verifies if well-defined"
        try:
            assert (self.xmin <= self.xmax and self.ymin <= self.ymax)
            assert (self.xmin is not None and
                    self.ymin is not None and
                    self.xmax is not None and
                    self.ymax is not None and
                    self.playerid is not None and
                    self.type is not None)
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
        rim: rim position
        backboard: backboard position TODO
        states: list of dictionaries with info at each frame
        possession_list: list of ball possession tuples
        passes: dictionary of passes with their start and end frames and players involved
        possession: dictionary of players with their possessions as list of frame tuples
        team1, team2: list of players on each team
        score1, score2: score of each team
        team1_pos, team2_pos: percentage of possession for each team
        """
        # IMMUTABLE
        self.rim = None
        self.backboard = None

        # MUTABLE
        # [{'frameno': #, 'players': {'player[id]' : xmin, ymin, xmax, ymax}, 'balls': {'ball[id]' : BallState }}]
        self.states = None


        self.possession_list = None
        # {'playerid': {'shots': 0, "points": 0, "rebounds": 0, "assists": 0}}
        self.players = {}
        # [(start_frame, end_frame, BallState)]
        self.ball_state = None
        # {'pass_id': {'frames': (start_frame, end_frame)}, 'players':(p1_id, p2_id)}}
        self.passes = None
        # {'player_id': [(start_frame, end_frame), ...]}
        self.possession = None
        self.team1 = None
        self.team2 = None

        # statistics
        self.score1 = 0
        self.score2 = 0
        self.team1_pos = 0
        self.team2_pos = 0


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
        madeshot_lst = []
        # Set counter to first made shot (where madeshot_list[counter][1] != 0)
        counter = 0
        for shot in madeshot_list:
            if shot[1] != 0:
                madeshot_lst.append(shot)

        # Iterate through possession list and find who made the shot
        # TODO what if madeshot_lst is empty?
        for pos in self.possession_list:
            if pos[2] >= madeshot_lst[counter][0]:
                madeshots.append((pos[0], madeshot_lst[counter][0]))
                counter += 1
                if counter >= len(madeshot_lst):
                    break
        # For each shot made update the player's and team's score
        for shot in madeshots:
            self.players[shot[0]]['shots'] += 1
            self.players[shot[0]]['points'] += 2
            if shot[0] in self.team1:
                self.score1 += 2
            else:
                self.score2 += 2


    def __repr__(self) -> str:
        result_dict = {
        "Rim coordinates": str(self.rim) if len(self.rim) > 0 else "None",
        "Backboard coordinates": str(self.backboard) if len(self.rim) > 0 else "None",
        "Court lines coordinates": "None",
        "Number of frames": str(len(self.states)),
        "Number of players": str(len(self.players)),
        "Number of passes": str(len(self.passes)),
        "Team 1": str(self.team1),
        "Team 2": str(self.team2),
        "Team 1 Score": str(self.score1),
        "Team 2 Score": str(self.score2),
        "Team 1 Possession": str(self.team1_pos),
        "Team 2 Possession": str(self.team2_pos)
        }
        for player in self.players:
            result_dict[player] = str(self.players[player])

        return str(result_dict)
