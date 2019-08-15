"""Packaging for Gencove CLI."""
from setuptools import find_packages, setup


def version():
    """Return current package version."""
    with open('gencove/version/A-major', 'rt') as f:
        major = f.read().replace('\n', '')
    with open('gencove/version/B-minor', 'rt') as f:
        minor = f.read().replace('\n', '')
    with open('gencove/version/C-patch', 'rt') as f:
        patch = f.read().replace('\n', '')

    return '{}.{}.{}'.format(major, minor, patch)


setup(
    name="gencove",
    description="Gencove API and CLI tool",
    url="http://docs.gencove.com",
    author="Tomaz Berisa",
    license="Apache 2.0",
    version=version(),
    packages=find_packages(exclude=["tests"]),
    install_requires=[
        "Click>=7.0",
        "requests>=2.19.1",
        "boto3>=1.9.188",
        "future",
        "tqdm",
    ],
    setup_requires=[
        "pytest-runner"
    ],
    tests_require=[
        "pytest",
        "pytest-mock",
    ],
    entry_points="""
        [console_scripts]
        gencove=gencove.cli:cli
    """,
    package_data={"gencove": ["version/*"]},
)
