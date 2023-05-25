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
        Initialises state; 
        """
        # IMMUTABLE
        self.rim = None
        self.backboard = None
        
        # MUTABLE
        # [{'ball': {xmin, xmax, ymin, ymax}, 'playerid'...}]
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
    
    
    def __repr__(self) -> str:
        string1 = ("'Rim coordinates': " + (str(self.rim) if len(self.rim)>0 else "None") + "\n" +
                "'Backboard coordinates':" + (str(self.backboard) if len(self.rim)>0 else "None") + "\n" +
                "'Court lines coordinates':" + "None" + "\n" +
                "'Number of frames':" + str(len(self.states)) + "\n" +
                "'Number of players':" + str(len(self.players)) + "\n" +
                "'Number of passes': " + str(len(self.passes)) + "\n" +
                "'Team 1': " + str(self.team1) + "\n" +
                "'Team 2': " + str(self.team2) + "\n" +
                "'Team 1 Score': " + str(self.score1) + "\n" +
                "'Team 2 Score': " + str(self.score2) + "\n" +
                "'Team 1 Possession': " + str(self.team1_pos) + "\n" +
                "'Team 2 Possession': " + str(self.team2_pos))
        string2 = ""
        for player in self.players:
            string2 += "'" + player + "': " + str(self.players[player]) + "\n"
        return string1 + "\n" + string2[:-1]
