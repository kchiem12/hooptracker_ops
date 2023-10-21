"""
Parsing module for parsing all
models outputs into the state
"""
from state import *


def parse_sort_output(state: GameState, sort_output) -> None:
    """
    Reads the SORT output and updates state.states frame-by-frame.
    Input:
      state [GameState]: GameState object
      sort_output [str]: path to SORT output file (right now for STRONGSORT)
    Assumptions:
      Frame numbers are shared between outpute files
      If rim is not detected, the rim from the previous frame will be supplied
      Object type number given in state.ObjectType
      Based on StrongSORT output
    """
    file = open(sort_output, "r")
    lines = [[int(x) for x in line.split()] for line in file.readlines()]
    file.close()

    sts = state.states
    b = 0  # index of line in ball
    s = 0  # index of state
    while b < len(lines):
        # TODO modify for BoT-SORT output
        frame, obj_type, id, xmin, ymin, xwidth, ywidth = lines[b][:7]
        sF: Frame = sts[s]
        if s <= len(sts):  # s-1 frameno < bframe, s = len(states)
            sts.append(Frame(frame))
        elif frame < sF.frameno:  # s-1 frameno < bframe < s frameno
            sts.insert(s, Frame(frame))
        elif frame > sF.frameno:
            if sF.rim is None and s > 0:
                sF.rim = sts[s - 1].rim  # ensure rim set
            s += 1
            continue

        sF: Frame = sts[s]  # frame to be updated DO NOT DELETE LINE
        assert sF.frameno == frame
        if obj_type is ObjectType.BALL.value:
            bs = BallState(xmin, ymin, xmax=xmin + xwidth, ymax=ymin + ywidth)
            id = "ball_" + id
            sF.balls.update({id: bs})
        elif obj_type is ObjectType.PLAYER.value:
            ps = PlayerState(xmin, ymin, xmax=xmin + xwidth, ymax=ymin + ywidth)
            id = "player_" + id
            sF.players.update({id: ps})
        elif obj_type is ObjectType.RIM.value:
            box = Box(xmin, ymin, xmax=xmin + xwidth, ymax=ymin + ywidth)
            sF.rim = box

        b += 1  # process next line
