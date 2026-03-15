"""
产品 CRUD、spec_items 维护、按 brand/model/full_name 查重。
"""
from decimal import Decimal
from typing import Any

from sqlalchemy.orm import Session

from app.models.phone import Product, ProductSpecItem
from app.schemas.product import ProductCreate, ProductUpdate, ProductSpecItemSchema


def _parse_price(value: Any) -> Decimal | None:
    """从字符串或数字解析为 Decimal。"""
    if value is None:
        return None
    if isinstance(value, Decimal):
        return value
    if isinstance(value, (int, float)):
        return Decimal(str(value))
    s = str(value).strip()
    if not s:
        return None
    # 去掉货币符号和空格，只保留数字和小数点
    import re
    m = re.search(r"[\d.,]+", s.replace(",", ""))
    if m:
        try:
            return Decimal(m.group(0).replace(",", ""))
        except Exception:
            pass
    return None


def list_products(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    brand: str | None = None,
    search: str | None = None,
    price_min: Decimal | None = None,
    price_max: Decimal | None = None,
    launch_year: str | None = None,
    order_by: str = "updated_at",
    desc: bool = True,
) -> tuple[list[Product], int]:
    """列表 + 筛选 + 排序，返回 (items, total_count)。"""
    q = db.query(Product)
    if brand:
        q = q.filter(Product.brand.ilike(f"%{brand}%"))
    from sqlalchemy import or_
    if search:
        q = q.filter(
            or_(
                Product.full_name.ilike(f"%{search}%"),
                Product.model.ilike(f"%{search}%"),
                Product.brand.ilike(f"%{search}%"),
            )
        )
    if price_min is not None:
        q = q.filter(Product.price >= price_min)
    if price_max is not None:
        q = q.filter(Product.price <= price_max)
    if launch_year:
        q = q.filter(Product.launch_date.ilike(f"%{launch_year}%"))
    total = q.count()
    order_col = getattr(Product, order_by, Product.updated_at)
    q = q.order_by(order_col.desc() if desc else order_col.asc())
    items = q.offset(skip).limit(limit).all()
    return items, total


def get_product(db: Session, product_id: int) -> Product | None:
    return db.query(Product).filter(Product.id == product_id).first()


def find_duplicate(db: Session, brand: str | None, model: str | None, full_name: str | None) -> Product | None:
    """按 brand+model 或 full_name 查找是否已有记录。"""
    if full_name:
        p = db.query(Product).filter(Product.full_name == full_name).first()
        if p:
            return p
    if brand and model:
        return db.query(Product).filter(
            Product.brand == brand,
            Product.model == model,
        ).first()
    return None


def create_product(db: Session, data: ProductCreate | dict) -> Product:
    """创建产品并写入 spec_items。"""
    if isinstance(data, dict):
        spec_items_data = data.pop("spec_items", [])
    else:
        spec_items_data = [s.model_dump() for s in data.spec_items]
        data = data.model_dump(exclude={"spec_items"})
    data = {k: v for k, v in data.items() if v is not None}
    if "price" in data and data["price"] is not None and not isinstance(data["price"], Decimal):
        data["price"] = _parse_price(data["price"])
    product = Product(**{k: v for k, v in data.items() if hasattr(Product, k)})
    db.add(product)
    db.flush()
    for i, s in enumerate(spec_items_data):
        item = ProductSpecItem(
            product_id=product.id,
            spec_group=s.get("spec_group"),
            spec_key=s.get("spec_key"),
            spec_value=s.get("spec_value"),
            sort_order=s.get("sort_order", i),
        )
        db.add(item)
    db.commit()
    db.refresh(product)
    return product


def update_product(db: Session, product_id: int, data: ProductUpdate | dict) -> Product | None:
    """更新产品；若传 spec_items 则先删后插。"""
    product = get_product(db, product_id)
    if not product:
        return None
    if isinstance(data, ProductUpdate):
        data = data.model_dump(exclude_unset=True)
    spec_items = data.pop("spec_items", None)
    if "price" in data and data["price"] is not None and not isinstance(data.get("price"), Decimal):
        data["price"] = _parse_price(data["price"])
    for k, v in data.items():
        if hasattr(product, k):
            setattr(product, k, v)
    if spec_items is not None:
        db.query(ProductSpecItem).filter(ProductSpecItem.product_id == product_id).delete()
        for i, s in enumerate(spec_items):
            item = ProductSpecItem(
                product_id=product_id,
                spec_group=s.get("spec_group"),
                spec_key=s.get("spec_key"),
                spec_value=s.get("spec_value"),
                sort_order=s.get("sort_order", i),
            )
            db.add(item)
    db.commit()
    db.refresh(product)
    return product


def delete_product(db: Session, product_id: int) -> bool:
    """删除产品。"""
    product = get_product(db, product_id)
    if not product:
        return False
    db.delete(product)
    db.commit()
    return True


def duplicate_product(db: Session, product_id: int) -> Product | None:
    """复制一条机型为新记录（去掉 id、created_at、updated_at）。"""
    product = get_product(db, product_id)
    if not product:
        return None
    data = {
        "brand": product.brand,
        "model": product.model,
        "full_name": (product.full_name or "") + " (副本)",
        "slug": None,
        "source_type": "manual",
        "source_url": None,
        "source_site": None,
        "launch_date": product.launch_date,
        "status": product.status,
        "os": product.os,
        "chipset": product.chipset,
        "cpu": product.cpu,
        "gpu": product.gpu,
        "display_type": product.display_type,
        "display_size": product.display_size,
        "resolution": product.resolution,
        "refresh_rate": product.refresh_rate,
        "battery": product.battery,
        "charging": product.charging,
        "main_camera": product.main_camera,
        "selfie_camera": product.selfie_camera,
        "memory_summary": product.memory_summary,
        "price": product.price,
        "currency": product.currency,
        "market_region": product.market_region,
        "sales_channel": product.sales_channel,
        "raw_specs_json": product.raw_specs_json,
        "raw_html": None,
        "spec_items": [{"spec_group": s.spec_group, "spec_key": s.spec_key, "spec_value": s.spec_value, "sort_order": s.sort_order} for s in product.spec_items],
    }
    return create_product(db, data)
