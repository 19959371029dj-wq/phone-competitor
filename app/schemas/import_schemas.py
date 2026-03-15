"""
Profile 上传、价格批量导入相关 schema。
"""
from decimal import Decimal
from pydantic import BaseModel, Field


# ---------- Profile 上传 ----------
class ProfileExtractPreview(BaseModel):
    """上传 profile 后解析出的预览数据。"""
    success: bool = True
    file_name: str = ""
    fields: dict[str, str | None] = Field(default_factory=dict)
    spec_items: list[dict] = Field(default_factory=list)
    message: str | None = None


class ProfileConfirmRequest(BaseModel):
    """用户确认写入数据库：可带修正后的字段。"""
    fields: dict[str, str | None] = Field(default_factory=dict)
    spec_items: list[dict] = Field(default_factory=list)


class ProfileConfirmResponse(BaseModel):
    success: bool
    product_id: int | None = None
    message: str


# ---------- 价格批量 ----------
class PriceRow(BaseModel):
    brand: str | None = None
    model: str | None = None
    full_name: str | None = None
    price: Decimal
    currency: str | None = None
    market_region: str | None = None
    sales_channel: str | None = None
    price_date: str | None = None


class PricePreviewRow(BaseModel):
    """单行预览：匹配结果。"""
    row_index: int
    brand: str | None = None
    model: str | None = None
    full_name: str | None = None
    price: Decimal
    currency: str | None = None
    match_status: str  # matched | no_match | duplicate
    matched_product_id: int | None = None
    matched_full_name: str | None = None


class PricePreviewResponse(BaseModel):
    success: bool = True
    total_rows: int = 0
    rows: list[PricePreviewRow] = []
    matched_count: int = 0
    no_match_count: int = 0
    duplicate_count: int = 0
    message: str | None = None


class PriceConfirmRequest(BaseModel):
    """确认执行价格更新：传预览时的 rows（或后端用 session/临时存储）。这里简化为前端再传一次解析后的 rows。"""
    rows: list[PricePreviewRow] = Field(default_factory=list)


class PriceConfirmResponse(BaseModel):
    success: bool
    batch_id: int | None = None
    updated_count: int = 0
    message: str


class ImportBatchSchema(BaseModel):
    id: int
    import_type: str
    file_name: str | None
    status: str | None
    summary: str | None
    created_at: str

    class Config:
        from_attributes = True
