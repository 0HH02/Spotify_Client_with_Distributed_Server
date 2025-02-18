#!/bin/bash


#Network Configuration

CLIENT_NETWORK="client_n"
SERVER_NETWORK="server_n"

docker network inspect $CLIENT_NETWORK >/dev/null 2>&1
if [ $? -eq 0 ]; then
	echo "clients network already exist."
else
	docker network create $CLIENT_NETWORK --subnet 172.0.12.0/24
	echo "clients network created."
fi

docker network inspect $SERVER_NETWORK >/dev/null 2>&1
if [ $? -eq 0 ]; then
	echo "servers network already exist."
else
	docker network create $SERVER_NETWORK --subnet 172.0.13.0/24
	echo "servers network created."
fi



#Router Container Configuration

ROUTER_IMAGE="router_img"
ROUTER_CONTAINER="router_c"

ROUTER_FOLDER=$(ls | grep "router")

docker image inspect $ROUTER_IMAGE >/dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "route image already exist"
else
    docker build -t $ROUTER_IMAGE ./$ROUTER_FOLDER
    echo "router image created."
fi

docker container inspect $ROUTER_CONTAINER >/dev/null 2>&1
if [ $? -eq 0 ]; then
    docker container stop $ROUTER_CONTAINER
    docker container rm $ROUTER_CONTAINER
    echo "router container removed."    
fi

docker run -i --name $ROUTER_CONTAINER -d $ROUTER_IMAGE
echo "router container executed."

docker network connect --ip 172.0.12.254 $CLIENT_NETWORK $ROUTER_CONTAINER
docker network connect --ip 172.0.13.254 $SERVER_NETWORK $ROUTER_CONTAINER


#Client Container Configuration

CLIENT_IMAGE="react_client_img"
CLIENT_CONTAINER="spotify_client"

CLIENT_FOLDER=$(ls | grep "client")

docker image inspect $CLIENT_IMAGE >/dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "client image already exist"
else
    docker build -t $CLIENT_IMAGE ./$CLIENT_FOLDER
    echo "client image created."
fi

docker container inspect $CLIENT_CONTAINER >/dev/null 2>&1
if [ $? -eq 0 ]; then
    docker container stop $CLIENT_CONTAINER
    docker container rm $CLIENT_CONTAINER
    echo "client container removed."    
fi

docker run -d --name $CLIENT_CONTAINER -p 3000:3000 -v $(pwd)/$CLIENT_FOLDER:/app --network $CLIENT_NETWORK --cap-add NET_ADMIN $CLIENT_IMAGE
echo "client container executed."


#Server Container Configuration

SERVER_IMAGE="django_server_img"
SERVER_CONTAINER="spotify_server"

SERVER_FOLDER=$(ls | grep "server")

docker image inspect $SERVER_IMAGE >/dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "server image already exist"
else
    docker build -t $SERVER_IMAGE ./$SERVER_FOLDER
    echo "server image created."
fi

docker container inspect $SERVER_CONTAINER >/dev/null 2>&1
if [ $? -eq 0 ]; then
    docker container stop $SERVER_CONTAINER
    docker container rm $SERVER_CONTAINER
    echo "server container removed."    
fi

for i in {0..9}
do
	docker run -d --name "${SERVER_CONTAINER}_${i}" -p "800${i}":"800${i}" -v $(pwd)/$SERVER_FOLDER:/app --network $SERVER_NETWORK --cap-add NET_ADMIN $SERVER_IMAGE
done	









