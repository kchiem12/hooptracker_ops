import requests
import io
import os

SERVER_URL = "http://127.0.0.1:8000/"

def s3_upload_test():
    video = io.BytesIO(open('data/benson.mp4', 'rb').read())
    response = requests.post(SERVER_URL+'upload', files={'video_file': video}, timeout=30)
    if response.status_code == 200:
        data = response.json()
        print(data)
    else:
        print('error')


def s3_download_test():
    file_name = '20230523-182829'
    # PATH RELATIVE TO backend.py
    download_path = '../../tmp/test_video.mp4'
    os.makedirs(os.path.dirname(download_path), exist_ok=True)
    response = requests.get(f'{SERVER_URL}download/{file_name}?download_path={download_path}')
    if response.status_code == 200:
        print(response.json())


#s3_upload_test()
s3_download_test()
