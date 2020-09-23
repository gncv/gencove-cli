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

    return "{}.{}.{}".format(major, minor, patch)


setup(
    name="gencove",
    description="Gencove API and CLI tool",
    url="http://docs.gencove.com",
    author="Tomaz Berisa",
    license="Apache 2.0",
    version=version(),
    python_requires=">=3.6",
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
        "boto3>=1.9.188",
        "progressbar2==3.50.1",
        "backoff==1.10.0",
    ],
    setup_requires=["pytest-runner"],
    tests_require=["pytest", "pytest-mock"],
    entry_points="""
        [console_scripts]
        gencove=gencove.cli:cli
    """,
    package_data={"gencove": ["version/*"]},
)
