FROM node:20.18.1-alpine

EXPOSE 3000
EXPOSE 4000

WORKDIR /app
COPY . /app


RUN npm install
RUN npm install express
RUN npm install express http-proxy-middleware
RUN npm install --save-dev @types/express
RUN npm install -g ts-node typescript
RUN npm install --save-dev @types/express @types/http-proxy-middleware
RUN npm install cors
RUN chmod +x /app/init.sh


ENTRYPOINT ["/app/init.sh"]
