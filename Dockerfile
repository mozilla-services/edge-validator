FROM python:3.6-slim
MAINTAINER Anthony Miyaguchi <amiyaguchi@mozilla.com>

# bootstrap
ENV PYTHONUNBUFFERED=1 \
    PORT=8000 \
    WEB_CONCURRENCY=1

EXPOSE $PORT

RUN pip install --upgrade pip
RUN pip install pipenv

WORKDIR /app
RUN groupadd --gid 10001 app && \
    useradd --gid app --uid 10001 --home-dir /app app
RUN chown -R app:app /app

COPY . /app

# start userland
RUN pipenv sync
CMD pipenv run gunicorn -b 0.0.0.0:$PORT app:app