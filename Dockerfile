FROM python:3

RUN pip install --pre poetry==1.0.0b5
COPY . /tmp/meme-bot
COPY fonts/* /usr/share/fonts/truetype/
WORKDIR /tmp/meme-bot
RUN poetry export -f requirements.txt > requirements.txt
RUN pip install -r requirements.txt
CMD [ "python", "-m", "apps.bot.memebot" ]
