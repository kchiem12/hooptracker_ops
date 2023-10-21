from typing import Tuple, List, Dict
from state import *


def player_passes(pos_lst) -> List[Tuple[int, int, int, int, int]]:
    """
    Input:
        pos_lst [list]: list of ball possession tuples
    Output:
        passes [list[tuple]]: Returns a list of passes with each pass
                            represented as a tuple of the form
                            (pass_id, passerid, receiverid,
                            start_frame, end_frame)
    """
    passes = []
    curr_player = pos_lst[0][0]
    curr_end_frame = pos_lst[0][2]
    for i in range(1, len(pos_lst)):
        curr_pass = (
            i,
            curr_player,
            pos_lst[i][0],
            curr_end_frame + 1,
            pos_lst[i][1] - 1,
        )
        passes.append(curr_pass)
        curr_player = pos_lst[i][0]
        curr_end_frame = pos_lst[i][2]
    return passes


def ball_state_update(pos_lst: list, lastframe) -> List[Tuple[int, int, BallType]]:
    """
    Reads in a possession list and the last frame of the game
    Returns: List[frame1, frame2, BallState] that partitions each interval of
    frames by ballstate
    """
    # [(start_frame, end_frame, BallState)]
    ball_state = []
    if pos_lst[0][1] != 0:
        ball_state.append((0, pos_lst[0][1] - 1, BallType.OUT_OF_PLAY))
    ball_state.append((pos_lst[0][1], pos_lst[0][2], BallType.IN_POSSESSION))
    curr_frame = pos_lst[0][2] + 1
    for i in range(1, len(pos_lst)):
        ball_state.append((curr_frame, pos_lst[i][1] - 1, BallType.IN_TRANSITION))
        ball_state.append((pos_lst[i][1], pos_lst[i][2], BallType.IN_POSSESSION))
        curr_frame = pos_lst[i][2] + 1
    ball_state.append((curr_frame, lastframe, BallType.OUT_OF_PLAY))
    return ball_state


def player_possession(pos_lst) -> Dict[int, List[Tuple[int, int]]]:
    """
    Input:
        pos_lst [list]: list of ball possession tuples
    Output:
        player_pos {dict}: Returns a dictionary with the player id as the
                            key and a list of tuples of the form
                            (start_frame, end_frame) as the value
    """
    player_pos = {}
    for pos in pos_lst:
        if pos[0] not in player_pos:
            player_pos[pos[0]] = [(pos[1], pos[2])]
        else:
            player_pos[pos[0]].append((pos[1], pos[2]))
    return player_pos
