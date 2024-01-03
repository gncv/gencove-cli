"""Gencove CLI models"""
from datetime import datetime
from typing import Any, List, Optional, Union
from uuid import UUID

from pydantic import BaseModel, HttpUrl, validator


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

    bucket: Optional[str]
    object_name: Optional[str]


class GencoveStatus(GencoveBaseModel):
    """GencoveStatus model"""

    status: Optional[str]
    note: Optional[str]
    created: Optional[datetime]
    transition_cutoff: Optional[datetime]


class UploadsPostData(GencoveBaseModel):
    """UploadsPostData model"""

    destination_path: Optional[str]
    s3: Optional[S3Object]
    last_status: Optional[GencoveStatus]


class ResponseMeta(BaseModel):
    """ResponseMeta model"""

    count: Optional[int]
    next: Optional[str]
    previous: Optional[str]


# pylint: disable=too-few-public-methods
class PipelineCapabilities(GencoveBaseModel):
    """Pipeline Capabilities record"""

    id: UUID
    name: Optional[str]
    key: Optional[str]


class SampleFile(GencoveBaseModel):
    """SampleFile model"""

    s3_path: Optional[str]
    size: Optional[int]
    download_url: Optional[HttpUrl]
    file_type: Optional[str]
    checksum_sha256: Optional[str]


# pylint: disable=too-few-public-methods
class Project(GencoveBaseModel):
    """Project record"""

    name: Optional[str]
    description: Optional[str]
    created: Optional[datetime]
    organization: Optional[str]
    sample_count: Optional[int]
    pipeline_capabilities: Optional[Union[UUID, PipelineCapabilities]]
    roles: Optional[dict]
    webhook_url: Optional[Union[HttpUrl, str]]  # deprecated
    files: Optional[List[SampleFile]]


class AWSCredentials(BaseModel):
    """Generic AWS credentials model"""

    version: Optional[int]
    access_key: Optional[str]
    secret_key: Optional[str]
    token: Optional[str]
    expiry_time: Optional[str]  # needs to be str for boto3 to work


class ExplorerDataCredentials(AWSCredentials):
    """AWS Credentials for Explorer data commands"""

    region_name: Optional[str]


class SampleDetails(GencoveBaseModel):
    """SampleDetails model"""

    created: Optional[datetime]
    modified: Optional[datetime]
    run: Optional[str]
    client_id: Optional[str]
    physical_id: Optional[str]
    legacy_id: Optional[str]
    last_status: Optional[GencoveStatus]
    archive_last_status: Optional[GencoveStatus]
    files: Optional[List[SampleFile]]


class ProjectSamples(BaseModel):
    """ProjectSamples model"""

    meta: ResponseMeta
    results: Optional[List[SampleDetails]]


class Upload(BaseModel):
    """Upload model"""

    upload: Optional[UUID]
    destination_path: Optional[str]
    last_status: Optional[GencoveStatus]


class Fastqs(BaseModel):
    """Fastqs model"""

    r1: Optional[Upload]
    r2: Optional[Upload]


class Sample(BaseModel):
    """Sample model"""

    client_id: Optional[str]
    fastq: Optional[Fastqs]
    sample: Optional[UUID]


class SampleSheet(BaseModel):
    """SampleSheet model"""

    meta: ResponseMeta
    results: Optional[List[Sample]]


class UploadSamples(BaseModel):
    """UploadSamples model"""

    uploads: Optional[List[Sample]]
    metadata: Optional[Any]


class QualityControlType(BaseModel):
    """QualityControlType model"""

    key: Optional[str]
    type: Optional[str]


class QualityControlData(BaseModel):
    """QualityControlData model"""

    value_expected: Optional[float]
    value_measured: Optional[float]
    value_string: Optional[str]
    status: Optional[str]

    @validator("value_string", pre=True)
    def blank_string(
        cls, value: str  # noqa: N805
    ):  # pylint: disable=no-self-argument,no-self-use
        """Validator for value_string field, return None in case of empty string"""
        if value == "":
            return None
        return value


class QualityControl(BaseModel):
    """QualityControl model"""

    quality_control_type: Optional[QualityControlType]
    quality_control: Optional[QualityControlData]


class SampleQC(BaseModel):
    """SampleQC model"""

    meta: ResponseMeta
    results: Optional[List[QualityControl]]


class ClientFastQ(BaseModel):
    """ClientFastQ model"""

    client_id: Optional[str]
    fastq: Optional[Upload]


class UploadFastQ(BaseModel):
    """UploadFastQ model"""

    meta: ResponseMeta
    results: Optional[List[ClientFastQ]]


class Projects(BaseModel):
    """Projects model"""

    meta: ResponseMeta
    results: Optional[List[Project]]


class BatchType(BaseModel):
    """BatchType model"""

    key: Optional[str]
    description: Optional[str]


class ProjectBatchTypes(BaseModel):
    """ProjectBatchTypes model"""

    meta: ResponseMeta
    results: Optional[List[BatchType]]


