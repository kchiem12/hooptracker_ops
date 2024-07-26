import sys
import os
import io
import ast
import streamlit as st
import hydralit_components as hc
import pandas as pd
import requests
import zipfile
import shutil

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from main import main

st.set_page_config(page_title="HoopTracker", page_icon=":basketball:")
# 'set up tab tile and favicon'

# Initialize Session States:
# 0 = Default State : No Video Uploaded --> Prompts For Upload / Home Screen Demo
# 1 = Uploading/Processing State --> Loading Screen
# 2 = Done Processing, Show Statistics, Allow Exporting
if "state" not in st.session_state:
    st.session_state.state = 0
    st.session_state.logo = "src/view/static/basketball.png"
    with open("data/short_new_1.mp4", "rb") as file:
        st.session_state.video_file = io.BytesIO(file.read())
    st.session_state.processed_video = None
    st.session_state.result_string = None
    st.session_state.upload_name = None
    st.session_state.user_file = "tmp/user_upload.mp4"

# Backend Connection
SERVER_URL = "http://3.95.210.247:8000/"


def process_video(video_file):
    """
    Takes in a mp4 file at video_file and uploads it to the backend, then stores
    the processed video name into session state
    Temporarily: stores the processed video into tmp/user_upload.mp4
    """

    # delete any unzipped files
    shutil.rmtree("unzipped_files", ignore_errors=True)

    user_video: str = st.session_state.user_file
    # UPLOAD VIDEO
    if video_file is None:
        return False
    r = requests.post(
        SERVER_URL + "upload", files={"video_file": video_file}, timeout=60
    )
    if r.status_code == 200:
        print("Successfully uploaded file")
        data = r.json()
        st.session_state.upload_name = data.get("message")
        # with open(user_video, "wb") as f:  # TODO is local write; temp fix
        #     f.write(video_file.getvalue())
    else:
        print("Error uploading file")  # TODO make an error handler in frontend
        return False
    st.session_state.is_downloaded = False

    # PROCESS VIDEO
    print("User Video", user_video)
    print("Upload Name", st.session_state.upload_name)

    # ASSUME process updates results locally for now TODO
    r = requests.post(
        SERVER_URL + "process", params={"file_name": st.session_state.upload_name}
    )
    if r.status_code == 200:
        print(r.json().get("message"))
        # with open("tmp/results.txt", "r") as file:
        #     st.session_state.result_string = file.read()
        # st.session_state.processed_video = "tmp/court_video_reenc.mp4"
    else:
        print(f"Error processing file: {r.text}")
        return False

    return download_results(st.session_state.upload_name)


def upload(video_file):
    user_video: str = st.session_state.user_file
    if video_file is None:
        print("No video")
    else:
        r = requests.post(
            SERVER_URL + "upload", files={"video_file": video_file}, timeout=120
        )
        if r.status_code == 200:
            print("Successfully uploaded file")
            data = r.json()
            print(data)
            st.session_state.upload_name = data.get("message")
            with open(user_video, "wb") as f:  # TODO is local write; temp fix
                f.write(video_file.getvalue())
        else:
            print("Error uploading file")  # TODO make an error handler in frontend
            return False
        st.session_state.is_downloaded = False


def health_check():
    r = requests.get(SERVER_URL, timeout=120)
    if r.status_code == 200:
        print("Successfully got file")
        data = r.json()
        print(data.get("message"))
    else:
        print("Error getting file")  # TODO make an error handler in frontend
        return False
    st.session_state.is_downloaded = False


def download_results(upload_name):
    r = requests.get(f"{SERVER_URL}download/{upload_name}")
    if r.status_code == 200:
        zip_file_path = "downloaded_files.zip"
        with open(zip_file_path, "wb") as file:
            file.write(r.content)

        # unzip the files
        unzip_dir = "unzipped_files"
        os.makedirs(unzip_dir, exist_ok=True)

        # unzip the files
        with zipfile.ZipFile(zip_file_path, "r") as zip_ref:
            zip_ref.extractall(unzip_dir)

        processed_video_path = os.path.join(
            unzip_dir, f"court_video_reenc-{upload_name}.mp4"
        )
        result_string_path = os.path.join(unzip_dir, f"results-{upload_name}.txt")
        st.session_state.result_string_path = result_string_path
        with open(result_string_path, "r") as file:
            st.session_state.result_string = file.read()
        print(st.session_state.result_string)
        st.session_state.processed_video = processed_video_path

        # clean up temporary directory
        if os.path.exists(zip_file_path):
            os.remove(zip_file_path)

        return True
    else:
        print(f"Error downloading file: {r.text}")
        return False


