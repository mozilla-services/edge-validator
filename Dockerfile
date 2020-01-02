FROM python:3.8-slim
MAINTAINER Anthony Miyaguchi <amiyaguchi@mozilla.com>

ENV PYTHONUNBUFFERED=1 \
    SHELL=/bin/bash \
    PORT=8000

EXPOSE $PORT

# Bootstrap the system with root privileges
RUN apt-get update && \
    apt-get --yes install make git rsync curl gnupg

# install cloud sdk
RUN echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] http://packages.cloud.google.com/apt cloud-sdk main" | \
    tee -a /etc/apt/sources.list.d/google-cloud-sdk.list && \
    curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | \
    apt-key --keyring /usr/share/keyrings/cloud.google.gpg  add - && \
    apt-get update -y && \
    apt-get install google-cloud-sdk -y

RUN pip install --upgrade pip

# Create the application user
WORKDIR /app
RUN groupadd --gid 10001 app && \
    useradd --gid app --uid 10001 --home-dir /app app

# Start the userland environment
COPY . /app
RUN chown -R app:app /app
RUN pip install -r requirements.txt

USER app
RUN make sync
CMD flask run --host 0.0.0.0 --port $PORT
