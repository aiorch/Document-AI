from typing import Optional, List
from pydantic import BaseModel, Field
from src.page_loaders.page15to16 import AnalyticalTestReport
from datetime import datetime

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

class YieldReport(BaseModel):
    product_name: str = Field(description="Name of the product (e.g., Ranitidine HCI)")
    expected_yield_min: float = Field(description="Minimum expected yield in kg")
    expected_yield_max: float = Field(description="Maximum expected yield in kg")
    actual_yield: float = Field(description="Actual yield in kg")
    sample_quantity: float = Field(description="Sample quantity in grams")
    balance_quantity: float = Field(
        description="Balance quantity in kg (Actual yield - Sample quantity)"
    )
    deviations: Optional[str] = Field(description="Deviations or delays, if any")
    compiled_by: str = Field(description="Name of the person who compiled the report")
    compiled_date: datetime = Field(description="Date when the report was compiled")
    checked_by: str = Field(description="Name of the person who checked the report")
    checked_date: datetime = Field(description="Date when the report was checked")

class DrumMeasurement(BaseModel):
    drum_no: int = Field(description="Drum number")
    tare_wt: Optional[float] = Field(description="Tare weight of the drum in kg")
    gross_wt: Optional[float] = Field(description="Gross weight of the drum in kg")
    net_wt: Optional[float] = Field(description="Net weight of the drum in kg")


class WeighingSheet(BaseModel):
    measurements: List[DrumMeasurement] = Field(description="List of drum measurements")
    total_weight: Optional[float] = Field(
        description="Total weight from the bottom of the sheet"
    )
    weighed_by: Optional[str] = Field(
        description="Name of the person who weighed the samples"
    )


class RawMaterialMeasurement(BaseModel):
    id: str = Field(description="ID of the raw material. Example: PA (SSRC 1102)")
    op_no: int = Field(description="Operation number (Op. No.)")
    initial_volume: float = Field(description="Initial volume (L)")
    final_volume: float = Field(description="Final volume (L)")
    difference_volume: float = Field(description="Difference in volume (L)")


class RawMaterialSheet(BaseModel):
    measurements: List[RawMaterialMeasurement] = Field(
        description="List of raw material measurements for each operation"
    )


# Subtable for time and temperature records within certain manufacturing steps
class TemperatureRecord(BaseModel):
    time: str = Field(description="Time of the temperature recording")
    temp_c: float = Field(description="Temperature in Celsius")
    sign: Optional[str] = Field(
        description="Sign of the person recording the temperature"
    )


# Manufacturing Procedure Section
class ManufacturingStep(BaseModel):
    op_no: int = Field(description="Operation number")
    description: str = Field(description="Description of the operation")
    equipment_no: Optional[List[str]] = Field(
        description="Equipment numbers used in this operation"
    )
    date: Optional[datetime] = Field(description="Date of the operation")
    time_from: Optional[str] = Field(description="Start time of the operation")
    time_to: Optional[str] = Field(description="End time of the operation")
    duration: Optional[str] = Field(description="Duration of the operation")
    performed_by: str = Field(
        description="Name of the person who performed the operation"
    )
    checked_by: str = Field(description="Name of the person who checked the operation")
    remarks: Optional[str] = Field(description="Remarks for the operation")
    # Additional field for temperature records in operations like step 11 and 13
    temperature_records: Optional[List[TemperatureRecord]] = Field(
        description="List of temperature records with time, temp, and sign"
    )


class ManufacturingProcedure(BaseModel):
    steps: List[ManufacturingStep] = Field(
        description="List of steps in the manufacturing procedure"
    )


class MeasurementRecord(BaseModel):
    time: str = Field(description="Time of the measurement")
    hot_water_temp_c: Optional[float] = Field(
        description="Hot water temperature in Celsius"
    )
    vapor_temp_c: Optional[float] = Field(description="Vapor temperature in Celsius")
    rcvd_vacuum_mm_hg: Optional[int] = Field(description="RCVD vacuum in mm Hg")
    sign: Optional[str] = Field(
        description="Sign of the person recording the measurement"
    )


class MeasurementSection(BaseModel):
    measurements: list[MeasurementRecord] = Field(
        description="List of measurement records over time"
    )

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

class InspectionForm(BaseModel):
    # Page 1
    batch_details: Optional[BatchDetails] = Field(
        None, description="Details of the batch"
    )
    material_usage_table: Optional[MaterialUsageTable] = Field(
        None, description="Details of the material usage"
    )
    equipment_list: Optional[EquipmentList] = Field(
        None, description="List of equipment used"
    )
    approval_details: Optional[ApprovalDetails] = Field(
        None, description="Approval details at the bottom of the page"
    )
    document_metadata: Optional[DocumentMetadata] = Field(
        None, description="Metadata details at the bottom of the page"
    )

    # Page 2
    raw_material_sheet: Optional[RawMaterialSheet] = Field(
        None, description="Raw Material Weighing / Measuring Sheet details"
    )
    manufacturing_procedure: Optional[ManufacturingProcedure] = Field(
        None, description="Details of the manufacturing procedure"
    )
    measurement_section: Optional[MeasurementSection] = Field(
        None, description="Periodic measurements of temperature, vacuum, etc."
    )

    # Pages 4 to 8
    manufacturing_procedures: Optional[list[ManufacturingProcedure]] = Field(
        None, description="Details of the manufacturing procedures"
    )
    measurement_sections: Optional[list[MeasurementSection]] = Field(
        None, description="Periodic measurements of temperature, vacuum, etc."
    )

    # Page 9
    weighing_sheet: Optional[WeighingSheet] = Field(
        None, description="Weighing Sheet with drum measurements and total weight details"
    )

    # Page 10
    yield_report: Optional[YieldReport] = Field(
        None, description="Yield report including expected range, actual yield, sample quantity, and deviations"
    )

    # Page 11
    bpr_review_checklist: Optional[BPRReviewChecklist] = Field(
        None, description="BPR Review Checklist with verification details"
    )

    # Page 12
    raw_material_indent_form: Optional[RawMaterialIndentForm] = Field(
        None, description="Raw Material Indent Form with details of raw materials"
    )

    # Page 13
    analytical_test_requisition: Optional[AnalyticalTestRequisition] = Field(
        None, description="Analytical Test Requisition with details of the test"
    )

    # Page 14
    finished_product_sample_advice_sheet: Optional[FinishedProductSampleAdviceSheet] = Field(
        None, description="Finished Product Sample Advice Sheet with details of the sample"
    )

    # Pages 15 to 16
    analytical_test_report: Optional[AnalyticalTestReport] = Field(
        None, description="Analytical Test Report with details of the test"
    )

    bpr_review_checklist: Optional[BPRReviewChecklist] = Field(
        None, description="BPR Review Checklist with verification details"
    )
