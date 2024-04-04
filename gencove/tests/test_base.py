import pytest

from gencove.command.base import Command
from gencove.constants import Credentials, Optionals


class SimpleCommand(Command):
    """Dummy command for testing, does not extend base class functionality"""

    def initialize(self):
        """Pass"""
        pass

    def validate(self):
        """Pass"""
        pass

    def execute(self):
        """Pass"""
        pass


@pytest.fixture
def empty_credentials():
    """Return empty credentials"""
    return Credentials(api_key="", email="", password="")


class TestFetchCredentialsFromEnv:
    """Test case for fetching credentials from environment variable behavior"""

    def test_no_credentials_provided_uses_api_env_var(
        self, monkeypatch, empty_credentials
    ):
        """Test CLI uses API key when no creds provided and all ENV available"""
        monkeypatch.setenv("GENCOVE_API_KEY", "env_api_key")
        monkeypatch.setenv("GENCOVE_EMAIL", "env_email@example.com")
        monkeypatch.setenv("GENCOVE_PASSWORD", "env_password")

        command = SimpleCommand(
            credentials=empty_credentials, options=Optionals(host="http://example.com")
        )

        # Command should prioritize API key from environment variable, ignore email
        assert command.credentials.api_key == "env_api_key"
        assert command.credentials.password == "env_password"
        assert command.credentials.email == ""
        assert command.is_credentials_valid is True

    def test_api_key_provided_skips_env_vars(self, monkeypatch, empty_credentials):
        """Test CLI uses provided API key and ignores ENV variables"""
        monkeypatch.setenv("GENCOVE_API_KEY", "wrong_api_key")
        monkeypatch.setenv("GENCOVE_EMAIL", "wrong_email@example.com")

        credentials = Credentials(api_key="correct_api_key", email="", password="")
        command = SimpleCommand(
            credentials=credentials, options=Optionals(host="http://example.com")
        )

        assert command.credentials.api_key == "correct_api_key"
        assert command.credentials.email == ""
        assert command.credentials.password == ""
        assert command.is_credentials_valid is True

    def test_email_password_provided_skips_env_vars(
        self, monkeypatch, empty_credentials
    ):
        """Test CLI uses provided email and password and ignores ENV variables"""
        monkeypatch.setenv("GENCOVE_API_KEY", "env_api_key")
        monkeypatch.setenv("GENCOVE_EMAIL", "wrong_email@example.com")
        monkeypatch.setenv("GENCOVE_PASSWORD", "wrong_password")

        credentials = Credentials(
            api_key="", email="correct_email@example.com", password="correct_password"
        )
        command = SimpleCommand(
            credentials=credentials, options=Optionals(host="http://example.com")
        )

        assert command.credentials.api_key == ""
        assert command.credentials.email == "correct_email@example.com"
        assert command.credentials.password == "correct_password"
        assert command.is_credentials_valid is True

    def test_no_env_vars_empty_defaults(self, empty_credentials):
        """Test CLI uses empty strings for credentials when no ENV variables set and
        no creds provided"""
        command = SimpleCommand(
            credentials=empty_credentials, options=Optionals(host="http://example.com")
        )

        assert command.credentials.api_key == ""
        assert command.credentials.email == ""
        assert command.credentials.password == ""
        assert command.is_credentials_valid is True

    def test_email_uses_env_password(self, monkeypatch, empty_credentials):
        """Test CLI uses provided email and ENV password"""
        monkeypatch.setenv("GENCOVE_API_KEY", "env_api_key")
        monkeypatch.setenv("GENCOVE_EMAIL", "env_email@example.com")
        monkeypatch.setenv("GENCOVE_PASSWORD", "env_password")

        credentials = Credentials(
            api_key="", email="provided_email@example.com", password=""
        )
        command = SimpleCommand(
            credentials=credentials, options=Optionals(host="http://example.com")
        )

        assert command.credentials.api_key == ""
        assert command.credentials.email == "provided_email@example.com"
        assert command.credentials.password == "env_password"
        assert command.is_credentials_valid is True

    def test_multiple_credentials_not_allowed(self, empty_credentials):
        """Test CLI does not allow multiple credentials to be provided"""
        credentials = Credentials(
            api_key="api_key", email="email@example.com", password="password"
        )
        command = SimpleCommand(
            credentials=credentials, options=Optionals(host="http://example.com")
        )
        assert command.is_credentials_valid is False
