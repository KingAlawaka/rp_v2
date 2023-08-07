FROM python:3.10-slim-bullseye

ENV app /app

RUN mkdir $app
WORKDIR $app
COPY . $app

#RUN apk add build-base
#RUN pip install --upgrade pip wheel
#RUN pip3 install -r requirements.txt
RUN pip install -r DTrequirements.txt

#CMD cd API
#RUN cd API/
WORKDIR $app/API/
#EXPOSE 9000
#ENTRYPOINT [ "python", "./app.py"]
#docker run -d -it --name dttsa -v $(pwd)/API/csv:/app/API/csv dttsa-26-11
EXPOSE 9000
ENTRYPOINT [ "python", "dttsa.py"]
# ENTRYPOINT [ "python", "dttsa_12_12_c1.py"]