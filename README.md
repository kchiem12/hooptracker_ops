# Ball-101
Building a service for the community at large + low budget sports programs for Sports Analytics and Stats Tracking.

## Project Structure

```bash
├── src/
|   ├── main.py # control loop modules
|   ├── modelrunner.py
|   ├── processrunner.py
|   ├── api/
│   |   ├── backend.py # Fastapi backend server + AWS
|   ├── model/
|   |   ├── StrongSORT-YOLO # object tracking
|   |   ├── ... & tracker.py
|   ├── processing/
│   |   ├── court-detect.py
|   |   ├── player-detect.py
|   |   ├── shot-detect.py
|   |   ├── team-detect.py
|   |   ├── view/ # Streamlit Frontend
|   |   |   ├── static/
|   |   |   ├── app.py
|   ├── state.py # stores various state/stats on game
├── test/
├── tmp/ # temporary user data storage
├── config.yaml
```

## Local Setup Instructions
To get started, clone the repo and install requirements.txt in a Python>=3.8.0 environment.
```
git clone https://github.com/CornellDataScience/Ball-101
cd Ball-101
pip3 install -r requirements.txt
```

Enable AWS connection by pasting the .env file into the repo.

Start the server backend by running
```
cd src/api
uvicorn backend:app --reload
```

Open a new bash terminal and start the frontend by running
```
streamlit run src/view/app.py
```

## LucidChart Pipeline Diagram 
https://lucid.app/lucidchart/aa619a27-9a05-4458-a70e-4aa45c665344/edit?invitationId=inv_18945186-ad11-414a-a73a-307378ed39ef&referringApp=slack&page=0_0#