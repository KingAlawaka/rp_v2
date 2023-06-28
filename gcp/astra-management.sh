#!/bin/bash
docker stop astra-mongo
docker stop astra
docker run --name astra-mongo -d --rm mongo
docker run -d -it --rm --name astra  -e MONGO_PORT_27017_TCP_ADDR=172.17.0.4 -p 8094:8094 kingalawaka/astra-old-mod3
docker ps

#update
#!/bin/bash
docker stop astra-mongo
docker stop astra
docker run --name astra-mongo -d --rm mongo
echo "waiting for mongo db"
sleep 10
docker run -d -it --rm --name astra  -e MONGO_PORT_27017_TCP_ADDR=172.17.0.4 -p 8094:8094 kingalawaka/astra-old-mod3
docker ps