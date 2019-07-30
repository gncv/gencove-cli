"""Utility to generate version string."""
import pkgutil


def version():
    """Return version string."""
    major = pkgutil.get_data(__package__, "version/A-major").strip()
    minor = pkgutil.get_data(__package__, "version/B-minor").strip()
    patch = pkgutil.get_data(__package__, "version/C-patch").strip()
    return "{}.{}.{}".format(
        major.decode("utf-8"), minor.decode("utf-8"), patch.decode("utf-8")
    )
