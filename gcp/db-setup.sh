#!/bin/bash
docker stop pg
docker stop pgadmin
docker run -p 5432:5432 -e POSTGRES_PASSWORD=123456 -e POSTGRES_HOST_AUTH_METHOD=trust -d -it --rm --name pg postgres
docker run -p 5555:80 --name pgadmin -e PGADMIN_DEFAULT_EMAIL="admin@dttsa.com" -e PGADMIN_DEFAULT_PASSWORD="123456" -d -it --rm dpage/pgadmin4
docker ps

