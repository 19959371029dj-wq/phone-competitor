"""
多机型对比与 AI 报告 schema。
"""
from pydantic import BaseModel, Field


class CompareTableRequest(BaseModel):
    product_ids: list[int] = Field(..., min_length=2, max_length=10)


class CompareTableResponse(BaseModel):
    """结构化参数对比表：行 = 参数名，列 = 机型。"""
    success: bool = True
    product_headers: list[dict] = []  # [{ id, full_name, brand, model }]
    rows: list[dict] = []  # [{ spec_key, spec_group, values: [v1, v2, ...] }]
    message: str | None = None


class CompareReportRequest(BaseModel):
    product_ids: list[int] = Field(..., min_length=2, max_length=10)


class CompareReportResponse(BaseModel):
    success: bool
    report_markdown: str | None = None
    report_id: int | None = None
    message: str | None = None
