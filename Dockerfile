FROM ubuntu:14.04
MAINTAINER Oleg Vasilev <omrigann@gmail.com>
ENV BOT_ENV production
RUN apt-get update
RUN apt-get -y upgrade
RUN apt-get install -y tar \
                   git \
                   curl \
                   nano \
                   wget \
                   dialog \
                   net-tools \
                   build-essential
RUN apt-get install -y python3 python3-dev python3-pip python python-pip python-dev
RUN pip3 install --upgrade pip
ADD . /root/bot
RUN pip3 install --upgrade  -r /root/bot/requirements.txt
RUN python3 -m nltk.downloader wordnet
WORKDIR /root/bot
CMD python3 /root/bot/main.py