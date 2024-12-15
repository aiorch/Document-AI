from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


# Raw Material Weighing / Measuring Sheet Section
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
