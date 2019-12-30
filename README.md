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
