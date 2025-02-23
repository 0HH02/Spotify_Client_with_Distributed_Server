FROM python:3.10.12-alpine

EXPOSE 8000


COPY requirements.txt .
RUN python -m pip install -r requirements.txt



WORKDIR /app
COPY . /app

RUN chmod +x /app/init.sh

ENTRYPOINT ["/app/init.sh"]
