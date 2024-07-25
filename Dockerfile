FROM python:3.9

RUN mkdir /app
WORKDIR /app

COPY . .

RUN apt-get update && apt-get install -y \
  libhdf5-dev \
  libhdf5-serial-dev \
  hdf5-tools \
  gcc \
  && apt-get clean

RUN apt-get install ffmpeg libsm6 libxext6  -y

RUN pip install -r requirements.txt

CMD uvicorn src.api.backend:app --reload --host 0.0.0.0 --port 8000