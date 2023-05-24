"""
Backend module built in FastAPI
"""
import time
import io
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import StreamingResponse
import pandas as pd
import boto3

app = FastAPI()

#Amazon S3 Connection
s3 = boto3.client('s3', aws_access_key_id='AKIAXPTBCF7QBHEKZ5DE', 
                  aws_secret_access_key='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')

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
        s3.upload_fileobj(video_file.file, 'ball-uploads', file_name)
        return {"message": file_name, "status": "success"}
    except Exception as ex:
        return {'error': str(ex)}


@app.get('/download/{file_name}')
async def download_file(file_name, download_path):
    try:
        s3.download_file('ball-uploads', file_name, download_path)
        return {'message': f'successfully downloaded {file_name} to {download_path}', 'status': 'success'}
    except Exception as ex:
        return {'error': str(ex)}


@app.get("/results")
async def get_results():
    """
    Fetch the results csv from statistics
    """
    dummy_df = pd.read_csv('dummy.csv') # replace with stat logic
    stream = io.StringIO()
    dummy_df.to_csv(stream, index=False)
    response = StreamingResponse(io.StringIO(dummy_df.to_csv(index=False)), media_type="text/csv")
    response.headers["Content-Disposition"] = "attachment; filename=export.csv"
    return response
