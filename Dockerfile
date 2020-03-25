FROM python:3

RUN pip install poetry==1.0.3
COPY . /tmp/meme-bot
COPY fonts/* /usr/share/fonts/truetype/
WORKDIR /tmp/meme-bot
RUN poetry install
CMD [ "poetry", "run", "bot" ]