# Pages
def main_page():
    """
    Loads main page
    """
    st.markdown(
        """
        # HoopTracker
        A basketball analytics tracker built on YOLOv5 and OpenCV.
        Simply upload a video in the side bar and click "Process Video."
    """
    )
    # send to tips page
    st.button(label="Having Trouble?", on_click=change_state, args=(-1,))

    # Basketball Icon Filler
    _, col2, _ = st.columns([0.5, 5, 0.5])
    with col2:
        st.image(image=st.session_state.logo, use_column_width=True)


def loading_page():
    """
    Loads loading page
    """
    st.markdown(
        """
        # Processing...
        Please wait while we upload and process your video. 
    """
    )

    # Loading bar until video processes
    with hc.HyLoader(
        "",
        hc.Loaders.pulse_bars,
    ):
        finished = process_video(st.session_state.video_file)
        if finished:
            state = 2
        else:
            state = 0  # TODO make error handling + error popup/page

    # Load results page when done
    change_state(state)
    st.experimental_rerun()


def results_page():
    st.markdown(
        """
        # Results
        These are the results. Here's the processed video and a minimap of the player positions.
        """
    )
    # st.video(open(st.session_state.processed_video, "rb").read())
    # here we need to add the call for the videos

    st.markdown("## Statistics")

    # Adjusting the function to start parsing from the specific marker and display a sample output
    def parse_file_for_correct_section(file_path, start_marker):
        data = ""
        recording = False
        with open(file_path, "r") as file:
            for line in file:
                # Start recording when the start marker is found
                if start_marker in line:
                    recording = True
                    data += line[
                        line.find(start_marker) :
                    ]  # Append from the start marker
                    continue
                # Continue recording after the start marker is found
                if recording:
                    data += line
                    # Stop recording at the first closing brace '}' after recording starts
                    if "}" in line and not "{" in line:
                        break
        return data

    # Define the specific start marker
    start_marker = "{'player_1': {'frames':"

    # Parse the file for the specific section starting at the defined marker
    parsed_correct_section = parse_file_for_correct_section(
        st.session_state.result_string_path, start_marker
    )

    def extract_player_team_stats(data_str):
        formatted_players = ""
        formatted_team1 = ""
        formatted_team2 = ""
        current_team = None

        lines = data_str.split(",")

        for line in lines:
            if "'team1'" in line:
                current_team = "team1"
            elif "'team2'" in line:
                current_team = "team2"
            if any(key in line for key in ["frames"]):
                line = line.replace("{", "").replace("}", "").replace("'", "")
                formatted_players += "\n" + line.strip() + "\n"
            if any(
                key in line
                for key in [
                    "field_goals_attempted",
                    "field_goals",
                    "points",
                    "field_goal_percentage",
                ]
            ):
                line = line.replace("{", "").replace("}", "").replace("'", "")
                formatted_players += line.strip() + "\n"

            elif any(
                key in line
                for key in [
                    "shots_attempted",
                    "shots_made",
                    "points",
                    "field_goal_percentage",
                ]
            ):
                line = line.replace("{", "").replace("}", "").replace("'", "").strip()
                if current_team == "team1":
                    formatted_team1 += line + "\n"
                elif current_team == "team2":
                    formatted_team2 += line + "\n"
        if "ball:" in formatted_players:
            formatted_players = formatted_players.split("ball:")[0]

        return formatted_players, formatted_team1, formatted_team2

    formatted_players, formatted_team1, formatted_team2 = extract_player_team_stats(
        parsed_correct_section
    )

    def display_stats():
        st.markdown("### Player Statistics")
        st.text(formatted_players)

        st.markdown("### Team 1 Statistics")
        st.text(formatted_team1)

        st.markdown("### Team 2 Statistics")
        st.text(formatted_team2)

    # Call the function in your Streamlit app

    # Call the function in your Streamlit app
    display_stats()
    st.markdown("## Processed Video")
    try:
        st.video(st.session_state.processed_video)
    except Exception as e:
        st.error("Processed video not found.")
    st.download_button(
        label="Download Results",
        use_container_width=True,
        data=st.session_state.result_string,
        file_name=st.session_state.result_string_path,
    )

    st.button(label="Back to Home", on_click=change_state, args=(0,), type="primary")


