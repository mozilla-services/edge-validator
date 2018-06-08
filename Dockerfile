FROM python:3.6-slim
MAINTAINER Anthony Miyaguchi <amiyaguchi@mozilla.com>

ENV PYTHONUNBUFFERED=1 \
    PIPENV_VENV_IN_PROJECT=1 \
    # AWS_ACCESS_KEY_ID= \
    # AWS_SECRET_ACCESS_KEY= \
    SHELL=/bin/bash \
    PORT=8000

EXPOSE $PORT

# Bootstrap the system with root privileges
RUN apt-get update && \
    apt-get --yes install make git
RUN pip install --upgrade pip
RUN pip install pipenv

# Create the application user
WORKDIR /app
RUN groupadd --gid 10001 app && \
    useradd --gid app --uid 10001 --home-dir /app app

# Start the userland environment
COPY . /app
RUN chown -R app:app /app

USER app
ENV PATH="/app/.venv/bin:$PATH"

RUN make sync
CMD pipenv run flask run --host 0.0.0.0 --port $PORT
