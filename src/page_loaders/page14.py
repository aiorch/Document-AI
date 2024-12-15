# src/page_loaders/page14.py

from pydantic import BaseModel, Field
from typing import Optional

class FinishedProductSampleAdviceSheet(BaseModel):
    department: str = Field(description="Department name")
    format_no: str = Field(description="Format number")
    format_title: str = Field(description="Title of the format")
    revision_no: str = Field(description="Revision number")
    effective_date: str = Field(description="Effective date of the form")
    review_date: str = Field(description="Review date of the form")
    sample_name: str = Field(description="Name of the sample")
    batch_no: str = Field(description="Batch number")
    manufacturing_date: str = Field(description="Manufacturing date")
    batch_quantity: str = Field(description="Quantity of the batch")
    number_of_containers: int = Field(description="Number of containers")
    mode_of_packing: str = Field(description="Mode of packing")
    test_requested: str = Field(description="Test(s) requested")
    requested_by: str = Field(description="Person who requested the sample")
    request_date: str = Field(description="Date the sample was requested")
    request_time: str = Field(description="Time the sample was requested")
    received_by: str = Field(description="Person who received the sample")
    received_date: str = Field(description="Date the sample was received")
    received_time: str = Field(description="Time the sample was received")