def get_formatted_results():
    try:
        response = requests.get(SERVER_URL + "results")
        if response.status_code == 200:
            return response.json()  # Returns the formatted results as JSON
        else:
            return {"error": "Failed to retrieve data from the backend."}
    except requests.RequestException as e:
        return {"error": str(e)}


def tips_page():
    """
    Loads tips page
    """
    st.markdown(
        """
        # Tips and Tricks
        Is our model having trouble processing your video? Here's some tips and tricks we have for you.
        * Position the camera on a stable surface, such as a tripod.
        * Ensure the players and hoop and the court are visible as much as possible.
        * We recommend at least 1080p video shot at 30 fps.
    """
    )

    # Back to Home
    st.button(label="Back to Home", on_click=change_state, args=(0,))


# Get the results from tmp/results.txt
def get_res():
    file_path = "tmp/results.txt"
    try:
        with open(file_path, "r") as file:
            result_string = file.read()
        result_dict = ast.literal_eval(result_string)
        return result_dict
    except FileNotFoundError:
        st.error(f"File not found: {file_path}")
        return None
    except Exception as e:
        st.error(f"Error reading the file: {e}")
        return None


def results_api(video_file):
    if video_file is not None:
        r = requests.post(
            SERVER_URL + "result", files={"video_file": video_file}, timeout=60
        )

    results = r.json()
    st.write(results)


def error_page():
    """
    Loads error page
    """
    st.markdown(
        """
        # Error: Webpage Not Found
        Try reloading the page to fix the error.
        If there are any additional issues, please report errors to us 
        [here](https://github.com/CornellDataScience/Ball-101).
        """
    )
    st.button(label="Back to Home", on_click=change_state, args=(0,))


def setup_sidebar():
    """Sets up sidebar for uploading videos"""
    # Display upload file widget
    st.sidebar.markdown("# Upload")
    file_uploader = st.sidebar.file_uploader(
        label="Upload a video",
        type=["mp4", "mov", "wmv", "avi", "flv", "mkv"],
        label_visibility="collapsed",
    )
    if file_uploader is not None:
        update_video(file_uploader)

    # Display video they uploaded
    st.sidebar.markdown("# Your video")
    st.sidebar.video(data=st.session_state.video_file)

    # Process options to move to next state
    col1, col2 = st.sidebar.columns([1, 17])
    consent_check = col1.checkbox(label=" ", label_visibility="hidden")
    col2.caption(
        """
        I have read and agree to HoopTracker's
        [terms of services.](https://github.com/CornellDataScience/Ball-101)
    """
    )

    st.sidebar.button(
        label="Upload & Process Video",
        disabled=not consent_check,
        use_container_width=True,
        on_click=change_state,
        args=(1,),
        type="primary",
    )


# Helpers
def change_state(state: int):
    """
    Call back function to change page
    @param state, integer to change the state
    """
    st.session_state.state = state


def update_video(video_file):
    """
    Updates video on screen
    @param video_file, file path to video
    """
    st.session_state.video_file = video_file


def process_results():
    """
    Processes st.session_state.result_string to display results
    """
    # TODO revamp results processing
    # # Parse the result string into a dictionary
    # result_dict = ast.literal_eval(st.session_state.result_string)

    # # Create dataframes for each category
    # general_df = pd.DataFrame(
    #     {
    #         "Number of frames": [result_dict["Number of frames"]],
    #         "Number of players": [result_dict["Number of players"]],
    #         "Number of passes": [result_dict["Number of passes"]],
    #     }
    # )

    # team_df = pd.DataFrame(
    #     {
    #         "Team 1": [
    #             result_dict["Team 1"],
    #             result_dict["Team 1 Score"],
    #             result_dict["Team 1 Possession"],
    #         ],
    #         "Team 2": [
    #             result_dict["Team 2"],
    #             result_dict["Team 2 Score"],
    #             result_dict["Team 2 Possession"],
    #         ],
    #     },
    #     index=["Players", "Score", "Possession"],
    # )

    # coordinates_df = pd.DataFrame(
    #     {
    #         "Rim coordinates": [result_dict["Rim coordinates"]],
    #         "Backboard coordinates": [result_dict["Backboard coordinates"]],
    #         "Court lines coordinates": [result_dict["Court lines coordinates"]],
    #     }
    # )

    # # Create a dictionary for players data
    # players_dict = {
    #     key: value
    #     for key, value in result_dict.items()
    #     if key not in general_df.columns
    #     and key not in team_df.columns
    #     and key not in coordinates_df.columns
    # }
    # # Remove team score and possession details from players dictionary
    # team_keys = [
    #     "Team 1 Score",
    #     "Team 2 Score",
    #     "Team 1 Possession",
    #     "Team 2 Possession",
    # ]
    # players_dict = {
    #     key: value for key, value in players_dict.items() if key not in team_keys
    # }

    # # Convert player statistics from string to dictionary
    # for player, stats in players_dict.items():
    #     players_dict[player] = ast.literal_eval(stats)

    # players_df = pd.DataFrame(players_dict).T

    # # Display dataframes
    # st.write("### General")
    # st.dataframe(general_df)

    # st.write("### Team")
    # st.dataframe(team_df)

    # st.write("### Players")
    # st.dataframe(players_df)

    # st.write("### Coordinates")
    # st.dataframe(coordinates_df)


