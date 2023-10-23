from state import GameState, ShotAttempt, Box, Interval


class ShotFrame:
    def __init__(self):
        self.top: bool = False
        self.rim: bool = False


def detect_shot(state: GameState, inte: Interval, window: int) -> ShotAttempt:
    sa = ShotAttempt(inte.start, inte.end)
    sfs: list[ShotFrame] = []
    for i in range(sa.start, sa.end + 1):  # construct sfs of shot frames
        rim = state.frames[i].rim
        h = rim.ymax - rim.ymin
        top = Box(rim.xmin, rim.ymin - h, rim.xmax, rim.ymax - h)  # top rim box
        ball = state.frames[i].ball

        sf = ShotFrame()
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
        if sfs[i].rim:
            r -= 1  # remove from window

    return sa
