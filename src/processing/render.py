"""
Video Rendering module for courtline detection and video reencoding.
"""
import cv2 as cv
import random
import os
import numpy as np
from ffmpy import FFmpeg
from state import GameState


# pass in homo matrix +  +
# implement video reencoding
class VideoRender:
    def __init__(self, homography):
        self._TRUE_PATH = os.path.join("data", "true_map.png")
        self._TRUTH_COURT_MAP = cv.imread(self._TRUE_PATH, cv.IMREAD_GRAYSCALE)
        self._HOMOGRAPHY = homography

    def reencode(self, input_path, output_path):
        """
        Re-encodes a MPEG4 video file to H.264 format. Overrides existing output videos if present.
        Deletes the unprocessed video when complete.
        """

        ff = FFmpeg(
            inputs={input_path: "-y"},
            outputs={output_path: "-c:a copy -c:v libx264"},
        )
        ff.run()
        os.remove(input_path)

    def render_video(self, state: GameState, filename: str, fps: int = 30):
        """
        Takes into player position data, applied homography,
        and renders video stored in filename
            state: GameState with at least bounding boxes on it
            filename: file path from project root where video is saved
            fps: frames per second expected of produced video
        """
        frames = state.frames
        players = list(state.players.keys())
        # Create a blank image to use as the background for each frame
        background = cv.cvtColor(self._TRUTH_COURT_MAP, cv.COLOR_GRAY2BGR)
        height, width, _ = background.shape

        # Initialize the video writer
        fourcc = cv.VideoWriter_fourcc(*"mp4v")
        video_writer = cv.VideoWriter(filename, fourcc, fps, (width, height))

        # Define initial positions for each player
        player_state: dict[str, dict] = {}
        for id in players:
            player_state.update(
                {
                    id: {
                        "pos": (0, 0),
                        "detected": False,
                        "color": (
                            random.randint(0, 256),
                            random.randint(0, 256),
                            random.randint(0, 256),
                        ),
                    }
                }
            )

        # find duration of video
        dur = frames[-1].frameno
        fi = 0
        # Loop through each time step
        for t in range(dur + 1):
            # Create a copy of the background image to draw the points on
            frame = background.copy()

            # Get dictionary of positions at each frame
            for id in player_state:
                player_state.get(id).update({"detected": False})  # reset detection
            while fi < len(frames) and frames[fi].frameno <= t:
                f = frames[fi]
                for id in players:  # update pos for each player
                    if id in f.players:
                        b = f.players.get(id).box  # get new player frame
                        x, y = (b.xmin + b.xmax) / 2.0, b.ymax
                        x, y = self._transform_point(x, y)
                        player_state.get(id).update({"pos": (x, y)})
                        player_state.get(id).update({"detected": True})
                fi += 1

            # Loop through each point and draw it on the frame
            for id in players:
                if not player_state.get(id).get("detected"):
                    continue
                pos = player_state[id]["pos"]
                pos = (int(pos[0]), int(pos[1]))
                color = player_state[id]["color"]
                font = cv.FONT_HERSHEY_SIMPLEX
                thickness = 2
                font_scale = 1
                radius = 10
                text_width = cv.getTextSize(id, font, font_scale, thickness)[0][0]
                cv.circle(
                    img=frame, center=pos, radius=radius, color=color, thickness=-1
                )
                cv.putText(
                    img=frame,
                    text=id,
                    org=(pos[0] - (text_width // 2), pos[1] - radius - 10),
                    fontFace=font,
                    fontScale=font_scale,
                    color=color,
                    thickness=thickness,
                    lineType=cv.LINE_AA,
                )

            # Write the frame to the video writer
            video_writer.write(frame)

        # Release the video writer
        video_writer.release()

    def _transform_point(self, x: float, y: float):
        """
        Applies court homography to single point
        @param x,y pixel positions of point on court video
        @returns transformed pixels x,y positions on true court
        """
        point = np.array([x, y], dtype=np.float32)
        point = point.reshape((1, 1, 2))
        transformed_point = cv.perspectiveTransform(point, self._HOMOGRAPHY)
        tx, ty = transformed_point[0, 0]
        return tx, ty
