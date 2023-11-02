import cv2
from state import GameState

class VideoCreator:
    def __init__(self, game_state: GameState, video_path: str, output_path: str) -> None:
        self.state = game_state
        self.video_path = video_path
        self.output_path = output_path

    def draw_boxes(self, frame, boxes, color, label=""):
        for box in boxes:
            cv2.rectangle(frame, (box.xmin, box.ymin), (box.xmax, box.ymax), color, 2)
            if label:
                cv2.putText(frame, label, (box.xmin, box.ymin - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 2)

    def draw_keypoints(self, frame, keypoints, color):
        for keypoint in keypoints:
            if isinstance(keypoint, (tuple, list)) and len(keypoint) == 2:
                x, y = keypoint
                cv2.circle(frame, (int(x), int(y)), 5, color, -1)

    def run(self):
        cap = cv2.VideoCapture(self.video_path)
        if not cap.isOpened():
            print("Error: Could not open video.")
            return

        fps = cap.get(cv2.CAP_PROP_FPS)
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')

        ret, frame = cap.read()
        if not ret:
            print("Error: Couldn't read the first frame.")
            return

        height, width, _ = frame.shape
        out = cv2.VideoWriter(self.output_path, fourcc, fps, (width, height))

        frame_count = 0
        game_frame_index = 0
        while cap.isOpened():
            if not ret:
                break

            video_timestamp = cap.get(cv2.CAP_PROP_POS_MSEC)
            game_frame = self.state.frames[game_frame_index] if game_frame_index < len(self.state.frames) else None

            if game_frame and game_frame.frameno <= video_timestamp:
                # Draw bounding boxes for players
                for player_id, player_frame in game_frame.players.items():
                    self.draw_boxes(frame, [player_frame.box], (0, 255, 0), label=player_id)
                    self.draw_keypoints(frame, player_frame.keypoints, (0, 255, 0))

                # Draw bounding box for ball
                if game_frame.ball:
                    self.draw_boxes(frame, [game_frame.ball.box], (0, 0, 255), label="Ball")

                game_frame_index += 1

            # Draw frame counter
            cv2.putText(frame, f'Frame: {frame_count}', (width - 150, height - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

            out.write(frame)
            frame_count += 1
            ret, frame = cap.read()

        cap.release()
        out.release()
        cv2.destroyAllWindows()
        print("Video processing complete. Output saved to:", self.output_path)