FROM nikolaik/python-nodejs:python3.9-nodejs16
RUN apt update -y && apt upgrade -y
RUN apt install ffmpeg -y
COPY . /TgMusicBot
WORKDIR /TgMusicBot

RUN pip3 install --no-cache-dir -r requirements.txt -U
CMD ["python3", "main.py"]
