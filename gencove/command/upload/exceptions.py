"""Upload command exceptions"""


class UploadError(Exception):
    """Upload related error."""


class UploadNotFound(Exception):
    """Upload related error."""


class SampleSheetError(Exception):
    """Error to generate the sample sheet for uploads."""
