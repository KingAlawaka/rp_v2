docker stop dttsa
sleep 10
docker container prune
docker run -d -it --restart always -v $(pwd)/csv:/app/API/csv  --name dttsa -p 9000:9000 kingalawaka/dttsa:v1