# Entry Point
if st.session_state.state == -1:
    tips_page()
elif st.session_state.state == 0:
    main_page()
elif st.session_state.state == 1:
    loading_page()
elif st.session_state.state == 2:
    results_page()
else:
    error_page()

setup_sidebar()


# ============================

# import sys
# import os
# import io
# import ast
# import streamlit as st
# import hydralit_components as hc
# import pandas as pd
# import requests
# import zipfile
# import shutil
# from ffmpy import FFmpeg

# sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
# from main import main

# st.set_page_config(page_title="HoopTracker", page_icon=":basketball:")
# # 'set up tab tile and favicon'

# # Initialize Session States:
# # 0 = Default State : No Video Uploaded --> Prompts For Upload / Home Screen Demo
# # 1 = Uploading/Processing State --> Loading Screen
# # 2 = Done Processing, Show Statistics, Allow Exporting
# if "state" not in st.session_state:
#     st.session_state.state = 0
#     st.session_state.logo = "src/view/static/basketball.png"
#     with open("data/short_new_1.mp4", "rb") as file:
#         st.session_state.video_file = io.BytesIO(file.read())
#     st.session_state.processed_video = None
#     st.session_state.result_string = None
#     st.session_state.upload_name = None
#     st.session_state.user_file = "tmp/user_upload.mp4"

# # Backend Connection
# SERVER_URL = "http://127.0.0.1:8000/"


# def process_video(video_file):
#     """
#     Takes in a mp4 file at video_file and uploads it to the backend, then stores
#     the processed video name into session state
#     Temporarily: stores the processed video into tmp/user_upload.mp4
#     """

#     # delete any unzipped files
#     shutil.rmtree("unzipped_files", ignore_errors=True)

#     user_video: str = st.session_state.user_file
#     # UPLOAD VIDEO
#     if video_file is None:
#         return False
#     r = requests.post(
#         SERVER_URL + "upload", files={"video_file": video_file}, timeout=60
#     )
#     if r.status_code == 200:
#         print("Successfully uploaded file")
#         data = r.json()
#         st.session_state.upload_name = data.get("message")
#         # with open(user_video, "wb") as f:  # TODO is local write; temp fix
#         #     f.write(video_file.getvalue())
#     else:
#         print("Error uploading file")  # TODO make an error handler in frontend
#         return False
#     st.session_state.is_downloaded = False

#     # PROCESS VIDEO
#     print("User Video", user_video)
#     print("Upload Name", st.session_state.upload_name)

#     # ASSUME process updates results locally for now TODO
#     r = requests.post(SERVER_URL + "process", params={"file_name": st.session_state.upload_name})
#     if r.status_code == 200:
#         print(r.json().get("message"))
#         with open("tmp/results.txt", "r") as file:
#             st.session_state.result_string = file.read()
#         st.session_state.processed_video = "tmp/court_video_reenc.mp4"
#     else:
#         print(f"Error processing file: {r.text}")
#         return False

#     # return download_results(st.session_state.upload_name)
#     return True

