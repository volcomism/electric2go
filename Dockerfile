FROM python:3.4.4
MAINTAINER dn-devops@sixt.com

COPY . /usr/src/app

WORKDIR /usr/src/app

RUN pip install -r requirements.txt

ENTRYPOINT [ "python", "./scripts/download.py drivenow all" ]
