# Gencove Python API and CLI

## Quick install ##
`pip install gencove`

## Documentation ##
Main documentation can be found here: [http://docs.gencove.com](http://docs.gencove.com)

## Local Development

```bash
pip install -e .
```

Install local requirements:
```bash
pip install -r requirements.txt
```

Use with local api service (need to have [back_api2](http://gitlab.com/gencove/v2/back_api2/) running)

```
gencove <command> --host http://localhost:8200
```

or use with development version of deployed API service

```
gencove <command> --host https://api-dev.gencove-dev.com
```

Before pushing run:

```bash
tox
```

This will run tests, black formatter and linters.

To run only a specific job from tox (i.e. only the tests for python 3.7):

```bash
tox -e py37
```

To create docs:

```bash
cd docs && make html
```
