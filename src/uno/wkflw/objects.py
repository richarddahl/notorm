# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

from typing import Optional, List, Dict, Any
from typing_extensions import Self
from datetime import datetime
from pydantic import model_validator

from uno.obj import UnoObj
from uno.schema import UnoSchemaConfig
from uno.auth.mixins import DefaultObjectMixin
from uno.meta.objects import MetaTypeModel, MetaRecordModel, MetaType, MetaRecord
from uno.wkflw.models import (
    WorkflowModel,
    WorkflowStepModel,
    WorkflowTransitionModel,
    WorkflowInstanceModel,
    WorkflowTaskModel,
)
from uno.auth.objects import User


class MetaType(UnoObj[MetaTypeModel]):
    # Class variables
    model = MetaTypeModel
    schema_configs = {
        "view_schema": UnoSchemaConfig(),
        "edit_schema": UnoSchemaConfig(),
    }
    endpoints = ["List"]

    id: str

    def __str__(self) -> str:
        return f"{self.id}"


class MetaRecord(UnoObj[MetaRecordModel]):
    # Class variables
    model = MetaRecordModel
    schema_configs = {
        "view_schema": UnoSchemaConfig(),
        "edit_schema": UnoSchemaConfig(),
    }
    endpoints = ["List"]

    id: str
    meta_type_id: str

    def __str__(self) -> str:
        return f"{self.meta_type_id}: {self.id}"


class WorkflowStep(UnoObj[WorkflowStepModel], DefaultObjectMixin):
    # Class variables
    model = WorkflowStepModel
    schema_configs = {
        "view_schema": UnoSchemaConfig(
            exclude_fields=[
                "created_by",
                "modified_by",
                "deleted_by",
                "group",
                "tenant",
                "workflow",
            ],
        ),
        "edit_schema": UnoSchemaConfig(
            include_fields=[
                "name",
                "description",
                "step_type",
                "workflow_id",
                "is_start",
                "is_end",
                "config",
            ],
        ),
    }
    terminate_filters = True

    # Fields
    name: str
    description: Optional[str] = None
    step_type: str  # manual, automatic, approval, notification
    workflow_id: str
    workflow: Optional["Workflow"] = None
    is_start: bool = False
    is_end: bool = False
    config: Dict[str, Any] = {}

    def __str__(self) -> str:
        return self.name

    @model_validator(mode="after")
    def validate_step(self) -> Self:
        # Validate step_type is one of the allowed types
        allowed_types = ["manual", "automatic", "approval", "notification"]
        if self.step_type not in allowed_types:
            raise ValueError(f"Step type must be one of: {', '.join(allowed_types)}")

        return self


class WorkflowTransition(UnoObj[WorkflowTransitionModel], DefaultObjectMixin):
    # Class variables
    model = WorkflowTransitionModel
    schema_configs = {
        "view_schema": UnoSchemaConfig(
            exclude_fields=[
                "created_by",
                "modified_by",
                "deleted_by",
                "group",
                "tenant",
                "workflow",
                "from_step",
                "to_step",
            ],
        ),
        "edit_schema": UnoSchemaConfig(
            include_fields=[
                "name",
                "description",
                "workflow_id",
                "from_step_id",
                "to_step_id",
                "condition",
            ],
        ),
    }
    terminate_filters = True

    # Fields
    name: str
    description: Optional[str] = None
    workflow_id: str
    workflow: Optional["Workflow"] = None
    from_step_id: str
    from_step: Optional[WorkflowStep] = None
    to_step_id: str
    to_step: Optional[WorkflowStep] = None
    condition: Optional[str] = None  # Python expression

    def __str__(self) -> str:
        return self.name


