from state import GameState, ShotAttempt, Box, Interval

class ShotFrame:
    def __init__(self):
        self.top: bool = False
        self.rim: bool = False


def madeshot(state: GameState, inte: Interval, window: int) -> ShotAttempt:
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
    for inte in state.shots:
        sa: ShotAttempt = madeshot(state, inte, window=window)
        state.shot_attempts.append(sa)

    state.populate_players_stats()  # populate players stats
    #state.populate_team_stats()  # populate team stats
    compute_stats(state)

def compute_stats(state:GameState):
    """Computes team scores, player assists, and player rebounds"""
    for shot in state.shot_attempts:
        player = shot.playerid
        team = state.team1 if player in state.team1.players else state.team2.players
        idx_after = -1
        for inte in state.possessions:
            if inte.start >= shot.end:
                idx_after = state.possessions.index(inte)
                break

        if shot.made:
            team.shots_made += 1
            team.points += shot.value()
            # assists
            if idx_after >= 2:
                player_prior = state.possessions[idx_after - 2].playerid
                if player_prior in team.players:
                    state.players[player_prior].assists += 1
        else:
            # rebound
            rebound_player = state.possessions[idx_after].playerid
            state.players[rebound_player].rebounds += 1