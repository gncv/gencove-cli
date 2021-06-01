"""Gencove CLI models"""
from datetime import datetime
from typing import Any, List, Optional, Union
from uuid import UUID

from pydantic import BaseModel, HttpUrl  # pylint: disable=no-name-in-module


# pylint: disable=too-few-public-methods
class GencoveBaseModel(BaseModel):
    """Gencove Base Model"""

    id: UUID


class RefreshJWTResponse(BaseModel):
    """RefreshJWTResponse model"""

    access: str


class CreateJWTResponse(BaseModel):
    """CreateJWTResponse model"""

    access: str
    refresh: str


class VerifyJWTResponse(BaseModel):
    """VerifyJWTResponse model"""


class S3Object(BaseModel):
    """S3Object model"""

    bucket: str
    object_name: str


class StatusObject(BaseModel):
    """StatusObject model"""

    # Should migrate id to GencoveBaseModel,
    # current type are for tests compatibility
    id: Optional[Union[UUID, str]]
    status: str
    note: Optional[str]
    created: Optional[datetime]
    transition_cutoff: Optional[datetime]


class UploadsPostDataResponse(BaseModel):
    """UploadsPostDataResponse model"""

    # Should migrate id to GencoveBaseModel,
    # current type are for tests compatibility
    id: Optional[Union[UUID, str]]
    destination_path: Optional[str]
    s3: S3Object
    last_status: Optional[StatusObject]


class ResponseMeta(BaseModel):
    """ResponseMeta model"""

    count: Optional[int]
    next: Optional[str]
    previous: Optional[str]


# pylint: disable=too-few-public-methods
class PipelineCapabilities(GencoveBaseModel):
    """Pipeline Capabilities record"""

    name: Optional[str]
    private: Optional[bool]
    merge_vcfs_enabled: Optional[bool]


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
    webhook_url: Optional[HttpUrl]  # deprecated


class UploadCredentialsResponse(BaseModel):
    """UploadCredentialsResponse model"""

    version: int
    access_key: str
    secret_key: str
    token: str
    expiry_time: datetime


class SampleFile(GencoveBaseModel):
    """SampleFile model"""

    s3_path: str
    size: Optional[int]
    download_url: HttpUrl
    file_type: str


class SampleDetails(BaseModel):
    """SampleDetails model"""

    # Should migrate id to GencoveBaseModel,
    # current type are for tests compatibility
    id: Optional[Union[UUID, str]]
    created: Optional[datetime]
    modified: Optional[datetime]
    client_id: Optional[str]
    physical_id: Optional[str]
    legacy_id: Optional[str]
    last_status: Optional[StatusObject]
    archive_last_status: Optional[StatusObject]
    files: Optional[List[SampleFile]]


class GetProjectSamplesResponse(BaseModel):
    """GetProjectSamplesResponse model"""

    meta: ResponseMeta
    results: Optional[List[SampleDetails]]


class UploadCreate(BaseModel):
    """UploadCreate model"""

    upload: UUID


class Fastqs(BaseModel):
    """Fastqs model"""

    r1: UploadCreate
    r2: UploadCreate


class SampleSheetCreate(BaseModel):
    """SampleSheetCreate model"""

    client_id: UUID
    fastq: Fastqs


class CreateProjectSamplesResponse(BaseModel):
    """CreateProjectSamplesResponse model"""

    uploads: List[SampleSheetCreate]
    metadata: Optional[Any]


class QualityControlType(BaseModel):
    """QualityControlType model"""

    key: str
    type: str


class QualityControlSelf(BaseModel):
    """QualityControlSelf model"""

    value_expected: Optional[float]
    value_measured: Optional[float]
    status: str


class QualityControl(BaseModel):
    """QualityControl model"""

    quality_control_type: QualityControlType
    quality_control: QualityControlSelf


class SampleQCResponse(BaseModel):
    """SampleQCResponse model"""

    meta: ResponseMeta
    results: List[QualityControl]


class UploadNestedList(BaseModel):
    """UploadNestedList model"""

    upload: UUID
    destination_path: Optional[str]
    last_status: StatusObject


class UploadFastQ(BaseModel):
    """UploadFastQ model"""

    client_id: UUID
    fastq: UploadNestedList


class SampleSheetResponse(BaseModel):
    """SampleSheetResponse model"""

    meta: ResponseMeta
    results: Optional[List[UploadFastQ]]


class GetProjectsResponse(BaseModel):
    """GetProjectsResponse model"""

    meta: ResponseMeta
    results: Optional[List[Project]]


class BatchType(BaseModel):
    """BatchType model"""

    key: str
    description: str


class ProjectBatchTypesResponse(BaseModel):
    """ProjectBatchTypesResponse model"""

    meta: ResponseMeta
    results: Optional[List[BatchType]]


class BatchDetail(GencoveBaseModel):
    """BatchDetail model"""

    name: str
    batch_type: str
    sample_ids: Optional[List[UUID]]
    last_status: StatusObject
    files: List[SampleFile]


class GetProjectBatchesResponse(BaseModel):
    """GetProjectBatchesResponse model"""

    meta: ResponseMeta
    results: Optional[List[BatchDetail]]


class ProjectMergeVCFs(GencoveBaseModel):
    """ProjectMergeVCFs model"""

    created: datetime
    user: UUID
    last_status: StatusObject
    up_to_date: bool


class SampleMetadata(GencoveBaseModel):
    """SampleMetadata model"""

    metadata: Optional[Any]
