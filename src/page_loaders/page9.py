from typing import List, Optional

from pydantic import BaseModel, Field


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
