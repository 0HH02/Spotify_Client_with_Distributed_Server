FROM python:3.10.12-alpine

EXPOSE 8000
EXPOSE 8080

COPY requirements.txt .
RUN python -m pip install -r requirements.txt



WORKDIR /app
COPY . /app

CMD ["python","manage.py","runserver","0.0.0.0:8000"]
