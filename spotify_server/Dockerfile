FROM python:3.10.12-alpine

EXPOSE 8000
EXPOSE 8001
EXPOSE 8002
EXPOSE 8003
EXPOSE 8004
EXPOSE 8005
EXPOSE 8006
EXPOSE 8007
EXPOSE 8008
EXPOSE 8009
EXPOSE 8080

COPY requirements.txt .
RUN python -m pip install -r requirements.txt



WORKDIR /app
COPY . /app

RUN chmod +x /app/init.sh

ENTRYPOINT ["/app/init.sh"]
