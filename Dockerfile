FROM ubuntu:14.04
MAINTAINER Oleg Vasilev <omrigann@gmail.com>
RUN apt-get update
RUN apt-get -y upgrade
RUN apt-get install -y tar git curl nano wget dialog net-tools build-essential libxml2 python3-lxml
RUN apt-get install -y python3 python3-dev python3-pip python python-pip python-dev
RUN apt-get install -y libxslt1-dev libxml2-dev lzma
RUN pip3 install --upgrade pip
ADD . /root/bot
WORKDIR /root/bot
RUN pip3 install -e /root/bot --upgrade
RUN python3 -m nltk.downloader wordnet
CMD python3 /root/bot/main.py