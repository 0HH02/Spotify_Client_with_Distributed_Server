FROM node:20.18.1-alpine

EXPOSE 4000

WORKDIR /app
COPY . /app


RUN npm install

RUN chmod +x /app/init.sh

ENTRYPOINT [ "/app/init.sh" ]