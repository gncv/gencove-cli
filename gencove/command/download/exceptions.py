"""Download command exceptions."""


class DownloadTemplateError(Exception):
    """Error that indicates an issue with the template.

     Caused by download overwriting previously downloaded files.
     """
