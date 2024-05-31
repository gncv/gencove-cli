"""Packaging for Gencove CLI."""
from setuptools import find_packages, setup


def version():
    """Return current package version."""
    with open("gencove/version/A-major", "rt") as f:
        major = f.read().replace("\n", "")
    with open("gencove/version/B-minor", "rt") as f:
        minor = f.read().replace("\n", "")
    with open("gencove/version/C-patch", "rt") as f:
        patch = f.read().replace("\n", "")

    return f"{major}.{minor}.{patch}"


def long_description():
    with open("gencove/description/pypi_readme.md") as f:
        text = f.read()
    return text


setup(
    name="gencove",
    description="Gencove API and CLI tool",
    long_description=long_description(),
    long_description_content_type="text/markdown",
    url="https://docs.gencove.com",
    author="Tomaz Berisa",
    license="Apache 2.0",
    version=version(),
    python_requires=">=3.7",
    packages=find_packages(exclude=["tests"]),
    install_requires=[
        # For the python-dateutil requirement, see:
        # https://github.com/awslabs/aws-shell/issues/161
        # and
        # https://stackoverflow.com/questions/27630114/matplotlib-issue-on-os-x-importerror-cannot-import-name-thread
        "python-dateutil>=2.2.0",
        # This six requirement is related to the python-dateutil requirement
        # above - we are attempting to keep the requirement as loose as
        # possible in terms of minimal required version
        "six>=1.5",
        "Click>=7.0",
        "requests>=2.19.1",
        "boto3>=1.17.97",
        "progressbar2==3.55.0",
        "backoff<=2.2.1",
        "pydantic==1.10.13",
        "click-default-group>=1.2.4",
        "sh>=1.14.3",
    ],
    setup_requires=["pytest-runner"],
    tests_require=["pytest", "pytest-mock"],
    entry_points="""
        [console_scripts]
        gencove=gencove.cli:cli
        d=gencove.command.explorer.data.cli:data
    """,
    package_data={"gencove": ["version/*", "description/*"]},
)
