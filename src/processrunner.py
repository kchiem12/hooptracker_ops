"""
Runner module for processing and statistics
"""
from state import GameState
from processing import general_detect, team_detect, shot_detect, courtline_detect, video_render
class ProcessRunner:
    """
    Runner class taking in: original video file path, 2 model output files, render destination path
    Performs player, team, shot, and courtline detection in sequence.
    Effect: updates GameState with statistics and produces courtline video.
    """
    def __init__(self, video_path, players_tracking, ball_tracking, output_video_path, 
                 output_video_path_reenc) -> None:
        self.video_path = video_path
        self.players_tracking = players_tracking
        self.ball_tracking = ball_tracking
        self.output_video_path = output_video_path
        self.output_video_path_reenc = output_video_path_reenc
        self.state = GameState()


    def run_general_detect(self):
        """Runs various detection modules that updates GameState's rim states, ball"""
        rim_info, frames = general_detect.parse_output(self.state, self.players_tracking)
        self.state.rim, self.state.states = rim_info, frames
        general_detect.parse_ball(self.state, self.ball_tracking)


    def run_team_detect(self):
        """
        TODO figure out how to decouple team and general processing more
        TODO explain pos_list
        Splits identified players into teams, then curates:
        ball state, passes, player possession, and team possession
        """
        teams, pos_list, playerids = team_detect.team_split(self.state.states)
        self.state.possession_list = pos_list
        for pid in playerids:
            self.state.players[pid] = {'shots': 0, "points": 0, "rebounds": 0, "assists": 0}
        self.state.ball_state = general_detect.ball_state_update(pos_list,
                                                                 len(self.state.states) - 1)
        self.state.passes = general_detect.player_passes(pos_list)
        self.state.possession = general_detect.player_possession(pos_list)

        self.state.team1 = teams[0]
        self.state.team2 = teams[1]

        self.state.team1_pos, self.state.team2_pos = team_detect.compute_possession(
            self.state.possession, self.state.team1)


    def run_shot_detect(self):
        """Runs shot detection and updates scores."""
        #TODO figure out madeshot and resolve conflict in state & takuma module
        made_shots = shot_detect.madeshot(self.players_tracking)
        self.state.update_scores(made_shots)


    def run_courtline_detect(self):
        """Runs courtline detection."""
        court = courtline_detect.Render(self.video_path)
        self.homography = court.get_homography()
        # court.render_video(self.state.states, self.state.players, self.output_video_path)


    def run_video_render(self):
        """Runs video rendering and reencodes, stores to output_video_path_reenc."""
        videoRender = video_render.VideoRender(self.homography)
        videoRender.render_video(self.state.states, self.state.players, self.output_video_path)
        videoRender.reencode(self.output_video_path, 
                              self.output_video_path_reenc)


    def run(self):
        """
        Runs all processing and statistics.
        """
        self.run_general_detect()
        self.run_team_detect()
        self.run_shot_detect()
        self.run_courtline_detect()
        self.run_video_render()


    def get_results(self):
        """
        Returns string of processed statistics.
        """
        return repr(self.state)
