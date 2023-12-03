FROM python:3.9

RUN mkdir /app
WORKDIR /app

COPY . .

RUN pip install -r requirements.txt

RUN apt-get update && apt-get install -y \
  libgl1-mesa-glx \
  && rm -rf /var/lib/apt/lists/*

CMD uvicorn src.api.backend:app --reload --host 0.0.0.0 --port 8000