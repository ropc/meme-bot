FROM python:3.8-slim-buster

RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg && rm -rf /var/lib/apt/lists/*
RUN pip install poetry==1.1.2
WORKDIR /tmp/meme-bot
COPY poetry.lock pyproject.toml ./
RUN poetry export -f requirements.txt > requirements.txt && poetry run pip install -r requirements.txt
COPY fonts/* /usr/share/fonts/truetype/
COPY assets ./assets
COPY tests ./tests
COPY meme_generator ./meme_generator
COPY memebot ./memebot
ENTRYPOINT [ "poetry", "run" ]
CMD [ "bot" ]
