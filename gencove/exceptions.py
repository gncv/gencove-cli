"""Define common exceptions in Gencove CLI."""


class ValidationError(Exception):
    """CLI validation error - indicating command input is not valid."""

    def __init__(self, message=""):
        super().__init__(message)
        self.message = message
