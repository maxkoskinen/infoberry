FROM python:3.9
WORKDIR /server
COPY  /server /server
COPY requirements.txt requirements.txt 
RUN pip install --no-cache-dir -r requirements.txt
ENV UWSGI_INI /server/uwsgi.ini
EXPOSE 8080
RUN flask --app app init-db
CMD ["uwsgi", "--ini", "/server/uwsgi.ini"]