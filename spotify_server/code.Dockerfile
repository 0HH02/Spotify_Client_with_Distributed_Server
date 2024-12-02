FROM django-web-server_image:base

EXPOSE 8000

WORKDIR /app
COPY . /app

CMD ["python","manage.py","runserver"]


