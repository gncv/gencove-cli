"""Gencove CLI models"""
from datetime import datetime
from typing import Any, List, Optional, Union
from uuid import UUID

from pydantic import BaseModel, HttpUrl, field_validator


# pylint: disable=too-few-public-methods
class GencoveBaseModel(BaseModel):
    """Gencove Base Model"""

    id: UUID


class AccessJWT(BaseModel):
    """AccessJWT model"""

    access: str


class CreateJWT(AccessJWT):
    """CreateJWT model"""

    refresh: str


class S3Object(BaseModel):
    """S3Object model"""

    bucket: Optional[str] = None
    object_name: Optional[str] = None


class GencoveStatus(GencoveBaseModel):
    """GencoveStatus model"""

    status: Optional[str] = None
    note: Optional[str] = None
    created: Optional[datetime] = None
    transition_cutoff: Optional[datetime] = None


class UploadsPostData(GencoveBaseModel):
    """UploadsPostData model"""

    destination_path: Optional[str] = None
    s3: Optional[S3Object] = None
    last_status: Optional[GencoveStatus] = None


class ResponseMeta(BaseModel):
    """ResponseMeta model"""

    count: Optional[int] = None
    next: Optional[str] = None
    previous: Optional[str] = None


# pylint: disable=too-few-public-methods
class PipelineCapabilities(GencoveBaseModel):
    """Pipeline Capabilities record"""

    id: UUID
    name: Optional[str] = None
    key: Optional[str] = None


class SampleFile(GencoveBaseModel):
    """SampleFile model"""

    s3_path: Optional[str] = None
    size: Optional[int] = None
    download_url: Optional[HttpUrl] = None
    file_type: Optional[str] = None
    checksum_sha256: Optional[str] = None


# pylint: disable=too-few-public-methods
class Project(GencoveBaseModel):
    """Project record"""

    name: Optional[str] = None
    description: Optional[str] = None
    created: Optional[datetime] = None
    organization: Optional[str] = None
    sample_count: Optional[int] = None
    pipeline_capabilities: Optional[Union[UUID, PipelineCapabilities]] = None
    roles: Optional[dict] = None
    webhook_url: Optional[Union[HttpUrl, str]] = None  # deprecated
    files: Optional[List[SampleFile]] = None


class AWSCredentials(BaseModel):
    """Generic AWS credentials model"""

    version: Optional[int] = None
    access_key: Optional[str] = None
    secret_key: Optional[str] = None
    token: Optional[str] = None
    expiry_time: Optional[str] = None  # needs to be str for boto3 to work


class ExplorerDataCredentials(AWSCredentials):
    """AWS Credentials for Explorer data commands"""

    region_name: Optional[str] = None


class SampleDetails(GencoveBaseModel):
    """SampleDetails model"""

    created: Optional[datetime] = None
    modified: Optional[datetime] = None
    run: Optional[str] = None
    client_id: Optional[str] = None
    physical_id: Optional[str] = None
    legacy_id: Optional[str] = None
    last_status: Optional[GencoveStatus] = None
    archive_last_status: Optional[GencoveStatus] = None
    files: Optional[List[SampleFile]] = None


class ProjectSamples(BaseModel):
    """ProjectSamples model"""

    meta: ResponseMeta
    results: Optional[List[SampleDetails]] = None


class Upload(BaseModel):
    """Upload model"""

    upload: Optional[UUID] = None
    destination_path: Optional[str] = None
    last_status: Optional[GencoveStatus] = None


class Fastqs(BaseModel):
    """Fastqs model"""

    r1: Optional[Upload] = None
    r2: Optional[Upload] = None


class Sample(BaseModel):
    """Sample model"""

    client_id: Optional[str] = None
    fastq: Optional[Fastqs] = None
    sample: Optional[UUID] = None


class SampleSheet(BaseModel):
    """SampleSheet model"""

    meta: ResponseMeta
    results: Optional[List[Sample]] = None


class UploadSamples(BaseModel):
    """UploadSamples model"""

    uploads: Optional[List[Sample]] = None
    metadata: Optional[Any] = None


class QualityControlType(BaseModel):
    """QualityControlType model"""

    key: Optional[str] = None
    type: Optional[str] = None


