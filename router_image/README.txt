##### nombrar network1 y network2 segun el nombre de network de los contenedores que desean hablar entre ellos #######

docker build -t custom-router .
docker run -it --name router --network network1 --privileged custom-router
docker network connect network2 router

### Ejemplo de contenedores en ventanas terminales separadas  ####
docker run -it --name server --network network1 alpine sh
docker run -it --name client --network network2 alpine sh

### Desde la terminal principal ...Para saber las ip de los contenedores ...
docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' server
docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' cliente

### Desde cliente ####
ping IP-Server

#### Desde el server ...
ping IP-Cliente

### si ejecutas el contenedor sin -it y bash o sh  acceder al contenedor para ejecutar los comandos... pejemplo
### desde la terminal principal

docker exec -it cliente bash
> ping IP-server


