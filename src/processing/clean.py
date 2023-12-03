from state import GameState, Frame


class Clean:
    def __init__(self, state: GameState):
        self.state = state

    def run(self, window:int):
        self.clean_ball(window)

    def incr(self, d: dict[str, int], fr: Frame, incr=1):
        "increments frequency of seen ball in frame by 1"
        for b in fr.ball_candidates:
            d[b] = d.get(b, 0) + incr

    def decr(self, d: dict[str, int], fr: Frame):
        "decrements frequency of seen ball in frame by 1"
        self.incr(d, fr, incr=-1)

    def clean_ball(self, window:int):
        "assigns ball with highest frame frequency over a window"
        freq: dict[str, int] = {}  # freq of id over winow
        frames = self.state.frames
        window = int(window / 2)
        for i in range(min(window, len(frames))):
            self.incr(freq, frames[i])
        for i, cur_fr in enumerate(frames):
            if i + window < len(frames):  # add new
                self.incr(freq, frames[i + window])
            max_v = max(freq.values())
            max_ks = [k for k, v in freq.items() if v == max_v]  # best keys
            for k in max_ks:
                if k in cur_fr.ball_candidates:
                    cur_fr.ball = cur_fr.ball_candidates[k]
                    break
            if i - window >= 0:
                self.decr(freq, frames[i - window])  # remove old
