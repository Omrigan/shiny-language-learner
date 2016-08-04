FROM ubuntu:16.04
MAINTAINER Oleg Vasilev <omrigann@gmail.com>
RUN apt-get update
RUN apt-get -y upgrade
RUN apt-get install -y curl build-essential
RUN apt-get install -y python3 python3-dev python3-pip
RUN apt-get install -y zlib1g-dev
RUN apt-get install -y libxslt1-dev lzma libxml2-dev libxml2 python3-lxml
RUN pip3 install --upgrade pip
ADD . /root/bot
WORKDIR /root/bot
RUN pip3 install -e /root/bot --upgrade
RUN python3 -m nltk.downloader wordnet
CMD python3 /root/bot/main.py