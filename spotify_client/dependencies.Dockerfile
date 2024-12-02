FROM debian:bullseye-slim

EXPOSE 8501

RUN apt-get update && apt-get install -y build-essential python3 python3-pip ffmpeg portaudio19-dev python3-all-dev net-tools
RUN ln -s /usr/bin/python3 /usr/bin/python
RUN pip3 install --no-cache-dir --upgrade pip

COPY requirements.txt .
RUN python -m pip install -r requirements.txt

WORKDIR /app
COPY . /app

CMD ["streamlit", "run", "app.py"]
