from pydantic import BaseModel, Field

from src.page_loaders.page1 import (ApprovalDetails, BatchDetails,
                                    DocumentMetadata, EquipmentList,
                                    MaterialUsageTable)
from src.page_loaders.page2 import (ManufacturingProcedure, MeasurementSection,
                                    RawMaterialSheet)
from src.page_loaders.page9 import WeighingSheet
from src.page_loaders.page10 import YieldReport
from src.page_loaders.page11 import BPRReviewChecklist
from src.page_loaders.page12 import RawMaterialIndentForm
from src.page_loaders.page13 import AnalyticalTestRequisition
from src.page_loaders.page14 import FinishedProductSampleAdviceSheet
from src.page_loaders.page15to16 import AnalyticalTestReport

class InspectionForm(BaseModel):
    # page 1
    batch_details: BatchDetails = Field(description="Details of the batch")
    material_usage_table: MaterialUsageTable = Field(
        description="Details of the material usage"
    )
    equipment_list: EquipmentList = Field(description="List of equipment used")
    approval_details: ApprovalDetails = Field(
        description="Approval details at the bottom of the page"
    )
    document_metadata: DocumentMetadata = Field(
        description="Metadata details at the bottom of the page"
    )

    # page 2
    raw_material_sheet: RawMaterialSheet = Field(
        description="Raw Material Weighing / Measuring Sheet details"
    )
    manufacturing_procedure: ManufacturingProcedure = Field(
        description="Details of the manufacturing procedure"
    )
    measurement_section: MeasurementSection = Field(
        description="Periodic measurements of temperature, vacuum, etc."
    )

    # page 4
    manufacturing_procedure: ManufacturingProcedure = Field(
        description="Details of the manufacturing procedure"
    )
    measurement_section: MeasurementSection = Field(
        description="Periodic measurements of temperature, vacuum, etc."
    )

    # page 5
    manufacturing_procedure: ManufacturingProcedure = Field(
        description="Details of the manufacturing procedure"
    )
    measurement_section: MeasurementSection = Field(
        description="Periodic measurements of temperature, vacuum, etc."
    )

    # page 6
    manufacturing_procedure: ManufacturingProcedure = Field(
        description="Details of the manufacturing procedure"
    )
    measurement_section: MeasurementSection = Field(
        description="Periodic measurements of temperature, vacuum, etc."
    )

    # page 7
    manufacturing_procedure: ManufacturingProcedure = Field(
        description="Details of the manufacturing procedure"
    )
    measurement_section: MeasurementSection = Field(
        description="Periodic measurements of temperature, vacuum, etc."
    )

    # page 8
    manufacturing_procedure: ManufacturingProcedure = Field(
        description="Details of the manufacturing procedure"
    )
    measurement_section: MeasurementSection = Field(
        description="Periodic measurements of temperature, vacuum, etc."
    )

    # page 9
    weighing_sheet: WeighingSheet = Field(
        description="Weighing Sheet with drum measurements and total weight details"
    )

    # page 10
    yield_report: YieldReport = Field(
        description="Yield report including expected range, actual yield, sample quantity, and deviations"
    )

    # page 11
    bpr_review_checklist: BPRReviewChecklist = Field(
        description="BPR Review Checklist with verification details"
    )

    # page 12
    raw_material_indent_form: RawMaterialIndentForm = Field(
        description="Raw Material Indent Form with details of raw materials"
    )

    # page 13
    analytical_test_requisition: AnalyticalTestRequisition = Field(
        description="Analytical Test Requisition with details of the test"
    )

    # page 14
    finished_product_sample_advice_sheet: FinishedProductSampleAdviceSheet = Field(
        description="Finished Product Sample Advice Sheet with details of the sample"
    )

    # page 15 to 16
    analytical_test_report: AnalyticalTestReport = Field(
        description="Analytical Test Report with details of the test"
    )