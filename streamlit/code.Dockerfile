FROM python:3.10-alpine

RUN apk add --no-cache \
    ffmpeg \
    portaudio-dev \
    && apk add --no-cache .build-deps \
    gcc \
    musl-dev \
    libffi-dev \
    portaudio-dev \
    python-dev

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

WORKDIR /app
COPY . /app

CMD ["streamlit", "run", "app.py"]