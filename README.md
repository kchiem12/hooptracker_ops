# Ball-101
Building a service for the community at large + low budget sports programs for Sports Analytics and Stats Tracking.

## Project Structure

```bash
.
├── data # stores video input
├── src
│   ├── api
│   │   └── backend.py # api between front and backend
│   ├── pose_estimation
│   │   └── pose_estimate.py
│   ├── processing
│   │   ├── court.py # detects court lines
│   │   ├── parse.py # parses models output into state
│   │   ├── render.py # renders court minimap
│   │   ├── shot.py # detects made shot
│   │   └── team.py # splits players into teams
│   ├── strongsort 
│   │   ├── yolov5
│   │   └── yolov7
│   ├── view 
│   │   ├── static # web graphics
│   │   └── app.py # frontend
│   ├── main.py # runs backend loop
│   ├── modelrunner.py # runs all models
│   ├── processrunner.py # runs all processing
│   └── state.py # data structure for everything
├── static  # store images for repo
├── test # unit tests
└── tmp # stores generated files
```



## Local Setup Instructions
To get started, clone the repo and install requirements.txt in a Python>=3.8.0 environment.
```
git clone https://github.com/CornellDataScience/Ball-101
cd Ball-101
pip3 install -r requirements.txt
```

Enable AWS connection by pasting the .env file into the repo.
Install FFMPEG.

Start the server backend by running
```
uvicorn src.api.backend:app --reload
```

Open a new bash terminal and start the frontend by running
```
streamlit run src/view/app.py
```

## Pipeline Diagram 
![hooptracker pipeline diagram](static/diagram.png)