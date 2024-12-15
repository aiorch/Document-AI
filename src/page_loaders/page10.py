from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


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