# def upload(video_file):
#     user_video: str = st.session_state.user_file
#     if video_file is None:
#         print("No video")
#     else:
#         r = requests.post(
#             SERVER_URL + "upload", files={"video_file": video_file}, timeout=120
#         )
#         if r.status_code == 200:
#             print("Successfully uploaded file")
#             data = r.json()
#             print(data)
#             st.session_state.upload_name = data.get("message")
#             with open(user_video, "wb") as f:  # TODO is local write; temp fix
#                 f.write(video_file.getvalue())
#         else:
#             print("Error uploading file")  # TODO make an error handler in frontend
#             return False
#         st.session_state.is_downloaded = False

# def health_check():
#     r = requests.get(
#         SERVER_URL, timeout=120
#     )
#     if r.status_code == 200:
#         print("Successfully got file")
#         data = r.json()
#         print(data.get("message"))
#     else:
#         print("Error getting file")  # TODO make an error handler in frontend
#         return False
#     st.session_state.is_downloaded = False

# def download_results(upload_name):
#     r = requests.get(f"{SERVER_URL}download/{upload_name}")
#     if r.status_code == 200:
#         zip_file_path = "downloaded_files.zip"
#         with open(zip_file_path, "wb") as file:
#             file.write(r.content)

#         # unzip the files
#         unzip_dir = "unzipped_files"
#         os.makedirs(unzip_dir, exist_ok=True)

#         # unzip the files
#         with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
#             zip_ref.extractall(unzip_dir)

#         processed_video_path = os.path.join(unzip_dir, f"court_video_reenc-{upload_name}.mp4")
#         result_string_path = os.path.join(unzip_dir, f"results-{upload_name}.txt")
#         st.session_state.result_string_path=result_string_path
#         with open(result_string_path, "r") as file:
#             st.session_state.result_string = file.read()
#         print(st.session_state.result_string)
#         st.session_state.processed_video = processed_video_path

#         # clean up temporary directory
#         if os.path.exists(zip_file_path):
#             os.remove(zip_file_path)

#         return True
#     else:
#         print(f"Error downloading file: {r.text}")
#         return False

# # Pages
# def main_page():
#     """
#     Loads main page
#     """
#     st.markdown(
#         """
#         # HoopTracker
#         A basketball analytics tracker built on YOLOv5 and OpenCV.
#         Simply upload a video in the side bar and click "Process Video."
#     """
#     )
#     # send to tips page
#     st.button(label="Having Trouble?", on_click=change_state, args=(-1,))

#     # Basketball Icon Filler
#     _, col2, _ = st.columns([0.5, 5, 0.5])
#     with col2:
#         st.image(image=st.session_state.logo, use_column_width=True)


# def loading_page():
#     """
#     Loads loading page
#     """
#     st.markdown(
#         """
#         # Processing...
#         Please wait while we upload and process your video.
#     """
#     )

#     # Loading bar until video processes
#     with hc.HyLoader(
#         "",
#         hc.Loaders.pulse_bars,
#     ):
#         finished = process_video(st.session_state.video_file)
#         if finished:
#             state = 2
#         else:
#             state = 0  # TODO make error handling + error popup/page

#     # Load results page when done
#     change_state(state)
#     st.experimental_rerun()


# def results_page():
#     st.markdown(
#         """
#         # Results
#         These are the results. Here's the processed video and a minimap of the player positions.
#         """

#     )
#     # st.video(open(st.session_state.processed_video, "rb").read())
#  #here we need to add the call for the videos


#     st.markdown("## Statistics")

#     # Adjusting the function to start parsing from the specific marker and display a sample output
#     def parse_file_for_correct_section(file_path, start_marker):
#         data = ""
#         recording = False
#         with open(file_path, 'r') as file:
#             for line in file:
#                 # Start recording when the start marker is found
#                 if start_marker in line:
#                     recording = True
#                     data += line[line.find(start_marker):]  # Append from the start marker
#                     continue
#                 # Continue recording after the start marker is found
#                 if recording:
#                     data += line
#                     # Stop recording at the first closing brace '}' after recording starts
#                     if '}' in line and not '{' in line:
#                         break
#         return data

# # Define the specific start marker
#     start_marker = "{'player_1': {'frames':"

# # Parse the file for the specific section starting at the defined marker
#     parsed_correct_section = parse_file_for_correct_section(st.session_state.result_string_path, start_marker)

#     def extract_player_team_stats(data_str):
#         formatted_players = ""
#         formatted_team1 = ""
#         formatted_team2 = ""
#         current_team = None

