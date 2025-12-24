"""List projects subcommand."""
import backoff

# pylint: disable=wrong-import-order
from gencove.client import APIClientError, APIClientTimeout  # noqa: I100
from gencove.command.base import Command
from gencove.constants import HiddenStatus
from gencove.models import Project

from .utils import get_line


class List(Command):
    """List projects command executor."""

    def __init__(self, include_hidden, include_capability, credentials, options):
        super().__init__(credentials, options)
        self.include_hidden = include_hidden
        self.include_capability = include_capability

    def initialize(self):
        """Initialize list subcommand."""
        self.login()

    def validate(self):
        """Validate command input."""

    def execute(self):
        self.echo_debug("Retrieving projects")

        projects = []
        try:
            for projects_page in self.get_paginated_projects():
                if not projects_page:
                    self.echo_debug("No projects were found.")
                    return
                projects.extend(projects_page)

            augmented_projects = self.augment_projects_with_pipeline_capabilities(
                projects
            )  # noqa: E501

            for project in augmented_projects:
                self.echo_data(get_line(project, self.include_capability))
        except APIClientError as err:
            if err.status_code == 404:
                self.echo_error("No projects found.")
            raise

    def get_paginated_projects(self):
        """Paginate over all projects.

        Yields:
            paginated lists of projects
        """
        more = True
        next_link = None
        while more:
            self.echo_debug("Get projects page")
            resp = self.get_projects(next_link)

            yield resp.results
            next_link = resp.meta.next
            more = next_link is not None

    @backoff.on_exception(
        backoff.expo,
        (APIClientTimeout),
        max_tries=2,
        max_time=30,
    )
    def get_projects(self, next_link=None):
        """Get projects page."""
        hidden_status = HiddenStatus.VISIBLE.value
        if self.include_hidden:
            hidden_status = HiddenStatus.ALL.value
        return self.api_client.list_projects(next_link, hidden_status=hidden_status)

    @backoff.on_exception(
        backoff.expo,
        (APIClientTimeout),
        max_tries=3,
        max_time=30,
    )
    def search_pipeline_capabilities_by_ids(self, pipeline_ids, next_link=None):
        """Search pipeline capabilities by ids."""
        return self.api_client.search_pipeline_capabilities_by_ids(
            pipeline_ids, next_link
        )

    def augment_projects_with_pipeline_capabilities(self, projects):
        """Fetch pipeline capabilities and append it to the project.

        Args:
            projects (list[Project]): list of projects

        Returns:
            list[Project]: same list of projects with pipeline capabilities
                uuid replaced with PipelineCapability
        """
        pipeline_capabilities_ids = list(
            {str(project.pipeline_capabilities) for project in projects}
        )
        pipeline_capabilities = []
        next_link = None
        for pipeline_capabilities_id in range(0, len(pipeline_capabilities_ids), 50):
            resp = self.search_pipeline_capabilities_by_ids(
                pipeline_capabilities_ids[
                    pipeline_capabilities_id : pipeline_capabilities_id  # noqa: E203
                    + 50
                ],
                next_link=next_link,
            )
            pipeline_capabilities.extend(resp.results)
            next_link = resp.meta.next

        pipeline_capabilities_dict = {
            capability.id: capability for capability in pipeline_capabilities
        }
        for project in projects:
            project_dict = dict(project)
            project_dict["pipeline_capabilities"] = pipeline_capabilities_dict[
                project.pipeline_capabilities
            ]
            yield Project(**project_dict)
