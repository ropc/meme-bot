FROM python:3

RUN pip install --pre poetry
COPY . /tmp/meme-bot
COPY fonts/* /usr/share/fonts/truetype/
WORKDIR /tmp/meme-bot
RUN poetry export -f requirements.txt > requirements.txt
RUN pip install -r requirements.txt
CMD [ "python", "./memebot/main.py" ]
