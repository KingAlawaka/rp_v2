#!/bin/sh

echo "Starting trust and security analyzer support services"


docker pull mongo
docker run --name astra-mongo -d mongo
docker run --rm -it --link astra-mongo:mongo -p 8094:8094 astra

sudo /usr/pgadmin4/bin/setup-web.sh

