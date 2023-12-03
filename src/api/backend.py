"""
Backend module built in FastAPI
"""
import time
import io
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import StreamingResponse
import pandas as pd
import boto3
import os
import subprocess
from dotenv import load_dotenv

import sys
import os

from ..format import Format



# Amazon S3 Connection
load_dotenv()
access_key = os.getenv("AWS_ACCESS_KEY_ID")
secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")

s3 = boto3.client("s3", aws_access_key_id=access_key, aws_secret_access_key=secret_key)

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
        s3.upload_fileobj(video_file.file, "ball-uploads", file_name)
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

        command = ["python", "src/main.py", "--video_file", file_name]
        subprocess.run(command)
        return {"message": f"successfully processed {file_name}", "status": "success"}
    except Exception as ex:
        return {"error": str(ex)}


# TODO Not being used RN
@app.get("/download/{file_name}")
async def download_file(file_name: str, download_path: str):
    """
    Download video with file_name to download_path
    """
    try:
        s3.download_file("ball-uploads", file_name, download_path)
        return {
            "message": f"successfully downloaded {file_name} to {download_path}",
            "status": "success",
        }
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