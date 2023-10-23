"""
Parsing module for parsing all
models outputs into the state
"""
from state import GameState, Frame, ObjectType


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

    sts = state.frames
    b = 0  # index of line in ball
    s = 0  # index of state
    while b < len(lines):
        frame, obj_type, id, xmin, ymin, xwidth, ywidth = lines[b][:7]
        if s >= len(sts):  # s-1 frameno < bframe, s = len(states)
            sts.append(Frame(frame))
        elif frame < sts[s].frameno:  # s-1 frameno < bframe < s frameno
            sts.insert(s, Frame(frame))
        elif frame > sts[s].frameno:
            if sts[s].rim is None and s > 0:
                sts[s].rim = sts[s - 1].rim  # ensure rim set
            s += 1
            continue

        sF: Frame = sts[s]
        assert sF.frameno == frame
        box = (xmin, ymin, xmin + xwidth, ymin + ywidth)
        if obj_type is ObjectType.BALL.value:
            sF.set_ball_frame(id, *box)
        elif obj_type is ObjectType.PLAYER.value:
            sF.add_player_frame(id, *box)
        elif obj_type is ObjectType.RIM.value:
            sF.set_rim_box(id, *box)

        b += 1  # process next line