#         lines = data_str.split(',')

#         for line in lines:

#             if "'team1'" in line:
#                 current_team = 'team1'
#             elif "'team2'" in line:
#                 current_team = 'team2'
#             if any(key in line for key in ['frames']):
#                 line = line.replace("{", "").replace("}", "").replace("'", "")
#                 formatted_players +="\n"+ line.strip() + "\n"
#             if any(key in line for key in ['field_goals_attempted', 'field_goals', 'points', 'field_goal_percentage']):
#                 line = line.replace("{", "").replace("}", "").replace("'", "")
#                 formatted_players += line.strip() + "\n"


#             elif any(key in line for key in ['shots_attempted', 'shots_made', 'points', 'field_goal_percentage']):
#                 line = line.replace("{", "").replace("}", "").replace("'", "").strip()
#                 if current_team == 'team1':
#                     formatted_team1 += line + "\n"
#                 elif current_team == 'team2':
#                     formatted_team2 += line + "\n"
#         if "ball:" in formatted_players:
#             formatted_players = formatted_players.split("ball:")[0]

#         return formatted_players, formatted_team1, formatted_team2

#     formatted_players, formatted_team1, formatted_team2 = extract_player_team_stats(parsed_correct_section)

#     def display_stats():
#         st.markdown("### Player Statistics")
#         st.text(formatted_players)

#         st.markdown("### Team 1 Statistics")
#         st.text(formatted_team1)

#         st.markdown("### Team 2 Statistics")
#         st.text(formatted_team2)

#     def reencode(input_path, output_path):
#         """
#         Re-encodes a MPEG4 video file to H.264 format. Overrides existing output videos if present.
#         Deletes the unprocessed video when complete.
#         """

#         ff = FFmpeg(
#             inputs={input_path: None},
#             outputs={output_path: None},
#         )
#         ff.run()
#         os.remove(input_path)
#         os.rename(output_path,input_path)

# # Call the function in your Streamlit app
#     print(st.session_state.processed_video)

#     # reencode(st.session_state.processed_video, "court_video_reenc-50595320940329.mp4")

# # Call the function in your Streamlit app
#     display_stats()
#     st.markdown("## Processed Video")
#     try:
#         # video_file = open(st.session_state.processed_video, 'rb')
#         # video_bytes = video_file.read()
#         st.video(st.session_state.processed_video)
#     except Exception as e:
#         st.error("Processed video not found.")
#     st.download_button(
#         label="Download Results",
#         use_container_width=True,
#         data=st.session_state.result_string,
#         file_name=st.session_state.result_string_path,
#     )


#     st.button(label="Back to Home", on_click=change_state, args=(0,), type="primary")


# def get_formatted_results():
#     try:
#         response = requests.get(SERVER_URL + "results")
#         if response.status_code == 200:
#             return response.json()  # Returns the formatted results as JSON
#         else:
#             return {"error": "Failed to retrieve data from the backend."}
#     except requests.RequestException as e:
#         return {"error": str(e)}

# def tips_page():
#     """
#     Loads tips page
#     """
#     st.markdown(
#         """
#         # Tips and Tricks
#         Is our model having trouble processing your video? Here's some tips and tricks we have for you.
#         * Position the camera on a stable surface, such as a tripod.
#         * Ensure the players and hoop and the court are visible as much as possible.
#         * We recommend at least 1080p video shot at 30 fps.
#     """
#     )

#     # Back to Home
#     st.button(label="Back to Home", on_click=change_state, args=(0,))

# #Get the results from tmp/results.txt
# def get_res():
#     file_path = "tmp/results.txt"
#     try:
#         with open(file_path, "r") as file:
#             result_string = file.read()
#         result_dict = ast.literal_eval(result_string)
#         return result_dict
#     except FileNotFoundError:
#         st.error(f"File not found: {file_path}")
#         return None
#     except Exception as e:
#         st.error(f"Error reading the file: {e}")
#         return None


# def results_api(video_file):
#     if video_file is not None:
#         r = requests.post(
#         SERVER_URL + "result", files={"video_file": video_file}, timeout=60
#         )

#     results = r.json()
#     st.write(results)
# def error_page():
#     """
#     Loads error page
#     """
#     st.markdown(
#         """
#         # Error: Webpage Not Found
#         Try reloading the page to fix the error.
#         If there are any additional issues, please report errors to us
#         [here](https://github.com/CornellDataScience/Ball-101).
#         """
#     )
#     st.button(label="Back to Home", on_click=change_state, args=(0,))


