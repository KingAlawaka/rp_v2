#!/bin/bash
p=9000
for i in {1..25}
do
        docker run -d -it --restart always  --name "dt-${i}" -p $(( p + i )):9100 --env dttsa_IP=http://34.173.74.160:9000 kingalawaka/dt-29-5-23-v3
done