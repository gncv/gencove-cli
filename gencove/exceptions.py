"""Define common exceptions in Gencove CLI."""


class ValidationError(Exception):
    """CLI validation error - indicating command input is not valid."""

    def __init__(self, message=""):
        super().__init__(message)
        self.message = message


class MaintenanceError(Exception):
    """API maintenance error - indicating backend API is in maintenance mode."""

    def __init__(self, message="", eta=""):
        super().__init__(message)
        self.message = message
        self.eta = eta
