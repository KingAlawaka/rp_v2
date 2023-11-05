#!/bin/bash
p=9100

for i in {1..10}
do
        kill -9 $(lsof -i:$(( p + i )) -t) 2> /dev/null
done

for i in {1..5}
do
        # echo $(( p + i ))
        # echo data${i}.db
        screen -d -m python3 dt.py -port $(( p + i )) -db data${i}.db
done

screen -ls