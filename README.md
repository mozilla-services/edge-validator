# edge-validator

A service-endpoint for validating pings against `mozilla-pipeline-schemas`.

See [bug 1452166](https://bugzilla.mozilla.org/show_bug.cgi?id=1452166) for motivating background.

## User Guid
### Installation

```bash
# clone and set the working directory
$ git clone https://github.com/acmiyaguchi/edge-validator.git
$ cd edge-validator

# make sure that the system pip is up to date
$ pip install --user --upgrade pip

# install pipenv for managing the application environment
$ pip install --user pipenv

# bootstrap for test and serve
$ make sync
```

### Serving
#### serving via docker host (recommended)

```bash
$ docker --version  # ensure that docker is installed
$ make run          # start the service
```

#### serving via local host
The docker host automates the following bootstrap process. `pipenv` should be installed on the host system. 

```bash
$ pipenv shell              # enter the application environment
$ pipenv sync               # update the environment
$ flask run --port 8000     # run the application
```

### Running tests

Unit tests do not require any dependencies and can be run out of the box. The sync command will
copy the test resources into the application resource folder.
```bash
$ make sync
$ make test
```

An integration report gives a performance report based on sampled data. Make sure that
aws is set up correctly.

```bash
# Run using the local app context
$ make report

# Run using the docker host
$ EXTERNAL=1 PORT=800 make report
```
