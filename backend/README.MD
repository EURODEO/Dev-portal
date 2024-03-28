# Backend
Backend application for Developer Portal written in Python 3.12 and FastAPI.

### Project structure
```bash
backend
├── app
│   ├── __init__.py  # Init module
│   ├── config.py # Configuration settings, logger etc
│   ├── dependencies # Dependencies needed in routers
│   │   ├── http_client.py
│   │   └── ...
│   ├── exceptions.py # Global exceptions
│   ├── main.py # Application runner
│   ├── routers # Routers (or controllers, routes) for the app
│   │   ├── __init__.py
│   │   ├── apikey.py
│   │   ├── ...
│   ├── services # Business logic & external services
│   │   ├── apisix.py
│   │   └── ...
│   └── utils # Utility functions and classes
│       ├── uuid.py
│       └── ...
├── tests
│    ├── conftest.py
│    └── ...
├── config.yaml # configuration values
├── scripts.py # scripts to run with poetry run
└── pyproject.toml # Configuration file for Poetry, dependencies, other metadata
```
### Prerequisites

1. Install Python version 3.12
2. Install [Poetry](https://python-poetry.org) 


### Initialize

To initialize the project, follow these steps:

1. Install the dependencies: `poetry install`


### Configurations
By default the application looks for config file in path `backend/config.default.yaml`.
You can override these settings by creating a file called `backend/config.yaml` or using an environment variable `CONFIG_FILE` for example `CONFIG_FILE=better-config.yaml`
`CONFIG_FILE` takes priority over the file paths.

#### Example config.default.yaml
```yaml
port: 8082
log_level: "INFO"
apisix:
  admin_url: http://127.0.0.1:9180
  gateway_url: http://127.0.0.1:9080
  admin_api_key: edd1c9f034335f136f87ad84b625c8f1
  key_path: $secret://vault/dev/
vault:
  url: http://127.0.0.1:8200
  base_path: apisix-dev/consumers/ewc
  token: 00000000-0000-0000-0000-000000000000
  secret_phase: geeks
keycloak:
  url: http://127.0.0.1:8080
  realm: test
```

### Run app in development mode
To run the application in local machine type `poetry run start-dev`.

If for some reason you need to run the application with different config file you can do it by giving the file as env variable to start command `CONFIG_FILE=better-config.yaml poetry run start-dev`


### Static analysis tools and tests

There are couple of analyze tools used. All the tool specific configurations if any are placed in pyproject.toml file.

1. [Black](https://pypi.org/project/black/) for checking and formatting code. You can run black formatting with `poetry run format` or to check if there is anything to format with `poetry run format-check`

2. [Pylint](https://pylint.readthedocs.io/en/latest/) for linting the application code. To run pylint type `poetry run lint`

3. [Mypy](https://www.mypy-lang.org/) for static type checking. Current rules are taken from https://careers.wolt.com/en/blog/tech/professional-grade-mypy-configuration. To run pylint type `poetry run type-check`

4. [Bandit](https://bandit.readthedocs.io/en/latest/) to find common security issues in Python code. To run bandit type `poetry run sec-check`

5. [Pytest](https://docs.pytest.org/en/8.0.x/index.html) to run tests. Before running tests make sure that external services are up and running by running the docker-compose.yml and then running tests with `poetry run test`

All of these are run also in ci cd pipeline before building the image.

TODO add pre-commit hooks to automatically run these before commit

#### MISC ATM

Dockerize the backend app and run it with local dev stack with command

`docker run --network dev-portal_apisix -p 8082:8082 -v $(pwd)/local-docker-config.yaml:/code/config.yaml my_app:latest`

Here we connect the dockerized backend app to services container. Using also different config.yaml to this (urls diffs when using docker or not)

