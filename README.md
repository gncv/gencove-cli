# Gencove Python API and CLI

## Quick install ##
`pip install gencove`

## Documentation ##
Main documentation can be found here: [http://docs.gencove.com](http://docs.gencove.com)

## Local Development ##

Have some form of virtualization, for instance pyenv for 3.7.x and a virtualenv.

Install in editing mode:
```bash
pip install -e .
```

Install local requirements:
```bash
pip install -r requirements.txt
```

Install pre-commit hooks:
```bash
pre-commit install
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
pre-commit run
```

and then:

```bash
tox
```

This will run tests, black formatter and linters.

To run only a specific job from tox (i.e. only the tests for python 3.7 using API key):

```bash
tox -e py37-api_key
```
If you invoke tox like this:

```
tox -e py37-api_key -- gencove/tests/test_utils.py
```
or
```
tox -e py37-api_key -- gencove/tests/test_utils.py::test_is_valid_uuid__is_not_valid__text
```
the arguments after the -- will be substituted everywhere where you specify {posargs} in your test commands.


Tests Configuration:

If you need to interact with the API (for instance to record new VCR cassettes) you need to set up environment variables, this way, the tests will have the credentials to have access.
In order to do that, just run `cp gencove/tests/.env.dist gencove/tests/.env` and change the desired values from the `.env` file.

For more details, read internal `CLI testing` document.


To create docs:

```bash
cd docs && make html
```

## Release process ##

1. Check for the current version by running `version-01-upgrade.sh print`
2. Make a new branch titled version/X-Y-Z
3. Run `version-01-upgrade.sh` in that branch with an argument `major`, `minor` or `patch`
4. Create a merge request to master
5. Once it is merged, create a merge request of master to prod
