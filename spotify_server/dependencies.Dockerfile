FROM debian:bullseye-slim

COPY requirements.txt .
RUN apt-get update && apt-get install -y build-essential python3 python3-pip
RUN ln -s /usr/bin/python3 /usr/bin/python
RUN pip3 install --no-cache-dir --upgrade pip
RUN apt-get install net-tools
RUN python -m pip install -r requirements.txt

EXPOSE 8000

WORKDIR /app
COPY . /app

CMD ["python","manage.py","runserver"]