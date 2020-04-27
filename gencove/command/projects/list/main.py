"""List projects subcommand."""
import backoff

import requests

# pylint: disable=wrong-import-order
from gencove.client import APIClientError  # noqa: I100
from gencove.command.base import Command

from .constants import PipelineCapabilities, Project
from .exceptions import ProjectsError
from .utils import get_line


class List(Command):
    """List projects command executor."""

    def initialize(self):
        """Initialize list subcommand."""
        self.login()

    def validate(self):
        """Validate command input."""

    def execute(self):
        self.echo_debug("Retrieving projects")

        for projects in self.get_paginated_projects():
            if not projects:
                self.echo_debug("No projects were found.")
                return

            augmented_projects = self.augment_projects_with_pipeline_capabilities(  # noqa: E501
                projects
            )

            for project in augmented_projects:
                self.echo(get_line(project))

    def get_paginated_projects(self):
        """Paginate over all projects.

        Yields:
            paginated lists of projects
        """
        more = True
        next_link = None
        while more:
            self.echo_debug("Get projects page")
            try:
                resp = self.get_projects(next_link)
                yield [Project(**result) for result in resp["results"]]
                next_link = resp["meta"]["next"]
                more = next_link is not None
            except APIClientError as err:
                self.echo_debug(err)
                raise ProjectsError

    @backoff.on_exception(
        backoff.expo,
        (requests.exceptions.ConnectionError, requests.exceptions.Timeout),
        max_tries=2,
        max_time=30,
    )
    def get_projects(self, next_link=None):
        """Get projects page."""
        return self.api_client.list_projects(next_link)

    @backoff.on_exception(
        backoff.expo,
        (requests.exceptions.ConnectionError, requests.exceptions.Timeout),
        max_tries=3,
        max_time=30,
    )
    def get_pipeline_capabilities(self, pipeline_id):
        """Get pipeline capabilities."""
        resp = self.api_client.get_pipeline_capabilities(pipeline_id)
        return PipelineCapabilities(**resp)

    def augment_projects_with_pipeline_capabilities(self, projects):
        """Fetch pipeline capabilities and append it to the project.

        Args:
            projects (list[Project]): list of projects

        Returns:
            list[Project]: same list of projects with pipeline capabilities
                uuid replaced with PipelineCapability
        """
        for project in projects:
            pipeline_capabilities = self.get_pipeline_capabilities(
                project.pipeline_capabilities
            )
            yield project._replace(
                pipeline_capabilities=pipeline_capabilities
            )
