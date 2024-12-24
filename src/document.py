from typing import Optional
from pydantic import BaseModel, Field

# Import your page loader classes
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


