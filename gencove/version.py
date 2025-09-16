"""Utility to generate version string."""
import os


def version():
    """Return version string."""
    base_dir = os.path.dirname(__file__)
    with open(os.path.join(base_dir, "version", "A-major")) as f:
        major = f.read().strip()
    with open(os.path.join(base_dir, "version", "B-minor")) as f:
        minor = f.read().strip()
    with open(os.path.join(base_dir, "version", "C-patch")) as f:
        patch = f.read().strip()
    return f"{major}.{minor}.{patch}"


def get_version():
    """Return version string for setuptools dynamic versioning."""
    return version()
