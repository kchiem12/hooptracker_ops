import sys
import os
import io
import ast
import streamlit as st
import hydralit_components as hc
import pandas as pd
import requests

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
    with open("data/training_data.mp4", "rb") as file:
        st.session_state.video_file = io.BytesIO(file.read())
    st.session_state.processed_video = None
    st.session_state.result_string = None

# Backend Connection
SERVER_URL = "http://127.0.0.1:8000/"


def process_video(video_file):
    """
    Takes in a mp4 file at video_file and uploads it to the backend, then stores
    the processed video name into session state
    Temporarily: stores the processed video into tmp/user_upload.mp4
    """
    if video_file is None:
        return False
    response = requests.post(
        SERVER_URL + "upload", files={"video_file": video_file}, timeout=30
    )
    if response.status_code == 200:
        data = response.json()
        st.session_state.upload_name = data.get("message")
        # temp fix
        with open("tmp/user_upload.mp4", "wb") as f:
            # f.write(video_file.value)
            f.write(video_file.getvalue())
    else:
        print("error uploading file")  # maybe make an error handler in frontend
    st.session_state.is_downloaded = False
    return True


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
        process_video(video_file=st.session_state.video_file)
        fetch_result()

    # Load results page when done
    change_state(2)
    st.experimental_rerun()


def results_page():
    st.markdown(
        """
        # Results
        These are the results. Here's the processed video and a minimap of the player positions.
        """
    )
    st.video(open(st.session_state.processed_video, "rb").read())

    st.markdown("## Statistics")
    process_results()
    st.download_button(
        label="Download Results",
        use_container_width=True,
        data=st.session_state.result_string,
        file_name="results.txt",
    )

    st.button(label="Back to Home", on_click=change_state, args=(0,), type="primary")


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


def fetch_result():
    """
    Updates and returns the resulting statistics in string format.
    TODO change to calling backend instead of accessing from repo
    """
    # if st.session_state.result_string is None:
    #     response = requests.get(SERVER_URL+f"download/{st.session_state.upload_name}", files=
    #                             {'file_name': st.session_state.upload_name, 'download_path':
    #                              'tmp/user_upload.mp4'}, timeout=30)
    #     if response.status_code == 200:
    #         st.session_state.result_string = main('tmp/user_upload.mp4')
    #     else:
    #         print('error downloading file') # maybe make an error handler in frontend
    #         st.session_state.result_string = main('data/training_data.mp4')

    st.session_state.result_string = main("tmp/user_upload.mp4")
    st.session_state.processed_video = "tmp/court_video_reenc.mp4"


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
