FROM ubuntu:20.04
ENV DEBIAN_FRONTEND=noninteractive
RUN apt update && apt upgrade -y
RUN apt install git curl python3.9 python3 python python3-pip python3.9-distutils ffmpeg wget -y
RUN curl -fsSL https://deb.nodesource.com/setup_16.x | bash -
RUN apt install nodejs -y
RUN npm install -g npm
RUN mkdir /TgMusicBot
COPY . /TgMusicBot/
WORKDIR /TgMusicBot/
RUN python3.9 -m pip install -r requirements.txt -U
CMD python3.9 main.py
