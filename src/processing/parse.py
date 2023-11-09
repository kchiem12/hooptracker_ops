"""
Parsing module for parsing all
models outputs into the state
"""
from state import GameState, Frame, ObjectType, Box
import json


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


def parse_pose_output(state: GameState, pose_data_json: str) -> None:
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
    with open(pose_data_json, "r") as f:
        pose_data = json.load(f)

    sts = state.frames
    p = 0  # index of pose_data
    s = 0  # index of state.frames

    while p < len(pose_data) and s < len(sts):
        # match frames up
        state_frame = sts[s]
        state_frameno = state_frame.frameno
        pose_frame = pose_data[p]
        pose_frameno = pose_frame.get("frame", state_frameno)  # defaults to match 1:1
        if state_frameno < pose_frameno:
            s += 1
            continue
        elif state_frameno > pose_frameno:
            p += 1
            continue

        # Retrieve the list of persons (players) from the current frame's data. If not found, default to an empty list.
        frame_persons = pose_frame.get("persons", [])
        if not frame_persons:
            print("No persons data found in this frame")
            continue

        # Iterate through each person in the frame.
        for person in frame_persons:
            bounding_box = person.get("box")
            if bounding_box is None:
                print("No bounding box data found for this person")
                continue

            # Unpack the bounding box coordinates and create a Box object.
            xmin, ymin, xmax, ymax = bounding_box
            pose_box = Box(xmin, ymin, xmax, ymax)

            # Initialize variables to keep track of the most likely player ID and the area of intersection.
            likely_id = [None, -1]
            # Iterate through each player in the frame.
            for player_id, player_frame in state_frame.players.items():
                # Calculate the area of intersection between the person's box and the player's box.
                intersection_area = pose_box.area_of_intersection(player_frame.box)
                # If the intersection area is greater than the current maximum, update the most likely player ID and area.
                if intersection_area > likely_id[1]:
                    likely_id = [player_id, intersection_area]

            # If a likely player is found, set the keypoints for that player. Otherwise, print a message.
            if likely_id[0] is not None:
                state_frame.players[likely_id[0]].set_keypoints(
                    person.get("keypoints"), person.get("confidences")
                )
                state_frame.players[likely_id[0]].set_angles(
                    person.get("angles")
                )
            else:
                print("No likely player found for this person")
        p += 1  # next pose frame
