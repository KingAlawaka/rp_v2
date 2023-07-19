#!/bin/bash
docker ps -aq | xargs docker stop | xargs docker rm
docker container prune
./db-setup.sh
./astra-management.sh
./dttsa-service.sh
docker ps
