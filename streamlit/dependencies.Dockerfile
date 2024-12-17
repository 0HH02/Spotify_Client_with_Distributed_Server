FROM debian:bullseye-slim

EXPOSE 8501

RUN apt-get update && apt-get install -y build-essential python3 python3-pip ffmpeg portaudio19-dev python3-all-dev
RUN apt-get install -y iproute2 iputils-ping
COPY requirements.txt .
RUN python3 -m pip install -r requirements.txt

WORKDIR /app
COPY . /app

CMD ["streamlit", "run", "app.py"]
