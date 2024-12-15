from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


# Batch Details Section
class BatchDetails(BaseModel):
    product_name: str = Field(description="Name of the product")
    stage: str = Field(description="Stage of the production")
    batch_no: str = Field(description="Batch number")
    batch_started_on: datetime = Field(description="Date when the batch was started")
    batch_completed_on: datetime = Field(
        description="Date when the batch was completed"
    )


# Material Usage Details Section
class MaterialUsageRow(BaseModel):
    raw_material: str = Field(description="Name of the raw material")
    unit: str = Field(description="Unit of measurement")
    standard_quantity: float = Field(description="Standard quantity of the material")
    allowed_range_min: float = Field(
        description="Minimum allowed range for the material"
    )
    allowed_range_max: float = Field(
        description="Maximum allowed range for the material"
    )
    actual_quantity: float = Field(description="Actual quantity used")
    in_house_batch_no: Optional[str] = Field(
        description="In-house batch number or A.R. No. (B. No. / A.R. No.)"
    )
    performed_by: str = Field(description="Person who performed the task")
    checked_by: str = Field(description="Person who checked the task")
    remarks: Optional[str] = Field(description="Any remarks for the material usage")


class MaterialUsageTable(BaseModel):
    rows: List[MaterialUsageRow] = Field(
        description="List of rows in the Material Usage table"
    )


# List of Equipment Section
class Equipment(BaseModel):
    serial_no: int = Field(description="Serial number of the equipment")
    name: str = Field(description="Name of the equipment")
    id_no: str = Field(description="ID number of the equipment")


class EquipmentList(BaseModel):
    equipments: List[Equipment] = Field(description="List of equipment used")


# Approval and Metadata Section
class ApprovalDetails(BaseModel):
    prepared_by: str = Field(
        description="Name and designation of the person who prepared the document"
    )
    reviewed_by: str = Field(
        description="Name and designation of the person who reviewed the document"
    )
    approved_by: str = Field(
        description="Name and designation of the person who approved the document"
    )


class DocumentMetadata(BaseModel):
    revision_no: str = Field(description="Revision number of the document")
    effective_date: datetime = Field(description="Effective date of the document")
    mfr_ref_no: str = Field(description="MFR reference number")
    format_no: str = Field(description="Format number of the document")
