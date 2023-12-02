
from state import Interval
from collections import deque


class PossessionComputer:
    def __init__(self, frames):
        self.frames = frames
        self.rolling_scores = []
        self.dominant_possessions = []
        self.possessions = []

    def compute_possessions(self):
        self._compute_frame_rankings()
        self._compute_rolling_scores()
        self._determine_dominant_possessions()
        self._create_possession_intervals(min_length=15)

        # for interval in self.possessions:
        # print(interval.playerid, interval.start, interval.end)

        return self.possessions

    # TODO give no one possession during shots
    def _compute_frame_rankings(self):
        """
        Compute frame-by-frame possession of the ball.
        Players are ranked based on their distance to the ball and the intersection area.
        The ranks are added together, and the player with the lowest score is considered
        the most likely possessor.
        """
        for index, frame in enumerate(self.frames):
            if frame.ball is None:
                frame.possessions = []
                continue

            distance_ranking = []
            area_ranking = []
            ball_box = frame.ball.box

            for player_id, player in frame.players.items():
                dist = player.box.distance_between_boxes(ball_box)
                intersection_area = player.box.area_of_intersection(ball_box)

                distance_ranking.append((player_id, dist))
                # Negative area for sorting purpose
                area_ranking.append((player_id, -intersection_area))

            # Rank players by distance (lower is better) and intersection area (higher is better)
            distance_ranking.sort(key=lambda x: x[1])
            area_ranking.sort(key=lambda x: x[1])

            # Combine ranks
            combined_ranks = {}
            for i, (player_id, _) in enumerate(distance_ranking):
                combined_ranks[player_id] = combined_ranks.get(
                    player_id, 0) + (i * 1)
            for i, (player_id, _) in enumerate(area_ranking):
                combined_ranks[player_id] = combined_ranks.get(
                    player_id, 0) + (i * 1)

            # Sort by combined ranks, lower rank indicates better possession
            sorted_combined_ranks = sorted(
                combined_ranks.items(), key=lambda x: x[1])
            frame.possessions = [player_id for player_id,
                                 _ in sorted_combined_ranks][:3]

            # print(f"frame {index}: {frame.possessions}")

    def _compute_rolling_scores(self):
        """
        Calculate and store the frame-by-frame score for each player based on their possession position.
        This score is stored in a rolling window covering the last 50 frames.
        """
        # Initialize an empty list for rolling scores
        self.rolling_scores = []

        for index, frame in enumerate(self.frames):
            # Dictionary to hold scores for each player in this frame
            frame_scores = {}

            # Assign points based on possession position (1 for 1st, 0.75 for 2nd, 0.25 for 3rd)
            for i, player_id in enumerate(frame.possessions[:2]):
                points = [1, 0.7, 0.25][i]
                frame_scores[player_id] = frame_scores.get(
                    player_id, 0) + points

            # Append the scores of this frame to the rolling window
            self.rolling_scores.append(frame_scores)

    def _determine_dominant_possessions(self):
        """
        Determine the dominant player in possession for each frame based on the rolling window of the last 50 frames.
        """
        # Initialize an empty list to store the dominant player for each frame
        self.dominant_possessions = []

        for i in range(len(self.frames)):
            # Dictionary to sum up scores in the rolling window for each player
            rolling_sum = {}

            # Accumulate scores for each player in the rolling window of the last 50 frames
            for j in range(max(0, i - 49), i + 1):
                for player_id, score in self.rolling_scores[j].items():
                    rolling_sum[player_id] = rolling_sum.get(
                        player_id, 0) + score

            # Determine the player with the highest score in this rolling window
            if rolling_sum:
                self.dominant_possessions.append(
                    max(rolling_sum, key=rolling_sum.get))
            else:
                self.dominant_possessions.append(None)

    def _create_possession_intervals(self, min_length):
        """
        Create possession intervals from the dominant players list using the Interval class.
        Shorter intervals (less than min_length) are first dropped, then the intervals are created.
        """
        self.possessions = []  # List to store the intervals
        cleaned_possessions = self._remove_short_intervals(min_length)

        current_interval = None

        for i, player_id in cleaned_possessions:
            if current_interval and player_id == current_interval.playerid:
                current_interval.end = i
                current_interval.length = current_interval.end - current_interval.start + 1
            else:
                if current_interval:
                    self.possessions.append(current_interval)
                current_interval = Interval(player_id, i, i)

        if current_interval:
            self.possessions.append(current_interval)

    def _remove_short_intervals(self, min_length):
        """
        Remove short intervals from the dominant possessions list. Helper function for _create_possession_intervals
        """
        cleaned_possessions = []
        current_player = None
        start_index = 0

        for i, player_id in enumerate(self.dominant_possessions):
            if player_id != current_player:
                if i - start_index >= min_length:
                    for index in range(start_index, i):
                        cleaned_possessions.append((index, current_player))
                start_index = i
                current_player = player_id

        # Check the last interval
        if len(self.dominant_possessions) - start_index >= min_length:
            for index in range(start_index, len(self.dominant_possessions)):
                cleaned_possessions.append((index, current_player))

        return cleaned_possessions


'''
    def run_possession(self):
        possession_computer = possession.PossessionComputer(
            self.state.frames)  # Assuming frames is a list of frame objects
        self.state.possessions = possession_computer.compute_possessions()

'''
