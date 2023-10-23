"""
Runner module for processing and statistics
"""
from state import GameState
from processing import (
    parse,
    general_detect,
    team_detect,
    shot_detect,
    courtline_detect,
    video_render,
)


class ProcessRunner:
    """
    Runner class taking in: original video file path, 2 model output files, render destination path
    Performs player, team, shot, and courtline detection in sequence.
    Effect: updates GameState with statistics and produces courtline video.
    """

    def __init__(
        self,
        video_path,
        players_tracking,
        ball_tracking,
        output_video_path,
        output_video_path_reenc,
    ):
        self.video_path = video_path
        self.players_tracking = players_tracking
        self.ball_tracking = ball_tracking
        self.output_video_path = output_video_path
        self.output_video_path_reenc = output_video_path_reenc
        self.state: GameState = GameState()

    def run_parse(self):
        "Runs parse module over SORT (and pose later) outputs to update GameState"
        parse.parse_sort_output(self.state, self.players_tracking)
        parse.parse_sort_output(self.state, self.ball_tracking)

    def run_possession(self):
        self.state.filter_players(threshold=100)
        self.state.recompute_possession_list(threshold=20, join_threshold=20)
        self.state.recompute_pass_from_possession()

    def run_team_detect(self):
        team_detect.split_team(self.state)

    def run_shot_detect(self):
        """Runs shot detection and updates scores."""
        # TODO figure out madeshot and resolve conflict in state & takuma module
        made_shots = shot_detect.madeshot(
            self.state
        )  # state already has rim information
        self.state.update_scores(made_shots)

    def run_courtline_detect(self):
        """Runs courtline detection."""
        court = courtline_detect.Render(self.video_path)
        self.homography = court.get_homography()

    def run_video_render(self):
        """Runs video rendering and reencodes, stores to output_video_path_reenc."""
        videoRender = video_render.VideoRender(self.homography)
        videoRender.render_video(
            self.state.frames, self.state.players, self.output_video_path
        )
        videoRender.reencode(self.output_video_path, self.output_video_path_reenc)

    def run(self):
        """
        Runs all processing and statistics.
        """
        self.run_parse()
        self.run_possession()
        self.run_team_detect()
        self.run_shot_detect()
        print('G, T, S detect fine')
        self.run_courtline_detect()
        print('courtline detect fine')
        self.run_video_render()
        print('video render fine')

    def get_results(self):
        """
        Returns string of processed statistics.
        """
        return repr(self.state)
