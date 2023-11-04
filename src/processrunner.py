"""
Runner module for processing and statistics
"""
import state
from state import GameState
from processing import parse, court, render, shot, team, video


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
        pose_json,
        output_video_path,
        output_video_path_reenc,
        processed_video_path,
    ):
        self.video_path = video_path
        self.players_tracking = players_tracking
        self.ball_tracking = ball_tracking
        self.pose_json = pose_json
        self.output_video_path = output_video_path
        self.output_video_path_reenc = output_video_path_reenc
        self.state: GameState = GameState()
        self.processed_video_path = processed_video_path

    def run_parse(self):
        "Runs parse module over SORT (and pose later) outputs to update GameState"
        parse.parse_sort_output(self.state, self.players_tracking)
        threshold = min(300, len(self.state.frames) / 3)  # in case of short video
        self.state.filter_players(threshold=threshold)

        parse.parse_sort_output(self.state, self.ball_tracking)
        parse.parse_pose_output(self.state, self.pose_json)

    def run_possession(self):
        self.state.recompute_possesssions()
        self.state.recompute_possession_list(threshold=10, join_threshold=20)
        self.state.recompute_pass_from_possession()

    def run_team_detect(self):
        team.split_team(self.state)

    def run_shot_detect(self):
        shot.shots(self.state, window=10)

    def run_courtline_detect(self):
        """Runs courtline detection."""
        c = court.Render(self.video_path, display_images=False)
        self.homography = c.get_homography()

    def run_video_render(self):
        """Runs video rendering and reencodes, stores to output_video_path_reenc."""
        videoRender = render.VideoRender(self.homography)
        videoRender.render_video(self.state, self.output_video_path)
        videoRender.reencode(self.output_video_path, self.output_video_path_reenc)

    def run_video_processor(self):
        video_creator = video.VideoCreator(
            self.state, self.video_path, self.processed_video_path
        )
        video_creator.run()

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
        print('court render complete!')
        self.run_video_processor()
        print("stats video render complete!")

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
