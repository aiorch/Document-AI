from pydantic import BaseModel
from typing import Optional, List

from pydantic import BaseModel
from typing import Optional, List

class RawMaterialDetail(BaseModel):
    s_no: Optional[int]
    raw_material: Optional[str]
    unit: Optional[str]
    standard_quantity: Optional[int]
    allowed_range: Optional[str]
    actual_quantity: Optional[int]
    in_house_b_no_ar_no: Optional[str]
    performed_by: Optional[str]
    checked_by: Optional[str]
    remarks: Optional[str]

class ReportPage1(BaseModel):
    product: Optional[str]
    stage: Optional[str]
    batch_no: Optional[str]
    batch_started_on: Optional[str]
    batch_completed_on: Optional[str]
    raw_material_details: Optional[List[RawMaterialDetail]]
    prepared_by: Optional[str]
    prepared_date: Optional[str]
    reviewed_by: Optional[str]
    reviewed_date: Optional[str]
    approved_by: Optional[str]
    approved_date: Optional[str]
    revision_no: Optional[str]
    effective_date: Optional[str]
    format_no: Optional[str]
    page: Optional[str]


from pydantic import BaseModel
from typing import Optional, List


class Equipment(BaseModel):
    s_no: Optional[int]
    name: Optional[str]
    id_no: Optional[str]


class RawMaterialMeasurement(BaseModel):
    op_no: Optional[int]
    initial_reading_l: Optional[int]
    final_reading_l: Optional[int]
    difference_l: Optional[int]


class ReportPage2(BaseModel):
    batch_no: Optional[str]
    list_of_equipments: Optional[List[Equipment]]
    raw_material_measuring_sheet: Optional[List[RawMaterialMeasurement]]
    prepared_by: Optional[str]
    reviewed_by: Optional[str]
    approved_by: Optional[str]
    sign_date_prepared_by: Optional[str]
    sign_date_reviewed_by: Optional[str]
    sign_date_approved_by: Optional[str]
    revision_no: Optional[str]
    effective_date: Optional[str]
    mfr_ref_no: Optional[str]
    format_no: Optional[str]
    page_info: Optional[str]


from pydantic import BaseModel
from typing import Optional, List

class OperationRecord(BaseModel):
    operation_number: Optional[int]
    description: Optional[str]
    equipment_number: Optional[str]
    date: Optional[str]
    time_from: Optional[str]
    time_to: Optional[str]
    duration: Optional[str]
    performed_by: Optional[str]
    checked_by: Optional[str]
    remarks: Optional[str]

class ReportPage3(BaseModel):
    batch_no: Optional[str]
    date: Optional[str]
    op_records: List[OperationRecord]

# Example instantiation
example_data = ReportPage3(
    batch_no="GP/08/2024/0018",
    date="26/08/24",
    op_records=[
        OperationRecord(
            operation_number=1,
            description="Check the cleanliness of the reactor.",
            equipment_number="GLRE-1010",
            date="26/08/24",
            time_from="16:00",
            time_to="17:40",
            duration=None,
            performed_by="X",
            checked_by="Q",
            remarks="-"
        ),
        # Add more OperationRecords as needed...
    ]
)


class Report(BaseModel):
    page_1: Optional[ReportPage1] = None
    page_2: Optional[ReportPage2] = None
    page_3: Optional[ReportPage3] = None
