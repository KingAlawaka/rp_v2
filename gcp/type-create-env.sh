#!/bin/bash
p=9000
for i in {1..8}
do
        docker run -d -it --restart always  --name "dt-${i}" -p $(( p + i )):9100 --env dt_type=n kingalawaka/dt-29-5-23-v3
done

for i in {9..16}
do
        docker run -d -it --restart always  --name "dt-${i}" -p $(( p + i )):9100 --env dt_type=c kingalawaka/dt-29-5-23-v3
done

for i in {17..24}
do
        docker run -d -it --restart always  --name "dt-${i}" -p $(( p + i )):9100 --env dt_type=m kingalawaka/dt-29-5-23-v3
done

b=9029
for i in {1..10}
do
        docker run -d -it --restart always  --name "backup-dt-${i}" -p $(( b + i )):9100  kingalawaka/backup-dt-17-06-23
done