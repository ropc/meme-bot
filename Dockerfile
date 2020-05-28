FROM python:3.8-slim-buster

RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg && rm -rf /var/lib/apt/lists/*
RUN pip install poetry==1.0.5
WORKDIR /tmp/meme-bot
COPY poetry.lock pyproject.toml ./
RUN poetry install --no-dev --no-root
COPY fonts/* /usr/share/fonts/truetype/
COPY assets ./assets
COPY tests ./tests
COPY meme_generator ./meme_generator
COPY memebot ./memebot
RUN poetry install --no-dev --no-interaction
ENTRYPOINT [ "poetry", "run" ]
CMD [ "bot" ]