class BatchDetail(GencoveBaseModel):
    """BatchDetail model"""

    name: Optional[str]
    batch_type: Optional[str]
    sample_ids: Optional[List[UUID]]
    last_status: Optional[GencoveStatus]
    files: Optional[List[SampleFile]]


class ProjectBatches(BaseModel):
    """ProjectBatches model"""

    meta: ResponseMeta
    results: Optional[List[BatchDetail]]


class ProjectMergeVCFs(GencoveBaseModel):
    """ProjectMergeVCFs model"""

    created: Optional[datetime]
    user: Optional[UUID]
    last_status: Optional[GencoveStatus]
    up_to_date: Optional[bool]


class SampleMetadata(BaseModel):
    """SampleMetadata model"""

    metadata: Optional[Any]


class BaseSpaceProjectDetail(BaseModel):
    """BaseSpace project detail model"""

    basespace_id: Optional[str]
    basespace_name: Optional[str]
    basespace_date_created: Optional[datetime]


class BaseSpaceProject(BaseModel):
    """BaseSpace project model"""

    meta: ResponseMeta
    results: Optional[List[BaseSpaceProjectDetail]]


class BaseSpaceBiosampleDetail(BaseModel):
    """BaseSpace Biosample detail model"""

    basespace_id: Optional[str]
    basespace_bio_sample_name: Optional[str]
    basespace_date_created: Optional[datetime]


class BaseSpaceBiosample(BaseModel):
    """BaseSpace Biosample model"""

    meta: ResponseMeta
    results: Optional[List[BaseSpaceBiosampleDetail]]


class BaseSpaceProjectImportDetail(GencoveBaseModel):
    """BaseSpace project import detail model"""

    project_id: UUID
    identifier: str
    metadata: Optional[Any]


class BaseSpaceProjectImport(BaseModel):
    """BaseSpace project import model"""

    meta: ResponseMeta
    results: Optional[List[BaseSpaceProjectImportDetail]]


class S3AutoimportTopic(GencoveBaseModel):
    """S3 autoimport topic"""

    topic_arn: str


class S3ProjectImportDetail(GencoveBaseModel):
    """S3 project import detail model"""

    project_id: UUID
    s3_uri: str
    metadata: Optional[Any]


class S3ProjectImport(BaseModel):
    """S3 project import model"""

    meta: ResponseMeta
    results: Optional[List[S3ProjectImportDetail]]


class SampleImport(BaseModel):
    """Existing sample import model"""

    sample_id: UUID
    client_id: Optional[str]


class ImportExistingSamplesModel(BaseModel):
    """Import existing samples model"""

    project_id: UUID
    samples: List[SampleImport]
    metadata: Optional[Any]


class FileType(BaseModel):
    """FileType model"""

    key: Optional[str]
    description: Optional[str]


class FileTypesModel(BaseModel):
    """File types model"""

    meta: ResponseMeta
    results: Optional[List[FileType]]


class Pipeline(GencoveBaseModel):
    """Pipeline model"""

    version: str


class PipelineDetail(Pipeline):
    """Pipeline detail model"""

    capabilities: List[PipelineCapabilities]


class Pipelines(BaseModel):
    """Pipeline model"""

    meta: ResponseMeta
    results: Optional[List[Pipeline]]


class UploadURLImport(GencoveBaseModel):
    """URL import moodel"""

    s3: Optional[S3Object]
    last_status: Optional[GencoveStatus]
    destination_path: Optional[str]
    source_url: Optional[str]


class File(GencoveBaseModel):
    """File model"""

    s3_path: Optional[str]
    size: Optional[int]
    download_url: Optional[str]
    file_type: Optional[str]
    checksum_sha256: Optional[str]


class SampleManifest(GencoveBaseModel):
    """Sample manifest model"""

    file_name: str
    file: Optional[File]
    project: UUID


class SampleManifests(BaseModel):
    """Sample manifests list model"""

    results: List[SampleManifest]


class ExplorerInstance(BaseModel):
    """ExplorerInstance model"""

    id: UUID
    status: str
    stop_after_inactivity_hours: Optional[int]


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
    stop_after_inactivity_hours: Optional[int]


class ExplorerInstanceInactivityStopOrganization(BaseModel):
    """ExplorerInstanceInactivityStopOrganization model"""

    explorer_override_stop_after_inactivity_hours: bool
    explorer_stop_after_inactivity_hours: int


class ExplorerShellSessionCredentials(BaseModel):
    """ExplorerShellSessionCredentials model"""

    version: Optional[int]
    access_key: Optional[str]
    secret_key: Optional[str]
    token: Optional[str]
    expiry_time: Optional[str]  # needs to be str for boto3 to work
    region_name: Optional[str]
    ec2_instance_id: Optional[str]
    shell_session_ssm_document_name: Optional[str]
    network_activity_ssm_document_name: Optional[str]


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
