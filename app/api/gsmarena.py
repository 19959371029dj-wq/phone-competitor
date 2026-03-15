"""
GSMArena 搜索与导入。
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.gsmarena import GsmArenaSearchResponse, GsmArenaImportRequest, GsmArenaImportResponse
from app.services import gsmarena_service as gsm
from app.services import product_service as psvc
from app.models.phone import Product, ProductSpecItem

router = APIRouter(prefix="/api/gsmarena", tags=["gsmarena"])


@router.get("/search", response_model=dict)
def search(q: str = Query(..., min_length=1)):
    """搜索机型，返回候选列表。"""
    success, results, msg = gsm.search_phones(q)
    if not success:
        return {"success": False, "query": q, "results": [], "message": msg}
    return {"success": True, "query": q, "results": results, "message": None}


@router.post("/import", response_model=dict)
def import_phone(
    body: GsmArenaImportRequest,
    db: Session = Depends(get_db),
    duplicate_action: str | None = None,  # overwrite | new_version | cancel
):
    """
    根据详情页 URL 或 slug 抓取并入库。
    若已存在同型号：通过 query 参数 duplicate_action 指定 overwrite / new_version / cancel。
    """
    url = body.url
    if not url and body.slug:
        url = f"https://www.gsmarena.com/{body.slug}" if not body.slug.startswith("http") else body.slug
    if not url:
        raise HTTPException(status_code=400, detail="请提供 url 或 slug")
    success, data, err = gsm.fetch_phone_specs(url)
    if not success:
        return {"success": False, "product_id": None, "message": err, "duplicate_action": None, "existing_id": None}
    # 查重
    existing = psvc.find_duplicate(db, data.get("brand"), data.get("model"), data.get("full_name"))
    if existing:
        if duplicate_action == "cancel":
            return {"success": False, "product_id": None, "message": "已取消导入（存在同型号）", "duplicate_action": "cancel", "existing_id": existing.id}
        if duplicate_action == "overwrite":
            product = existing
            product.source_url = data.get("source_url")
            product.source_type = "gsmarena"
            product.os = data.get("os")
            product.chipset = data.get("chipset")
            product.cpu = data.get("cpu")
            product.gpu = data.get("gpu")
            product.display_type = data.get("display_type")
            product.display_size = data.get("display_size")
            product.resolution = data.get("resolution")
            product.refresh_rate = data.get("refresh_rate")
            product.battery = data.get("battery")
            product.charging = data.get("charging")
            product.main_camera = data.get("main_camera")
            product.selfie_camera = data.get("selfie_camera")
            product.memory_summary = data.get("memory_summary")
            product.launch_date = data.get("launch_date")
            product.status = data.get("status")
            product.raw_specs_json = data.get("raw_specs_json")
            product.raw_html = data.get("raw_html")
            db.query(ProductSpecItem).filter(ProductSpecItem.product_id == product.id).delete()
            for i, s in enumerate(data.get("spec_items") or []):
                db.add(ProductSpecItem(product_id=product.id, spec_group=s.get("spec_group"), spec_key=s.get("spec_key"), spec_value=s.get("spec_value"), sort_order=s.get("sort_order", i)))
            db.commit()
            db.refresh(product)
            return {"success": True, "product_id": product.id, "message": "已覆盖更新", "duplicate_action": "overwrite", "existing_id": existing.id}
        if duplicate_action == "new_version":
            data["full_name"] = (data.get("full_name") or "") + " (v2)"
            product = psvc.create_product(db, data)
            return {"success": True, "product_id": product.id, "message": "已另存为新版本", "duplicate_action": "new_version", "existing_id": existing.id}
        return {"success": False, "product_id": None, "message": "数据库已存在同型号，请选择：覆盖更新(overwrite)、另存为新版本(new_version)、取消(cancel)", "duplicate_action": None, "existing_id": existing.id}
    product = psvc.create_product(db, data)
    return {"success": True, "product_id": product.id, "message": "导入成功", "duplicate_action": None, "existing_id": None}
