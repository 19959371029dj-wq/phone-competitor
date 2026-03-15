"""
机型管理：GET/POST/PUT/DELETE products，列表筛选。
"""
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.phone import Product
from app.schemas.product import ProductListSchema, ProductDetailSchema, ProductCreate, ProductUpdate, ProductSpecItemSchema
from app.services import product_service as svc

router = APIRouter(prefix="/api/products", tags=["products"])


@router.get("/brands", response_model=dict)
def list_brands(db: Session = Depends(get_db)):
    """返回所有不重复的品牌列表，供竞品分析页筛选用。"""
    from sqlalchemy import distinct, select
    result = db.execute(select(distinct(Product.brand)).where(Product.brand.isnot(None), Product.brand != "").order_by(Product.brand))
    brands = [r[0] for r in result.fetchall()]
    return {"success": True, "data": brands}


@router.get("", response_model=dict)
def list_products(
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    brand: str | None = None,
    search: str | None = None,
    price_min: float | None = None,
    price_max: float | None = None,
    launch_year: str | None = None,
    order_by: str = "updated_at",
    desc: bool = True,
):
    """产品列表，支持搜索、筛选、排序。"""
    price_min_dec = Decimal(str(price_min)) if price_min is not None else None
    price_max_dec = Decimal(str(price_max)) if price_max is not None else None
    items, total = svc.list_products(
        db, skip=skip, limit=limit, brand=brand, search=search,
        price_min=price_min_dec, price_max=price_max_dec, launch_year=launch_year,
        order_by=order_by, desc=desc,
    )
    return {
        "success": True,
        "data": [ProductListSchema.model_validate(x) for x in items],
        "total": total,
    }


@router.get("/{product_id}", response_model=dict)
def get_product(product_id: int, db: Session = Depends(get_db)):
    """产品详情，含 spec_items。"""
    product = svc.get_product(db, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="产品不存在")
    return {"success": True, "data": ProductDetailSchema.model_validate(product)}


@router.post("", response_model=dict)
def create_product(body: ProductCreate, db: Session = Depends(get_db)):
    """新增产品。"""
    product = svc.create_product(db, body)
    return {"success": True, "data": ProductDetailSchema.model_validate(product), "id": product.id}


@router.put("/{product_id}", response_model=dict)
def update_product(product_id: int, body: ProductUpdate, db: Session = Depends(get_db)):
    """更新产品。"""
    product = svc.update_product(db, product_id, body)
    if not product:
        raise HTTPException(status_code=404, detail="产品不存在")
    return {"success": True, "data": ProductDetailSchema.model_validate(product)}


@router.delete("/{product_id}", response_model=dict)
def delete_product(product_id: int, db: Session = Depends(get_db)):
    """删除产品。"""
    ok = svc.delete_product(db, product_id)
    if not ok:
        raise HTTPException(status_code=404, detail="产品不存在")
    return {"success": True, "message": "已删除"}


@router.post("/{product_id}/duplicate", response_model=dict)
def duplicate_product(product_id: int, db: Session = Depends(get_db)):
    """复制机型为新记录。"""
    product = svc.duplicate_product(db, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="产品不存在")
    return {"success": True, "data": ProductDetailSchema.model_validate(product), "id": product.id}
