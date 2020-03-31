FROM python:3

RUN apt-get update && apt-get install -y ffmpeg
RUN pip install poetry==1.0.3
COPY . /tmp/meme-bot
COPY fonts/* /usr/share/fonts/truetype/
WORKDIR /tmp/meme-bot
RUN poetry install --no-dev
CMD [ "poetry", "run", "bot" ]
