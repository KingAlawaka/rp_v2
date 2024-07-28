FROM python:3.10-slim-bullseye

ENV app /app

RUN mkdir $app
WORKDIR $app
COPY . $app

#RUN apk add build-base
#RUN pip install --upgrade pip wheel
#RUN pip3 install -r requirements.txt
RUN pip install -r DTrequirements.txt

#WORKDIR API/
#EXPOSE 9000
#ENTRYPOINT [ "python", "./app.py"]
#docker run -d -it --name dt2 dt_19_11 -port 9100 -db data.db
EXPOSE 9100
ENTRYPOINT [ "python", "./dt.py"]
# ENTRYPOINT [ "python", "./dt_backup_last.py"]
# ENTRYPOINT [ "python", "./dt_backup_5_12.py"]
# ENTRYPOINT [ "python", "./dt_backup_v2.py"]
# ENTRYPOINT [ "python", "./dt_dtbackup_5_12.py"]
# ENTRYPOINT [ "python", "./dt_doc_29_5_23_v3.py" ]