"""
手机产品参数与竞品分析 - 数据模型。
表：products, product_spec_items, price_history, import_batches, comparison_reports。
"""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from sqlalchemy import DateTime, ForeignKey, Numeric, String, Text, Integer, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Product(Base):
    """产品主表：手机机型，来源可为 GSMArena 或上传 profile。"""

    __tablename__ = "phone_products"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    brand: Mapped[str | None] = mapped_column(String(100), nullable=True)
    model: Mapped[str | None] = mapped_column(String(200), nullable=True)
    full_name: Mapped[str | None] = mapped_column(String(500), nullable=True)
    slug: Mapped[str | None] = mapped_column(String(300), nullable=True, index=True)
    source_type: Mapped[str | None] = mapped_column(String(50), nullable=True)  # gsmarena | upload_profile
    source_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_site: Mapped[str | None] = mapped_column(String(100), nullable=True)
    launch_date: Mapped[str | None] = mapped_column(String(100), nullable=True)
    status: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # 系统/性能
    os: Mapped[str | None] = mapped_column(String(200), nullable=True)
    chipset: Mapped[str | None] = mapped_column(String(300), nullable=True)
    cpu: Mapped[str | None] = mapped_column(Text, nullable=True)
    gpu: Mapped[str | None] = mapped_column(String(300), nullable=True)

    # 屏幕
    display_type: Mapped[str | None] = mapped_column(String(200), nullable=True)
    display_size: Mapped[str | None] = mapped_column(String(100), nullable=True)
    resolution: Mapped[str | None] = mapped_column(String(200), nullable=True)
    refresh_rate: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # 电池与充电
    battery: Mapped[str | None] = mapped_column(String(200), nullable=True)
    charging: Mapped[str | None] = mapped_column(String(300), nullable=True)

    # 影像
    main_camera: Mapped[str | None] = mapped_column(Text, nullable=True)
    selfie_camera: Mapped[str | None] = mapped_column(Text, nullable=True)

    # 内存摘要
    memory_summary: Mapped[str | None] = mapped_column(String(300), nullable=True)

    # 价格与市场
    price: Mapped[Decimal | None] = mapped_column(Numeric(14, 2), nullable=True)
    currency: Mapped[str | None] = mapped_column(String(20), nullable=True)
    market_region: Mapped[str | None] = mapped_column(String(50), nullable=True)
    sales_channel: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # 原始数据
    raw_specs_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    raw_html: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False), server_default=func.now(), onupdate=func.now()
    )

    spec_items: Mapped[list["ProductSpecItem"]] = relationship(
        "ProductSpecItem", back_populates="product", cascade="all, delete-orphan", order_by="ProductSpecItem.sort_order"
    )
    price_histories: Mapped[list["PriceHistory"]] = relationship(
        "PriceHistory", back_populates="product", cascade="all, delete-orphan"
    )


class ProductSpecItem(Base):
    """规格明细：便于灵活展示与编辑。"""

    __tablename__ = "product_spec_items"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("phone_products.id", ondelete="CASCADE"), nullable=False)
    spec_group: Mapped[str | None] = mapped_column(String(100), nullable=True)
    spec_key: Mapped[str | None] = mapped_column(String(150), nullable=True)
    spec_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False), server_default=func.now(), onupdate=func.now()
    )

    product: Mapped["Product"] = relationship("Product", back_populates="spec_items")


class PriceHistory(Base):
    """价格历史：每次批量导入或单条更新可写一条。"""

    __tablename__ = "price_history"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("phone_products.id", ondelete="CASCADE"), nullable=False)
    price: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    currency: Mapped[str | None] = mapped_column(String(20), nullable=True)
    market_region: Mapped[str | None] = mapped_column(String(50), nullable=True)
    sales_channel: Mapped[str | None] = mapped_column(String(100), nullable=True)
    price_date: Mapped[str | None] = mapped_column(String(50), nullable=True)
    import_batch_id: Mapped[int | None] = mapped_column(ForeignKey("import_batches.id", ondelete="SET NULL"), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), server_default=func.now())

    product: Mapped["Product"] = relationship("Product", back_populates="price_histories")
    import_batch: Mapped["ImportBatch | None"] = relationship(
        "ImportBatch", back_populates="price_histories", foreign_keys=[import_batch_id]
    )


class ImportBatch(Base):
    """导入批次：价格批量导入、回滚用。"""

    __tablename__ = "import_batches"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    import_type: Mapped[str] = mapped_column(String(50), nullable=False)  # price_bulk
    file_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[str | None] = mapped_column(String(50), nullable=True)  # success | failed | rolled_back
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON 或文本摘要

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), server_default=func.now())

    price_histories: Mapped[list["PriceHistory"]] = relationship(
        "PriceHistory", back_populates="import_batch", foreign_keys="PriceHistory.import_batch_id"
    )


class ComparisonReport(Base):
    """对比分析报告：多机型 + AI 生成内容。"""

    __tablename__ = "comparison_reports"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str | None] = mapped_column(String(500), nullable=True)
    selected_product_ids: Mapped[str | None] = mapped_column(String(200), nullable=True)  # 逗号分隔 id
    report_markdown: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), server_default=func.now())