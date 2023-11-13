"""
Parsing module for parsing all
models outputs into the state
"""
from state import GameState, Frame, ObjectType, Box
from pose_estimation.pose_estimate import AngleNames, KeyPointNames

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


def parse_pose_output(state: GameState, pose_output: str) -> None:
    """
    Parses pose data and updates the player frames in the game state.

    Inputs:
    - state (GameState): The game state object to be updated.
    - pose_data_json (str): File path to the pose data JSON file.

    Notes:
    - Pose data is expected to be in JSON format with keypoint information for each player in each frame.
    - The function assumes the frames in the pose data are in the same order as in the game state.
    """
    # Open the pose data JSON file and load its content.
    # Expect list of data [frame_data]
    file = open(pose_output, "r")
    lines = [[int(x) for x in line.split()] for line in file.readlines()]
    file.close()

    kpn = len(KeyPointNames.list) # number of keypoints
    an = len(AngleNames.list) # number of angles

    sts = state.frames
    p = 0  # index of pose_data
    s = 0  # index of state.frames

    while p < len(lines) and s < len(sts):
        # match frames up
        state_frame = sts[s]
        state_frameno = state_frame.frameno
        frameno, _, _, x, y, w, h = lines[p][:7]
        if state_frameno < frameno:
            s += 1
            continue
        elif state_frameno > frameno:
            p += 1
            continue

        # Iterate through each person in the frame
        bbox = Box(x, y, x + w, y + h)
        likely_id = [None, -1]
        for id, pf in state_frame.players.items():
            pbox = pf.box
            
            # Calculate the area of intersection between the person's box and the player's box.
            intersection_area = bbox.area_of_intersection(pbox)
            # If the intersection area is greater than the current maximum, update the most likely player ID and area.
            if intersection_area > likely_id[1]:
                likely_id = [id, intersection_area]

            # If a likely player is found, set the keypoints for that player. Otherwise, print a message.
            if likely_id[0] is not None:
                state_frame.players[likely_id[0]].set_keypoints(
                    lines[p][7:7+2*kpn]
                )
                state_frame.players[likely_id[0]].set_angles(
                    lines[p][7+2*kpn:7+2*kpn+an]
                )
            else:
                print("No likely player found for this person")
        p += 1  # next pose frame
