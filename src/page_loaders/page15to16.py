# src/page_loaders/page15.py

from pydantic import BaseModel, Field
from typing import List, Optional

class TestSpecification(BaseModel):
    s_no: str = Field(description="Serial number of the test")
    test: str = Field(description="Name of the test")
    specification: str = Field(description="Specification details of the test")
    result: str = Field(description="Result of the test")

class AnalyticalTestReport(BaseModel):
    department: str = Field(description="Department name")
    atr_no: str = Field(description="ATR number")
    atr_title: str = Field(description="Title of the ATR")
    revision_no: str = Field(description="Revision number")
    effective_date: str = Field(description="Effective date of the report")
    review_date: str = Field(description="Review date of the report")
    specification_ref_no: str = Field(description="Specification reference number")
    moa_ref_no: str = Field(description="MOA reference number")
    sample_name: str = Field(description="Name of the sample")
    batch_no: str = Field(description="Batch number")
    manufacturing_date: str = Field(description="Manufacturing date")
    expiry_date: str = Field(description="Expiry date or retest date")
    quantity: str = Field(description="Quantity of the sample")
    number_of_containers: int = Field(description="Number of containers")
    ar_no: str = Field(description="A.R. number")
    test_specifications: List[TestSpecification] = Field(description="List of test specifications and results")
    
    # New field for customer specified requirements
    customer_specified_requirements: Optional[str] = Field(description="Customer specified requirements, if any", default=None)
    
    # Approval section
    complied_by: str = Field(description="Person who complied with the test requirements")
    complied_date: str = Field(description="Date of compliance")
    checked_by: str = Field(description="Person who checked the results")
    checked_date: str = Field(description="Date of check")
    approved_by: str = Field(description="Person who approved the results")
    approved_date: str = Field(description="Date of approval")

class BPRReviewChecklistEntry(BaseModel):
    serial_no: str = Field(description="Serial number of the verification item")
    verification_details: str = Field(description="Description of the verification item")
    status_yes: Optional[bool] = Field(default=False, description="Whether the item is marked 'Yes'")
    status_no: Optional[bool] = Field(default=False, description="Whether the item is marked 'No'")
    status_na: Optional[bool] = Field(default=False, description="Whether the item is marked 'N/A'")

class BPRReviewChecklist(BaseModel):
    department: str = Field(description="Department name")
    revision_no: Optional[str] = Field(description="Revision number")
    format_no: str = Field(description="Format number of the checklist")
    effective_date: str = Field(description="Effective date of the checklist")
    review_date: Optional[str] = Field(description="Review date of the checklist")
    product_stage: str = Field(description="Product or stage name")
    batch_no: str = Field(description="Batch number")

    # Entries for verification details
    verification_items: List[BPRReviewChecklistEntry] = Field(description="List of verification items with statuses")

    # Review and Approval Details
    reviewed_by: str = Field(description="Name of the person who reviewed the checklist")
    reviewed_date: str = Field(description="Date of review")
    approved_by: str = Field(description="Name of the person who approved the checklist")
    approved_date: str = Field(description="Date of approval")
    qa_review: Optional[str] = Field(default=None, description="QA review remarks or stamp details")
