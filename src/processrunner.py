"""
Runner module for processing and statistics
"""
import state
from state import GameState
from processing import parse, court, render, shot, team


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
        self.state.recompute_possesssions()
        threshold = min(100, len(self.state.frames) / 3)  # in case of short video
        self.state.filter_players(threshold=threshold)
        self.state.recompute_possession_list(threshold=10, join_threshold=20)
        self.state.recompute_pass_from_possession()

    def run_team_detect(self):
        team.split_team(self.state)

    def run_shot_detect(self):
        shot.shots(self.state, window=10)

    def run_courtline_detect(self):
        """Runs courtline detection."""
        c = court.Render(self.video_path)
        self.homography = c.get_homography()

    def run_video_render(self):
        """Runs video rendering and reencodes, stores to output_video_path_reenc."""
        videoRender = render.VideoRender(self.homography)
        videoRender.render_video(self.state, self.output_video_path)
        videoRender.reencode(self.output_video_path, self.output_video_path_reenc)

    def run(self):
        """
        Runs all processing and statistics.
        """
        self.run_parse()
        print("parsing complete!")
        self.run_possession()
        print("possession detection complete!")
        self.run_team_detect()
        print("team detection complete!")
        self.run_shot_detect()
        print("shot detection complete!")
        self.run_courtline_detect()
        print("court detection complete!")
        self.run_video_render()
        print("court render complete!")

    def get_results(self):
        """
        Returns string of processed statistics.
        """
        print(
            "PLAYERS", str(state.todict(self.state.players))
        )  # print the entire GameState
        print("PASSES", str(state.todict(self.state.passes)))
        print("POSSESSIONS", str(state.todict(self.state.possessions)))

        return str(state.todict(self.state))
