import cv2 as cv
import random
import os
import numpy as np
import subprocess
import sys

# pass in homo matrix +  + 
# implement video reencoding 

class VideoRender:
    def __init__(self, homography):
        self._TRUE_PATH = os.path.join('data','true_map.png')
        self._TRUTH_COURT_MAP = cv.imread(self._TRUE_PATH,cv.IMREAD_GRAYSCALE)
        self._HOMOGRAPHY = homography


    def reencode(self, input_path, output_path):
        """
        Re-encodes a MPEG4 video file to H.264 format. Overrides existing output videos if present.
        Deletes the unprocessed video when complete.
        Ensures ffmpeg dependency is installed
        """

        if sys.platform != 'darwin':
            print("Designed to install dependency for macOS")
        else:
            try:
                # check if it is installed already
                subprocess.run(["brew", "list", "ffmpeg"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            except:
                # install dependency
                print("Installing ffmpeg")
                try:
                    subprocess.run(["brew", "install", "ffmpeg"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                except:
                    print("Error installing ffmpeg")
                    return

        reencode_command = f'ffmpeg -y -i {input_path} -vcodec libx264 -c:a copy {output_path}'
        os.system(reencode_command)
        # os.remove(input_path)
    
    
    def render_video(self,states:list,players:dict,filename:str,fps:int=30):
        '''
        Takes into player position data, applied homography,
        and renders video stored in filename
        @param states, list of dictionaries,
        each represent a frame with state info in chronological order
        @param players, dictionary of players where keys are players
        @param filename, file path from project root where video is saved
        @param fps, frames per second expected of produced video
        '''
        players=players.keys()
        # Create a blank image to use as the background for each frame
        background = cv.cvtColor(self._TRUTH_COURT_MAP,cv.COLOR_GRAY2BGR)
        height, width, _ = background.shape

        # Initialize the video writer
        fourcc = cv.VideoWriter_fourcc(*'H264')
        video_writer = cv.VideoWriter(filename, fourcc, fps, (width,height))

        # Define initial positions for each player
        player_state = {}
        for player in players:
            player_state.update({player:{'pos':(0,0),
                                        'color':(random.randint(0,256),random.randint(0,256),random.randint(0,256))}})

        # find duration of video
        dur = states[-1]["frameno"]
        states += [{"frameno":dur+fps,"players":{}}]
        frame_index = 0
        # Loop through each time step
        for t in range(1,dur+10):
            # Create a copy of the background image to draw the points on
            frame = background.copy()

            # Get dictionary of positions at each frame
            while (states[frame_index]["frameno"]<=t):
                state = states[frame_index]
                player_info = state['players']
                for player in players:
                    if player in player_info:
                        pd = player_info[player]
                        ps = player_state[player]
                        x, y = (pd['xmin']+pd['xmax'])/2.0, pd['ymax']-5
                        x1, y1 = self._transform_point(x,y)
                        x0, y0 = ps['pos']
                        x1, y1 = (2*x1+x0)/3.0, (2*y1+y0)/3.0
                        ps.update({'pos':(x1, y1)})
                if frame_index>=len(states)-2>= 0 or states[frame_index+1]["frameno"] > t: # release if at end of contig
                    break
                frame_index += 1


            # Loop through each point and draw it on the frame
            for player in players:
                pos = player_state[player]['pos']
                pos = (int(pos[0]),int(pos[1]))
                color = player_state[player]['color']
                font = cv.FONT_HERSHEY_SIMPLEX
                thickness = 2
                font_scale = 1
                radius = 10
                text_width = cv.getTextSize(player, font, font_scale, thickness)[0][0]
                cv.circle(img=frame, center=pos, radius=radius, color=color, thickness=-1)
                cv.putText(img=frame,text=player,org=(pos[0]-(text_width//2),pos[1]-radius-10),
                           fontFace=font,fontScale=font_scale,color=color,thickness=thickness,lineType=cv.LINE_AA)

            # Write the frame to the video writer
            video_writer.write(frame)

        # Release the video writer
        video_writer.release()

    def _transform_point(self,x:float,y:float):
        '''
        Applies court homography to single point
        @param x,y pixel positions of point on court video
        @returns transformed pixels x,y positions on true court
        '''
        point = np.array([x, y], dtype=np.float32)
        point = point.reshape((1, 1, 2))
        transformed_point = cv.perspectiveTransform(point, self._HOMOGRAPHY)
        tx, ty = transformed_point[0, 0]
        return tx, ty
