from pydantic import BaseModel, Field
from typing import List

class RawMaterialDetail(BaseModel):
    s_no: int = Field(description="Serial number of the raw material entry")
    raw_material: str = Field(description="Name of the raw material")
    units: str = Field(description="Units of the material")
    quantity_indented: int = Field(description="Quantity indented")
    quantity_issued: int = Field(description="Quantity issued")
    ihb_no: str = Field(description="I.H.B. number")
    issued_by: str = Field(description="Person who issued the material")
    received_by: str = Field(description="Person who received the material")
    remarks: str = Field(description="Remarks regarding the issuance")

class RawMaterialIndentForm(BaseModel):
    department: str = Field(description="Department name")
    format_no: str = Field(description="Format number")
    format_title: str = Field(description="Title of the format")
    revision_no: str = Field(description="Revision number")
    effective_date: str = Field(description="Effective date of the form")
    review_date: str = Field(description="Review date of the form")
    rmi_no: str = Field(description="RMI number")
    date: str = Field(description="Date of the form")
    requested_by: str = Field(description="Person who requested the materials")
    department_requested: str = Field(description="Department that requested the materials")
    raw_material_details: List[RawMaterialDetail] = Field(description="List of raw material details")
    department_incharge: str = Field(description="Signature of the department incharge")
    stores_incharge: str = Field(description="Signature of the stores incharge")
