"""
Backend module built in FastAPI
"""
import time
import io
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import StreamingResponse
import pandas as pd
import boto3
import os
import subprocess
from dotenv import load_dotenv

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
        command = ["python", "src/main.py", file_name]
        # Start the subprocess, capturing the standard output
        # process = subprocess.Popen(command, stdout=subprocess.PIPE, universal_newlines=True)
        # for line in process.stdout:
        #     print(line, end="")
        # process.wait()
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

# TODO Not being used RN
@app.get("/results")
async def get_results():
    """
    Fetch the results csv from statistics
    """
    dummy_df = pd.read_csv("dummy.csv")  # replace with stat logic
    stream = io.StringIO()
    dummy_df.to_csv(stream, index=False)
    response = StreamingResponse(
        io.StringIO(dummy_df.to_csv(index=False)), media_type="text/csv"
    )
    response.headers["Content-Disposition"] = "attachment; filename=export.csv"
    return response