class QualityControlData(BaseModel):
    """QualityControlData model"""

    value_expected: Optional[float] = None
    value_measured: Optional[float] = None
    value_string: Optional[str] = None
    status: Optional[str] = None

    @field_validator("value_string", mode="before")
    @classmethod
    def blank_string(
        cls, value: str  # noqa: N805
    ):  # pylint: disable=no-self-argument,no-self-use
        """Validator for value_string field, return None in case of empty string"""
        if value == "":
            return None
        return value


class QualityControl(BaseModel):
    """QualityControl model"""

    quality_control_type: Optional[QualityControlType] = None
    quality_control: Optional[QualityControlData] = None


class SampleQC(BaseModel):
    """SampleQC model"""

    meta: ResponseMeta
    results: Optional[List[QualityControl]] = None


class ClientFastQ(BaseModel):
    """ClientFastQ model"""

    client_id: Optional[str] = None
    fastq: Optional[Upload] = None


class UploadFastQ(BaseModel):
    """UploadFastQ model"""

    meta: ResponseMeta
    results: Optional[List[ClientFastQ]] = None


class Projects(BaseModel):
    """Projects model"""

    meta: ResponseMeta
    results: Optional[List[Project]] = None


class BatchType(BaseModel):
    """BatchType model"""

    key: Optional[str] = None
    description: Optional[str] = None


class ProjectBatchTypes(BaseModel):
    """ProjectBatchTypes model"""

    meta: ResponseMeta
    results: Optional[List[BatchType]] = None


class BatchDetail(GencoveBaseModel):
    """BatchDetail model"""

    name: Optional[str] = None
    batch_type: Optional[str] = None
    sample_ids: Optional[List[UUID]] = None
    last_status: Optional[GencoveStatus] = None
    files: Optional[List[SampleFile]] = None


class ProjectBatches(BaseModel):
    """ProjectBatches model"""

    meta: ResponseMeta
    results: Optional[List[BatchDetail]] = None


class ProjectMergeVCFs(GencoveBaseModel):
    """ProjectMergeVCFs model"""

    created: Optional[datetime] = None
    user: Optional[UUID] = None
    last_status: Optional[GencoveStatus] = None
    up_to_date: Optional[bool] = None


class SampleMetadata(BaseModel):
    """SampleMetadata model"""

    metadata: Optional[Any] = None


class BaseSpaceProjectDetail(BaseModel):
    """BaseSpace project detail model"""

    basespace_id: Optional[str] = None
    basespace_name: Optional[str] = None
    basespace_date_created: Optional[datetime] = None


class BaseSpaceProject(BaseModel):
    """BaseSpace project model"""

    meta: ResponseMeta
    results: Optional[List[BaseSpaceProjectDetail]] = None


class BaseSpaceBiosampleDetail(BaseModel):
    """BaseSpace Biosample detail model"""

    basespace_id: Optional[str] = None
    basespace_bio_sample_name: Optional[str] = None
    basespace_date_created: Optional[datetime] = None


class BaseSpaceBiosample(BaseModel):
    """BaseSpace Biosample model"""

    meta: ResponseMeta
    results: Optional[List[BaseSpaceBiosampleDetail]] = None


class BaseSpaceProjectImportDetail(GencoveBaseModel):
    """BaseSpace project import detail model"""

    project_id: UUID
    identifier: str
    metadata: Optional[Any] = None


class BaseSpaceProjectImport(BaseModel):
    """BaseSpace project import model"""

    meta: ResponseMeta
    results: Optional[List[BaseSpaceProjectImportDetail]] = None


class S3AutoimportTopic(GencoveBaseModel):
    """S3 autoimport topic"""

    topic_arn: str


class S3ProjectImportDetail(GencoveBaseModel):
    """S3 project import detail model"""

    project_id: UUID
    s3_uri: str
    metadata: Optional[Any] = None


class S3ProjectImport(BaseModel):
    """S3 project import model"""

    meta: ResponseMeta
    results: Optional[List[S3ProjectImportDetail]] = None


class SampleImport(BaseModel):
    """Existing sample import model"""

    sample_id: UUID
    client_id: Optional[str] = None


