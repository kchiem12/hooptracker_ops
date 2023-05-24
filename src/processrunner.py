"Runner module for processing and statistics"
class ProcessRunner:
    """
    Runner class taking in: original video file path and the 2 model output files
    Performs player, team, shot, and courtline detection in sequence.
    Effect: updates GameState with statistics and produces courtline video. 
    """
    def __init__(self, video_path, players_tracking, ball_tracking) -> None:
        self.video_path = video_path
        self.players_tracking = players_tracking
        self.ball_tracking = ball_tracking       

    
    def run_player_detect(self):
        pass


    def run_team_detect(self):
        pass


    def run_shot_detect(self):
        pass


    def run_courtline_detect(self):
        pass


    def run(self):
        pass
