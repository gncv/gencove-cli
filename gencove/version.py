"""Utility to generate version string."""
import os


def version():
    """Return version string."""
    base_dir = os.path.dirname(__file__)
    with open(
        os.path.join(base_dir, "version", "A-major"), encoding="utf-8"
    ) as major_file:
        major = major_file.read().strip()
    with open(
        os.path.join(base_dir, "version", "B-minor"), encoding="utf-8"
    ) as minor_file:
        minor = minor_file.read().strip()
    with open(
        os.path.join(base_dir, "version", "C-patch"), encoding="utf-8"
    ) as patch_file:
        patch = patch_file.read().strip()
    return f"{major}.{minor}.{patch}"
