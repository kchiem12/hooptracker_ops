from typing import Tuple, List, Dict
from state import BallType, BallState, GameState

def parse_output(state: GameState, output_path: str):
    """
    Parses the player output file into a list of dictionaries.
    File is in the format:
    Each line represents a frame and contains the following information:
        <frame_no> <obj_type> <obj_id> <xmin>, <ymin>, <width>, <height>,
        <irrelevant>
    Object types: 0 - ball, 1 - player, 2 - rim
    Input:
        state [GameState]: GameState object
        output_path [str]: path to output file
    Output:
        rim_info [dict]: dictionary containing rim coordinates
        frames [list]: list of dictionaries containing frame information
    """
    frames = []
    rim_info = {}
    with open(output_path, 'r') as file:
        lines = file.readlines()
        curr_frame = int(lines[0].split()[0])
        rim = True
        frame_info = {"frameno": curr_frame, "players": {}, "balls": {}}
        for line in lines:
            curr = line.split()
            if curr_frame != curr[0]:
                frames.append(frame_info)
                frame_info = {"frameno": int(curr[0]), "players": {}}
                curr_frame = curr[0]
            if curr[1] == '1':
                frame_info['players']['player' + curr[2]] = {
                    'xmin': int(curr[3]),
                    'ymin': int(curr[4]),
                    'xmax': int(curr[3]) + int(curr[5]),
                    'ymax': int(curr[4]) + int(curr[6])
                }
            elif rim and curr[1] == '2':
                rim_info = {
                    'xmin': int(curr[3]),
                    'ymin': int(curr[4]),
                    'xmax': int(curr[3]) + int(curr[5]),
                    'ymax': int(curr[4]) + int(curr[6])
                }
                rim = False
        frames.append(frame_info)
    return rim_info, frames


def parse_ball(state: GameState, ball_out) -> None:
    """
    Reads the ball output and updates state.states.
    Input:
        state [GameState]: GameState object
        ball_out [str]: path to ball output file
    """
    with open(ball_out, 'r') as file:
        lines = file.readlines()
        curr_frame = lines[0].split()[0]
        idx = 0
        for i, frame in enumerate(state.states):
            if frame.get("frameno") == int(curr_frame):
                idx = i
                break
        frame_info = {}
        for line in lines:
            curr = line.split()
            if curr_frame != curr[0]: # if first frame is not at first ball
                state.states[idx].update(frame_info)
                for i in range(idx, len(state.states)):
                    if state.states[i].get("frameno") == int(curr[0]):
                        idx = i
                        break
                frame_info = {}
                curr_frame = curr[0]
            if int(curr[5]) > 200 or int(curr[6]) > 200:
                continue
            frame_info['ball'] = {
                'xmin': int(curr[3]),
                'ymin': int(curr[4]),
                'xmax': int(curr[3]) + int(curr[5]),
                'ymax': int(curr[4]) + int(curr[6])
            }
    return None

def parse_ball2(state: GameState, ball_out) -> None:
    """
    Reads the ball output and updates state.states for "balls".
    Input:
        state [GameState]: GameState object
        ball_out [str]: path to ball output file
    Assume: frame numbers are shared between ball and people
    """
    BALL = 0
    with open(ball_out, 'r') as file:
        lines = [ [int(x) for x in line.split()] 
                 for line in file.readlines()] # lines[idb][0-6]
        b = 0 #index of line in ball
        s = 0 #index of state
        while s < len(state.states) and b < len(lines):
            bframe, obj_type, b_id, xmin, ymin, xwidth, ywidth = lines[b][:7]
            sframe = state.states[s].get("frameno")
            if obj_type != BALL:
                b += 1
            elif bframe < sframe: #catch up
                b += 1
            elif bframe > sframe:
                s += 1
            else: #bframe = sframe, update frame
                bs:BallState = BallState(xmin, ymin, xmax=xmin+xwidth, ymax=ymin+ywidth)
                b_id:str = "ball" + b_id
                state.states[s].get("balls").update({b_id : bs})
                b += 1
    return None


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
        curr_pass = (i, curr_player, pos_lst[i][0], curr_end_frame+1,
                        pos_lst[i][1]-1)
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
        ball_state.append((0, pos_lst[0][1]-1, BallType.OUT_OF_PLAY))
    ball_state.append(
        (pos_lst[0][1], pos_lst[0][2], BallType.IN_POSSESSION))
    curr_frame = pos_lst[0][2]+1
    for i in range(1, len(pos_lst)):
        ball_state.append(
            (curr_frame, pos_lst[i][1]-1, BallType.IN_TRANSITION))
        ball_state.append(
            (pos_lst[i][1], pos_lst[i][2], BallType.IN_POSSESSION))
        curr_frame = pos_lst[i][2]+1
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
