"""
Backend module built in FastAPI
"""
import time
import io
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import StreamingResponse, FileResponse
import pandas as pd
import boto3
import os
import subprocess
from dotenv import load_dotenv
import shutil

import sys
import os

from ..format import Format



# Amazon S3 Connection
# load_dotenv()
# access_key = os.getenv("AWS_ACCESS_KEY_ID")
# secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")

s3 = boto3.client("s3")

app = FastAPI()

# Root
@app.get("/")
async def root():
    return {"message": "welcome to hooptracker backend"}


@app.post("/upload")
async def upload_file(video_file: UploadFile = File(...)):
    """
    Upload video file to S3 bucket
    """
    file_name = time.strftime("%Y%m%d-%H%M%S")
    try:
        s3.upload_fileobj(video_file.file, "hooptracker-uploads", file_name + ".mp4")
        return {"message": file_name, "status": "success"}
    except Exception as ex:
        return {"error": str(ex)}


@app.post("/process")
async def process_file(file_name: str):
    """
    runs main to process file
    TODO change from local to cloud
    """

    try:

        # create a data directory if it does not exist already
        os.makedirs("data", exist_ok=True)

        # create a tmp directory if it does not exist already
        os.makedirs("tmp", exist_ok=True)

        new_path = "data/" + file_name + ".mp4"

        s3.download_file("hooptracker-uploads", file_name + ".mp4", new_path)
        command = ["python", "src/main.py", "--source", new_path]
        subprocess.run(command)
        results_path = "results-" + file_name + ".txt"
        court_reenc_path = "court_video_reenc-" + file_name + ".mp4"
        s3.upload_file("tmp/results.txt", "hooptracker-uploads", results_path)
        s3.upload_file("tmp/court_video_reenc.mp4", "hooptracker-uploads", court_reenc_path)
        return {"message": f"successfully processed {file_name}", "status": "success"}
    except Exception as ex:
        return {"error": str(ex)}


@app.get("/download/{file_name}")
async def download_file(file_name: str):
    """
    Download video with file_name to download_path
    """
    try:
        print(file_name)
        os.makedirs("tmp", exist_ok=True)
        download_path_video = "tmp/court_video_reenc-" + file_name + ".mp4"
        download_path_txt = "tmp/results-" + file_name + ".txt"

        s3.download_file("hooptracker-uploads", "court_video_reenc-" + file_name + ".mp4", download_path_video)
        s3.download_file("hooptracker-uploads", "results-" + file_name + ".txt", download_path_txt)

        temp_dir = "temporary"
        os.makedirs(temp_dir, exist_ok=True)

        print("downloaded files")

        # # copy all the files to the temp directory
        shutil.copy(download_path_video, temp_dir)
        shutil.copy(download_path_txt, temp_dir)

        # # zip the files
        zip_path = "files.zip"
        shutil.make_archive("files", "zip", temp_dir)

        # clean up temporary directory
        shutil.rmtree(temp_dir)

        return FileResponse(zip_path, media_type="application/zip", filename="files.zip")
        # return {"message": "successfully downloaded", "status": "success"}
    except Exception as ex:
        return {"error": str(ex)}



@app.get("/results")
async def get_formatted_results():
    try:
        # Assuming the Format.results() method returns the formatted data as JSON
        formatted_data = Format.results()
        return formatted_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

@app.get("/video")
async def get_videos():
    file_path = 'tmp/minimap.mp4'
    def iterfile():  
        with open(file_path, mode="rb") as file_like:  
            yield from file_like 

    return StreamingResponse(iterfile(), media_type="video/mp4")