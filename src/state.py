"""
Module containing state of game statistics
"""
from enum import Enum

class BallState(Enum):
    """
    Indicates the status of the ball at any given frame.
    """
    IN_POSSESSION = 1  # hold/dribble
    IN_TRANSITION = 2  # pass/shot
    OUT_OF_PLAY = 3  # out of bounds, just after shot, etc.


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
        # [{'frameno': #, 'ball': {xmin, xmax, ymin, ymax}, 'playerid'...}]
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