class ImportExistingSamplesModel(BaseModel):
    """Import existing samples model"""

    project_id: UUID
    samples: List[SampleImport]
    metadata: Optional[Any] = None


class SampleCopy(BaseModel):
    """Existing sample copy model"""

    sample_id: UUID
    client_id: Optional[str] = None


class CopyExistingSamplesModel(BaseModel):
    """Copy existing samples model"""

    project_id: UUID
    samples: List[SampleCopy]


class FileType(BaseModel):
    """FileType model"""

    key: Optional[str] = None
    description: Optional[str] = None


class FileTypesModel(BaseModel):
    """File types model"""

    meta: ResponseMeta
    results: Optional[List[FileType]] = None


class Pipeline(GencoveBaseModel):
    """Pipeline model"""

    version: str


class PipelineDetail(Pipeline):
    """Pipeline detail model"""

    capabilities: List[PipelineCapabilities]


class Pipelines(BaseModel):
    """Pipeline model"""

    meta: ResponseMeta
    results: Optional[List[Pipeline]] = None


class UploadURLImport(GencoveBaseModel):
    """URL import moodel"""

    s3: Optional[S3Object] = None
    last_status: Optional[GencoveStatus] = None
    destination_path: Optional[str] = None
    source_url: Optional[str] = None


class File(GencoveBaseModel):
    """File model"""

    s3_path: Optional[str] = None
    size: Optional[int] = None
    download_url: Optional[str] = None
    file_type: Optional[str] = None
    checksum_sha256: Optional[str] = None


class SampleManifest(GencoveBaseModel):
    """Sample manifest model"""

    file_name: str
    file: Optional[File] = None
    project: UUID


class SampleManifests(BaseModel):
    """Sample manifests list model"""

    results: List[SampleManifest]


class ExplorerInstance(BaseModel):
    """ExplorerInstance model"""

    id: UUID
    status: str
    stop_after_inactivity_hours: Optional[int] = None


class ExplorerInstanceIds(BaseModel):
    """ExplorerInstanceIds model"""

    instance_ids: List[UUID]


class ExplorerInstances(BaseModel):
    """ExplorerInstances model"""

    meta: ResponseMeta
    results: List[ExplorerInstance]


class ExplorerInstanceInactivityStop(BaseModel):
    """ExplorerInstanceInactivityStop model"""

    instance_ids: List[UUID]
    stop_after_inactivity_hours: Optional[int] = None


class ExplorerInstanceInactivityStopOrganization(BaseModel):
    """ExplorerInstanceInactivityStopOrganization model"""

    explorer_override_stop_after_inactivity_hours: bool
    explorer_stop_after_inactivity_hours: int


class ExplorerShellSessionCredentials(BaseModel):
    """ExplorerShellSessionCredentials model"""

    version: Optional[int] = None
    access_key: Optional[str] = None
    secret_key: Optional[str] = None
    token: Optional[str] = None
    expiry_time: Optional[str] = None  # needs to be str for boto3 to work
    region_name: Optional[str] = None
    ec2_instance_id: Optional[str] = None
    shell_session_ssm_document_name: Optional[str] = None
    network_activity_ssm_document_name: Optional[str] = None


class ExplorerAccessURL(BaseModel):
    """ExplorerAccessURL model"""

    url: str
    access_token_expiration: Optional[int] = None


class OrganizationDetails(GencoveBaseModel):
    """OrganizationDetails model"""

    id: UUID
    name: str
    expire_uploads_period_days: int
    archive_period_days: int
    archive_restore_period_days: int
    uploads_enabled: bool


class UserDetails(GencoveBaseModel):
    """UserDetails model"""

    id: UUID
    email: str
    name: str
    uploads_enabled: bool
    explorer_enabled: bool
    is_support: bool


class OrganizationUser(GencoveBaseModel):
    """OrganizationUser model"""

    id: UUID
    name: str
    email: str
    is_active: Optional[bool] = None
    has_mfa_device: Optional[bool] = None
    roles: Optional[dict] = None
    is_support: Optional[bool] = None


class OrganizationUsers(BaseModel):
    """OrganizationUsers model"""

    meta: ResponseMeta
    results: List[OrganizationUser]
