from pydantic import BaseModel
from typing import List, Optional

class VerificationDetail(BaseModel):
    item_no: str
    description: str
    yes: bool
    no: bool
    na: bool

class BPRReviewChecklist(BaseModel):
    department: str
    format_no: str
    format_title: str
    revision_no: str
    effective_date: str
    review_date: str
    product_stage: str
    batch_no: str
    verification_details: List[VerificationDetail]
    reviewed_by: str
    reviewed_date: str
    approved_by: str
    approved_date: str
    qa_review: Optional[str] = None

# Example data structure that could be filled in based on this page's content
checklist_data = BPRReviewChecklist(
    department="QUALITY ASSURANCE",
    format_no="QSP-021/F-004",
    format_title="BPR REVIEW CHECKLIST",
    revision_no="00",
    effective_date="12-05-2023",
    review_date="April 2023",
    product_stage="Ranitidine HCl RH",
    batch_no="RH/08 2024 0574",
    verification_details=[
        VerificationDetail(item_no="1.0", description="Is the Batch production record issued by QA?", yes=True, no=False, na=False),
        VerificationDetail(item_no="2.0", description="Are raw material input weights, in-house batch nos./A.R.Nos. recorded?", yes=True, no=False, na=False),
        # Add other items similarly
    ],
    reviewed_by="Officer-Production/Designee",
    reviewed_date="09/09/24",
    approved_by="Head-Production/Designee",
    approved_date="10/08/24",
    qa_review="QA Review"
)