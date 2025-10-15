# build stage
FROM python:3.12-slim AS builder

# install PDM
RUN apt-get update && apt-get install -y --no-install-recommends curl gcc g++ \
    && pip install --no-cache-dir -U pip setuptools wheel pdm \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /project

# copy files
COPY pyproject.toml pdm.lock /project/
RUN mkdir __pypackages__ && pdm sync --prod --no-editable --no-self

# run stage
FROM python:3.12-slim
RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*
ENV PYTHONPATH=/project/pkgs
COPY --from=builder /project/__pypackages__/3.12/lib /project/pkgs
# retrieve executables
COPY --from=builder /project/__pypackages__/3.12/bin/* /usr/local/bin/
WORKDIR /project
COPY fonts/* /usr/share/fonts/truetype/
COPY assets ./assets
COPY meme_generator ./meme_generator
COPY memebot ./memebot

HEALTHCHECK CMD discordhealthcheck || exit 1
ENTRYPOINT [ "python", "-m" ]
CMD [ "memebot.memebot", "run" ]
