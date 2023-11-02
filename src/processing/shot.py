from state import GameState, ShotAttempt, Box, Interval


class ShotFrame:
    def __init__(self):
        self.top: bool = False
        self.rim: bool = False


def detect_shot(state: GameState, inte: Interval, window: int) -> ShotAttempt:
    """
    Returns a ShotAttempt analyzing frames along the interval
        window: margin of error in frames from top to rim box
    """
    sa = ShotAttempt(inte.playerid, inte.start, inte.end)
    sfs: list[ShotFrame] = []
    for i in range(sa.start, sa.end + 1):  # construct sfs of shot frames
        rim = state.frames[i].rim
        h = rim.ymax - rim.ymin
        top = Box(rim.xmin, rim.ymin - h, rim.xmax, rim.ymax - h)  # top rim box
        ball = state.frames[i].ball

        sf = ShotFrame()
        if ball is None or rim is None:
            pass
        else:
            if ball.box.intersects(top):
                sf.top = True
            if rim.contains(ball.box):
                sf.rim = True
        sfs.append(sf)

    r = 0  # freq rim intersects in window
    for i in range(len(sfs) - window):
        if sfs[i + window].rim:
            r += 1  # add to window
        if sfs[i].top and r > 0:
            sa.made = True  # made shot detected
            sa.frame = i + sa.start
        if sfs[i].rim:
            r -= 1  # remove from window

    return sa


def shots(state: GameState, window: int):
    """
    Calculate shots throughout game
        window: margin of error in frames from top to rim box
    Assumption:
        shots are counted as breaks between possesssions
    """
    # Create intervals of shots
    shots: list[Interval] = []
    poss = state.possessions
    for i in range(len(poss) - 1):
        p1 = poss[i]
        p2 = poss[i + 1]
        shots.append(Interval(p1.playerid, p1.end, p2.start))

    for inte in shots:
        sa: ShotAttempt = detect_shot(state, inte, window=window)
        state.shot_attempts.append(sa)

    state.populate_players_stats() # populate players stats
    state.populate_team_stats() # populate team stats
