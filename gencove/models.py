"""Gencove CLI models"""
from datetime import datetime
from typing import List, Optional, Union
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


class UploadStatusObject(GencoveBaseModel):
    """UploadStatusObject model"""

    status: str
    note: str
    created: str


class UploadsPostDataResponse(GencoveBaseModel):
    """UploadsPostDataResponse model"""

    destination_path: str
    s3: S3Object
    last_status: UploadStatusObject


class ResponseMeta(BaseModel):
    """ResponseMeta model"""

    count: int
    next: Optional[str]
    previous: Optional[str]


# pylint: disable=too-few-public-methods
class PipelineCapabilities(GencoveBaseModel):
    """Pipeline Capabilities record"""

    name: Optional[str]
    private: Optional[str]
    merge_vcfs_enabled: Optional[str]


# pylint: disable=too-few-public-methods
class Project(GencoveBaseModel):
    """Project record"""

    name: Optional[str]
    description: Optional[str]
    created: Optional[datetime]
    organization: Optional[str]
    sample_count: Optional[int]
    pipeline_capabilities: Optional[Union[UUID, PipelineCapabilities]]
    webhook_url: Optional[HttpUrl]  # deprecated


class GetProjectSamplesResponse(BaseModel):
    """GetProjectSamplesResponse model"""

    meta: ResponseMeta
    result: Optional[List[Project]]
