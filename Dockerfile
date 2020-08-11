FROM python:3.6
# Create app directory
RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app

COPY . /usr/src/app

RUN pip3 install -r ./requirements.txt


WORKDIR src

# RUN ["gunicorn","web-server:app"]