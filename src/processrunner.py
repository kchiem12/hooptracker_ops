"""
Runner module for processing and statistics
"""
import state
from state import GameState
from processing import parse, court, render, shot, team, video, trendline, action, possession
from args import DARGS


class ProcessRunner:
    """
    Runner class taking in: original video file path, 2 model output files, render destination path
    Performs player, team, shot, and courtline detection in sequence.
    Effect: updates GameState with statistics and produces courtline video.
    """

    def __init__(self, args=DARGS):
        self.args = args
        self.state: GameState = GameState()

    def run_parse(self):
        "Runs parse module over SORT (and pose later) outputs to update GameState"
        parse.parse_sort_output(self.state, self.args["people_file"])
        self.state.recompute_frame_count()
        if not self.args["skip_player_filter"]:
            # in case of short video
            threshold = min(300, len(self.state.frames) / 3)
            self.state.filter_players(threshold=threshold)

        parse.parse_sort_output(self.state, self.args["ball_file"])
        parse.parse_pose_output(self.state, self.args["pose_file"])

    def run_possession(self):
        """self.state.recompute_possesssions()
        self.state.recompute_possession_list(
            threshold=self.args["filter_threshold"],
            join_threshold=self.args["join_threshold"],
        )"""
        possession_computer = possession.PossessionComputer(
            self.state.frames, self.state.players)  # Assuming frames is a list of frame objects
        self.state.possessions = possession_computer.compute_possessions()
        self.state.recompute_pass_from_possession()

    def run_team_detect(self):
        team.split_team(self.state)

    def run_shot_detect(self):
        action_recognition = action.ActionRecognition(self.state)
        action_recognition.shot_detect()
        shot.shots(self.state, window=self.args["shot_window"])

    def run_courtline_detect(self):
        """Runs courtline detection."""
        if self.args["skip_court"]:
            return
        c = court.Render(self.args["video_file"], display_images=False)
        homography = c.get_homography()
        self.run_video_render(homography)

    def run_video_render(self, homography):
        """Runs video rendering and reencodes, stores to output_video_path_reenc."""
        if self.args["skip_court"]:
            return
        videoRender = render.VideoRender(homography)
        videoRender.render_video(self.state, self.args["minimap_file"])
        videoRender.reencode(
            self.args["minimap_file"], self.args["minimap_temp_file"])

    def run_video_processor(self):
        video_creator = video.VideoCreator(
            self.state, self.args["video_file"], self.args["processed_file"]
        )
        video_creator.run()

    def run_trendline(self):
        """Runs the LinearTrendline process to track and estimate ball position and velocity."""
        trendline_process = trendline.LinearTrendline(self.state, self.args)
        trendline_process.process()

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
        self.run_trendline()
        print("trendline processing complete!")
        self.run_shot_detect()
        print("shot detection complete!")
        self.run_courtline_detect()
        print("court detection and render complete!")
        self.run_video_processor()
        print("stats video render complete!")

    def get_results(self):
        """
        Returns string of processed statistics.
        """

        return str(state.todict(self.state))