class Workflow(UnoObj[WorkflowModel], DefaultObjectMixin):
    # Class variables
    model = WorkflowModel
    schema_configs = {
        "view_schema": UnoSchemaConfig(
            exclude_fields=[
                "created_by",
                "modified_by",
                "deleted_by",
                "group",
                "tenant",
                "applicable_types",
            ],
        ),
        "edit_schema": UnoSchemaConfig(
            include_fields=[
                "name",
                "description",
                "version",
                "is_active",
                "applicable_type_ids",
            ],
        ),
    }
    terminate_filters = True

    # Fields
    name: str
    description: Optional[str] = None
    version: str = "1.0.0"
    is_active: bool = True
    applicable_type_ids: List[str] = []
    applicable_types: List[MetaType] = []
    steps: List[WorkflowStep] = []
    transitions: List[WorkflowTransition] = []

    def __str__(self) -> str:
        return f"{self.name} v{self.version}"


class WorkflowTask(UnoObj[WorkflowTaskModel], DefaultObjectMixin):
    # Class variables
    model = WorkflowTaskModel
    schema_configs = {
        "view_schema": UnoSchemaConfig(
            exclude_fields=[
                "created_by",
                "modified_by",
                "deleted_by",
                "group",
                "tenant",
                "instance",
                "step",
                "assigned_to",
            ],
        ),
        "edit_schema": UnoSchemaConfig(
            include_fields=[
                "title",
                "description",
                "instance_id",
                "step_id",
                "assigned_to_id",
                "due_date",
                "priority",
            ],
        ),
    }
    terminate_filters = True

    # Fields
    title: str
    description: Optional[str] = None
    instance_id: str
    instance: Optional["WorkflowInstance"] = None
    step_id: str
    step: Optional[WorkflowStep] = None
    assigned_to_id: Optional[str] = None
    assigned_to: Optional[User] = None
    due_date: Optional[datetime] = None
    priority: str = "medium"  # low, medium, high
    status: str = "pending"  # pending, in_progress, completed, cancelled
    completed_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None

    def __str__(self) -> str:
        return self.title

    @model_validator(mode="after")
    def validate_task(self) -> Self:
        # Validate priority is one of the allowed values
        allowed_priorities = ["low", "medium", "high"]
        if self.priority not in allowed_priorities:
            raise ValueError(
                f"Priority must be one of: {', '.join(allowed_priorities)}"
            )

        # Validate status is one of the allowed values
        allowed_statuses = ["pending", "in_progress", "completed", "cancelled"]
        if self.status not in allowed_statuses:
            raise ValueError(f"Status must be one of: {', '.join(allowed_statuses)}")

        return self


class WorkflowInstance(UnoObj[WorkflowInstanceModel], DefaultObjectMixin):
    # Class variables
    model = WorkflowInstanceModel
    schema_configs = {
        "view_schema": UnoSchemaConfig(
            exclude_fields=[
                "created_by",
                "modified_by",
                "deleted_by",
                "group",
                "tenant",
                "workflow",
                "current_step",
                "record",
            ],
        ),
        "edit_schema": UnoSchemaConfig(
            include_fields=[
                "workflow_id",
                "record_type_id",
                "record_id",
            ],
        ),
    }
    terminate_filters = True

    # Fields
    workflow_id: str
    workflow: Optional[Workflow] = None
    record_type_id: str
    record_id: str
    record: Optional[MetaRecord] = None
    current_step_id: Optional[str] = None
    current_step: Optional[WorkflowStep] = None
    status: str = "active"  # active, completed, cancelled
    context: Dict[str, Any] = {}
    tasks: List[WorkflowTask] = []
    completed_at: Optional[datetime] = None

    def __str__(self) -> str:
        return (
            f"{self.workflow.name if self.workflow else 'Unknown'} - {self.record_id}"
        )

    @model_validator(mode="after")
    def validate_instance(self) -> Self:
        # Validate status is one of the allowed values
        allowed_statuses = ["active", "completed", "cancelled"]
        if self.status not in allowed_statuses:
            raise ValueError(f"Status must be one of: {', '.join(allowed_statuses)}")

        return self
