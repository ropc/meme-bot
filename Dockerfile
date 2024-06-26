# build stage
FROM python:3.12 AS builder

# install PDM
RUN pip install -U pip setuptools wheel
RUN pip install pdm

WORKDIR /project

RUN curl -sL https://github.com/ipython/xkcd-font/raw/master/xkcd-script/font/xkcd-script.ttf -o /project/xkcd-script.ttf

# copy files
COPY pyproject.toml pdm.lock /project/
RUN mkdir __pypackages__ && pdm sync --prod --no-editable

# run stage
FROM python:3.12
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg && rm -rf /var/lib/apt/lists/*
ENV PYTHONPATH=/project/pkgs
COPY --from=builder /project/__pypackages__/3.12/lib /project/pkgs
# retrieve executables
COPY --from=builder /project/__pypackages__/3.12/bin/* /bin/
WORKDIR /project
COPY --from=builder /project/*.ttf /usr/share/fonts/truetype/
COPY fonts/* /usr/share/fonts/truetype/
COPY assets ./assets
COPY tests ./tests
COPY meme_generator ./meme_generator
COPY memebot ./memebot

HEALTHCHECK CMD discordhealthcheck || exit 1
ENTRYPOINT [ "python", "-m" ]
CMD [ "memebot.memebot", "run" ]
