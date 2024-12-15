from pydantic import BaseModel, Field
from typing import List, Optional

class TestDetail(BaseModel):
    s_no: int = Field(description="Serial number of the test entry")
    test: str = Field(description="Name of the test")
    specification: str = Field(description="Specification range for the test")
    results: str = Field(description="Results obtained for the test")

class AnalyticalTestRequisition(BaseModel):
    department: str = Field(description="Department name")
    atr_no: str = Field(description="ATR number")
    atr_title: str = Field(description="Title of the ATR")
    revision_no: str = Field(description="Revision number")
    effective_date: str = Field(description="Effective date of the form")
    review_date: str = Field(description="Review date of the form")
    product_name: str = Field(description="Name of the product")
    stage: str = Field(description="Stage of the product")
    test_name: str = Field(description="Name of the test")
    batch_no: str = Field(description="Batch number or lot number")
    department_requested: str = Field(description="Department that requested the test")
    requested_by: str = Field(description="Person who requested the test")
    request_date: str = Field(description="Date of the request")
    request_time: Optional[str] = Field(description="Time of the request", default=None)
    ar_no: str = Field(description="A.R. number")
    out_time: str = Field(description="Out time for the test sample")
    specification_ref_no: str = Field(description="Specification reference number")
    moa_ref_no: str = Field(description="MOA reference number")
    test_details: List[TestDetail] = Field(description="Details of each test conducted")
    compliance: bool = Field(description="Compliance status with specifications")
    tested_by: str = Field(description="Name of the person who tested the sample")
    test_date: str = Field(description="Date the test was conducted")
    checked_by: str = Field(description="Name of the person who checked and approved")
    checked_date: str = Field(description="Date of approval check")