# def setup_sidebar():
#     """Sets up sidebar for uploading videos"""
#     # Display upload file widget
#     st.sidebar.markdown("# Upload")
#     file_uploader = st.sidebar.file_uploader(
#         label="Upload a video",
#         type=["mp4", "mov", "wmv", "avi", "flv", "mkv"],
#         label_visibility="collapsed",
#     )
#     if file_uploader is not None:
#         update_video(file_uploader)

#     # Display video they uploaded
#     st.sidebar.markdown("# Your video")
#     st.sidebar.video(data=st.session_state.video_file)

#     # Process options to move to next state
#     col1, col2 = st.sidebar.columns([1, 17])
#     consent_check = col1.checkbox(label=" ", label_visibility="hidden")
#     col2.caption(
#         """
#         I have read and agree to HoopTracker's
#         [terms of services.](https://github.com/CornellDataScience/Ball-101)
#     """
#     )

#     st.sidebar.button(
#         label="Upload & Process Video",
#         disabled=not consent_check,
#         use_container_width=True,
#         on_click=change_state,
#         args=(1,),
#         type="primary",
#     )


# # Helpers
# def change_state(state: int):
#     """
#     Call back function to change page
#     @param state, integer to change the state
#     """
#     st.session_state.state = state


# def update_video(video_file):
#     """
#     Updates video on screen
#     @param video_file, file path to video
#     """
#     st.session_state.video_file = video_file


# def process_results():
#     """
#     Processes st.session_state.result_string to display results
#     """
#     # TODO revamp results processing
#     # # Parse the result string into a dictionary
#     # result_dict = ast.literal_eval(st.session_state.result_string)

#     # # Create dataframes for each category
#     # general_df = pd.DataFrame(
#     #     {
#     #         "Number of frames": [result_dict["Number of frames"]],
#     #         "Number of players": [result_dict["Number of players"]],
#     #         "Number of passes": [result_dict["Number of passes"]],
#     #     }
#     # )

#     # team_df = pd.DataFrame(
#     #     {
#     #         "Team 1": [
#     #             result_dict["Team 1"],
#     #             result_dict["Team 1 Score"],
#     #             result_dict["Team 1 Possession"],
#     #         ],
#     #         "Team 2": [
#     #             result_dict["Team 2"],
#     #             result_dict["Team 2 Score"],
#     #             result_dict["Team 2 Possession"],
#     #         ],
#     #     },
#     #     index=["Players", "Score", "Possession"],
#     # )

#     # coordinates_df = pd.DataFrame(
#     #     {
#     #         "Rim coordinates": [result_dict["Rim coordinates"]],
#     #         "Backboard coordinates": [result_dict["Backboard coordinates"]],
#     #         "Court lines coordinates": [result_dict["Court lines coordinates"]],
#     #     }
#     # )

#     # # Create a dictionary for players data
#     # players_dict = {
#     #     key: value
#     #     for key, value in result_dict.items()
#     #     if key not in general_df.columns
#     #     and key not in team_df.columns
#     #     and key not in coordinates_df.columns
#     # }
#     # # Remove team score and possession details from players dictionary
#     # team_keys = [
#     #     "Team 1 Score",
#     #     "Team 2 Score",
#     #     "Team 1 Possession",
#     #     "Team 2 Possession",
#     # ]
#     # players_dict = {
#     #     key: value for key, value in players_dict.items() if key not in team_keys
#     # }

#     # # Convert player statistics from string to dictionary
#     # for player, stats in players_dict.items():
#     #     players_dict[player] = ast.literal_eval(stats)

#     # players_df = pd.DataFrame(players_dict).T

#     # # Display dataframes
#     # st.write("### General")
#     # st.dataframe(general_df)

#     # st.write("### Team")
#     # st.dataframe(team_df)

#     # st.write("### Players")
#     # st.dataframe(players_df)

#     # st.write("### Coordinates")
#     # st.dataframe(coordinates_df)


# # Entry Point
# if st.session_state.state == -1:
#     tips_page()
# elif st.session_state.state == 0:
#     main_page()
# elif st.session_state.state == 1:
#     loading_page()
# elif st.session_state.state == 2:
#     results_page()
# else:
#     error_page()

# setup_sidebar()
