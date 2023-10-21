from typing import List, Tuple
from state import GameState, ShotAttempt, ShotType, Box

# TODO revamp this method using new ball states
def madeshot(state:GameState, start:int, end:int) -> List[Tuple[int, int]]:
    """
    Accepts a strongsort text file path as an input, and outputs the frame
    intervals in which a shot was made. Ex: If a shot was made between the
    frames 0 and 10, the output of madeshot() will be [(0, 10)].
    """
    # Initialize values
    shots_made = []
    passed_top = False
    passed_rim = False
    top_collision_start = 0
    top_collision_end = 0
    rim_collision_start = 0
    rim_collision_end = 0

    for frame in state.states[start:end]:
        rim: Box = frame.rim
        # ball index = 0
        if frame.ball is not None:
            # Take the center coordinates of the ball
            ball_x = (frame.ball.box.xmin + frame.ball.box.xmax)/2
            ball_y = (frame.ball.box.ymin + frame.ball.box.ymax)/2
            # check to see if ball is in top box
            in_top_x = (ball_x >= rim.xmin and ball_x <= rim.xmin + rim.xmax)
            in_top_y = (ball_y <= rim.ymin and ball_y >= rim.ymin - rim.ymax)
            if not passed_top:
                if in_top_x and in_top_y and (frame.frameno not in
                                              range(top_collision_start,
                                                    top_collision_end)):
                    top_collision_start = frame.frameno
                    passed_top = True
            else:
                if not in_top_x or not in_top_y:
                    top_collision_end = frame.frameno

            #check to see if ball is in rim box
            in_rim_x = (ball_x >= rim.xmin and ball_x <= rim.xmin + rim.xmax)
            in_rim_y = (ball_y <= rim.ymin and ball_y >= rim.ymin - rim.ymax)
            if not passed_rim:
                if in_rim_x and in_rim_y and (frame.frameno not in
                                              range(rim_collision_start,
                                                    rim_collision_end)):
                    rim_collision_start = frame.frameno
                    passed_rim = True
            else:
                if not in_rim_x or not in_rim_y:
                    rim_collision_end = frame.frameno
            # if the ball has passed both the top and the rim box, then
            # a shot has been made, and is added to the shots_made list
            if passed_top and passed_rim:
                shots_made.append((top_collision_start, rim_collision_end))

                # Reset all the values
                passed_top = False
                passed_rim = False
                top_collision_start = 0
                top_collision_end = 0
                rim_collision_start = 0
                rim_collision_end = 0
            
    return shots_made


    # old code
    with open(file_path, 'r') as f:
        lines = f.readlines()
        for line in lines:
            # Convert each text file line into an int list
            lst = [int(i) for i in line.split()]
            frame = lst[0]

            # Ball index = 0
            if lst[1] == 0:
                # Take the center coordinates of the ball
                ball_x = lst[3] + lst[5]/2
                ball_y = lst[4] - lst[6]/2

                # Check to see if ball is in top box
                in_top_x = (ball_x >= top[0] and ball_x <= top[0] + top[2])
                in_top_y = (ball_y <= top[1] and ball_y >= top[1] - top[3])
                if not passed_top:
                    if in_top_x and in_top_y and (frame not in
                                                  range(top_collision_start,
                                                        top_collision_end)):
                        top_collision_start = frame
                        passed_top = True
                else:
                    if not in_top_x or not in_top_y:
                        top_collision_end = frame


                # Check to see if ball is in rim box
                in_rim_x = (ball_x >= rim[0] and ball_x <= rim[0] + rim[2])
                in_rim_y = (ball_y <= rim[1] and ball_y >= rim[1] - rim[3])
                if not passed_rim:
                    if in_rim_x and in_rim_y and (frame not in
                                                  range(rim_collision_start,
                                                        rim_collision_end)):
                        rim_collision_start = frame
                        passed_rim = True
                else:
                    if not in_rim_x or not in_rim_y:
                        rim_collision_end = frame

                # If the ball has passed both the top and the rim box, then
                # a shot has been made, and is added to the shots_made list
                if passed_top and passed_rim:
                    shots_made.append((top_collision_start, rim_collision_end))

                    # Reset all the values
                    passed_top = False
                    passed_rim = False
                    top_collision_start = 0
                    top_collision_end = 0
                    rim_collision_start = 0
                    rim_collision_end = 0

    # return shots_made
    # TODO this algorithm currently does not work for the current model outputs.
    # TEMPORARY FIX: return the results ran on an older output
    return [(131, 131), (132, 0), (629, 629), (630, 0), (1244, 0), (1561, 1561), (1562, 0)]

if __name__ == '__main__':
    print(madeshot('tmp/people.txt'))
