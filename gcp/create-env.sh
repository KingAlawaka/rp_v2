#!/bin/bash
docker ps -aq | xargs docker stop | xargs docker rm
p=9000
for i in {1..25}
do
        docker run -d -it --restart always  --name "dt-${i}" -p $(( p + i )):9100 --env dttsa_IP=http://34.173.74.160:9000 kingalawaka/dt-29-5-23-v3
done

b=9029
for i in {1..10}
do
        docker run -d -it --restart always  --name "backup-dt-${i}" -p $(( b + i )):9600 --env dttsa_IP=http://34.173.74.160:9000 kingalawaka/backup-dt-17-06-23
done