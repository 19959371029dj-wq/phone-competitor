"""
产品相关 Pydantic 模型：列表、详情、创建、更新。
"""
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field


class ProductSpecItemSchema(BaseModel):
    id: int | None = None
    spec_group: str | None = None
    spec_key: str | None = None
    spec_value: str | None = None
    sort_order: int = 0

    model_config = ConfigDict(from_attributes=True)


class ProductListSchema(BaseModel):
    """列表项：用于表格展示、筛选。"""
    id: int
    brand: str | None = None
    model: str | None = None
    full_name: str | None = None
    source_type: str | None = None
    price: Decimal | None = None
    currency: str | None = None
    launch_date: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProductDetailSchema(BaseModel):
    """详情：含主表字段 + spec_items。"""
    id: int
    brand: str | None = None
    model: str | None = None
    full_name: str | None = None
    slug: str | None = None
    source_type: str | None = None
    source_url: str | None = None
    source_site: str | None = None
    launch_date: str | None = None
    status: str | None = None
    os: str | None = None
    chipset: str | None = None
    cpu: str | None = None
    gpu: str | None = None
    display_type: str | None = None
    display_size: str | None = None
    resolution: str | None = None
    refresh_rate: str | None = None
    battery: str | None = None
    charging: str | None = None
    main_camera: str | None = None
    selfie_camera: str | None = None
    memory_summary: str | None = None
    price: Decimal | None = None
    currency: str | None = None
    market_region: str | None = None
    sales_channel: str | None = None
    raw_specs_json: str | None = None
    raw_html: str | None = None
    created_at: datetime
    updated_at: datetime
    spec_items: list[ProductSpecItemSchema] = []

    model_config = ConfigDict(from_attributes=True)


class ProductCreate(BaseModel):
    """创建产品：所有字段可选，便于从抓取或上传结果写入。"""
    brand: str | None = None
    model: str | None = None
    full_name: str | None = None
    slug: str | None = None
    source_type: str | None = None
    source_url: str | None = None
    source_site: str | None = None
    launch_date: str | None = None
    status: str | None = None
    os: str | None = None
    chipset: str | None = None
    cpu: str | None = None
    gpu: str | None = None
    display_type: str | None = None
    display_size: str | None = None
    resolution: str | None = None
    refresh_rate: str | None = None
    battery: str | None = None
    charging: str | None = None
    main_camera: str | None = None
    selfie_camera: str | None = None
    memory_summary: str | None = None
    price: Decimal | None = None
    currency: str | None = None
    market_region: str | None = None
    sales_channel: str | None = None
    raw_specs_json: str | None = None
    raw_html: str | None = None
    spec_items: list[ProductSpecItemSchema] = Field(default_factory=list)


class ProductUpdate(BaseModel):
    """更新产品：全部可选。"""
    brand: str | None = None
    model: str | None = None
    full_name: str | None = None
    slug: str | None = None
    source_type: str | None = None
    source_url: str | None = None
    source_site: str | None = None
    launch_date: str | None = None
    status: str | None = None
    os: str | None = None
    chipset: str | None = None
    cpu: str | None = None
    gpu: str | None = None
    display_type: str | None = None
    display_size: str | None = None
    resolution: str | None = None
    refresh_rate: str | None = None
    battery: str | None = None
    charging: str | None = None
    main_camera: str | None = None
    selfie_camera: str | None = None
    memory_summary: str | None = None
    price: Decimal | None = None
    currency: str | None = None
    market_region: str | None = None
    sales_channel: str | None = None
    raw_specs_json: str | None = None
    raw_html: str | None = None
    spec_items: list[ProductSpecItemSchema] | None = None
