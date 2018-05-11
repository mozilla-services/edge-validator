FROM python:3.6-slim
MAINTAINER Anthony Miyaguchi <amiyaguchi@mozilla.com>

# bootstrap
ENV PYTHONUNBUFFERED=1 \
    PORT=8000

EXPOSE $PORT

RUN apt-get update && \
    apt-get --yes install make git
RUN pip install --upgrade pip
RUN pip install pipenv

WORKDIR /app
RUN groupadd --gid 10001 app && \
    useradd --gid app --uid 10001 --home-dir /app app
RUN chown -R app:app /app

COPY . /app

# start userland
USER app
RUN make sync
CMD pipenv run flask run --host 0.0.0.0 --port $PORT
