FROM python:3.10.12-slim

EXPOSE 8000

COPY requirements.txt .
RUN python -m pip install -r requirements.txt

WORKDIR /app
