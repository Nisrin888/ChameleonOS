from pydantic import BaseModel


class DashboardSummary(BaseModel):
    total_impressions: int
    total_conversions: int
    overall_cvr: float
    control_cvr: float
    lift_vs_control: float


class PerformanceRow(BaseModel):
    traffic_source: str
    vibe: str
    variation_name: str
    variation_id: str
    impressions: int
    conversions: int
    cvr: float
    is_control: bool


class DashboardData(BaseModel):
    summary: DashboardSummary
    rows: list[PerformanceRow]
    last_updated: str
