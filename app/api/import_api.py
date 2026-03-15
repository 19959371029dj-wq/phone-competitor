"""
价格批量导入、产品模板导入、回滚。
"""
import io

import pandas as pd
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.phone import ImportBatch
from app.schemas.import_schemas import (
    PricePreviewResponse,
    PricePreviewRow,
    PriceConfirmRequest,
    PriceConfirmResponse,
)
from app.services import price_import_service as pimp
from app.services import product_service as psvc

router = APIRouter(tags=["import"])

# 产品批量导入模板列（与 GSMArena/产品表字段一致）
PRODUCT_TEMPLATE_COLUMNS = [
    "brand", "model", "full_name",
    "os", "chipset", "cpu", "gpu",
    "display_type", "display_size", "resolution", "refresh_rate",
    "battery", "charging",
    "main_camera", "selfie_camera",
    "memory_summary",
    "price", "currency",
    "launch_date",
]


@router.get("/api/import/product-template")
def get_product_template():
    """下载产品批量导入模板 Excel（与 GSMArena 字段一致）。"""
    sample = [
        [
            "Xiaomi", "14", "Xiaomi 14",
            "Android 14", "Snapdragon 8 Gen 3", "Octa-core", "Adreno 750",
            "LTPO OLED", "6.36\"", "1200x2670", "120Hz",
            "4610 mAh", "90W",
            "50MP+50MP+50MP", "32MP",
            "12+256GB",
            "3999", "CNY",
            "2024-01",
        ]
    ]
    df = pd.DataFrame(sample, columns=PRODUCT_TEMPLATE_COLUMNS)
    buf = io.BytesIO()
    df.to_excel(buf, index=False, engine="openpyxl")
    buf.seek(0)
    return StreamingResponse(
        io.BytesIO(buf.getvalue()),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=product_template.xlsx"},
    )


@router.post("/api/import/products-upload", response_model=dict)
async def products_upload(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """按模板批量导入机型到产品数据库。"""
    if not file.filename:
        raise HTTPException(status_code=400, detail="请选择文件")
    content = await file.read()
    fn = (file.filename or "").lower()
    try:
        if fn.endswith(".csv"):
            df = pd.read_csv(io.BytesIO(content), encoding="utf-8", on_bad_lines="skip")
        else:
            df = pd.read_excel(io.BytesIO(content), header=0)
    except Exception as e:
        return {"success": False, "created": 0, "message": f"文件解析失败: {e}"}
    created = 0
    for _, row in df.iterrows():
        brand = str(row.get("brand") or "").strip()
        model = str(row.get("model") or "").strip()
        full_name = str(row.get("full_name") or "").strip()
        if not (brand or model or full_name):
            continue
        data = {
            "brand": brand or None,
            "model": model or None,
            "full_name": full_name or None,
            "os": _cell(row.get("os")),
            "chipset": _cell(row.get("chipset")),
            "cpu": _cell(row.get("cpu")),
            "gpu": _cell(row.get("gpu")),
            "display_type": _cell(row.get("display_type")),
            "display_size": _cell(row.get("display_size")),
            "resolution": _cell(row.get("resolution")),
            "refresh_rate": _cell(row.get("refresh_rate")),
            "battery": _cell(row.get("battery")),
            "charging": _cell(row.get("charging")),
            "main_camera": _cell(row.get("main_camera")),
            "selfie_camera": _cell(row.get("selfie_camera")),
            "memory_summary": _cell(row.get("memory_summary")),
            "price": row.get("price"),
            "currency": _cell(row.get("currency")),
            "launch_date": _cell(row.get("launch_date")),
            "source_type": "template_upload",
            "spec_items": [],
        }
        psvc.create_product(db, data)
        created += 1
    return {"success": True, "created": created, "message": f"已导入 {created} 条机型记录"}


def _cell(v):
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return None
    s = str(v).strip()
    return s if s else None


@router.get("/api/import/price-template")
def get_price_template():
    """下载价格批量导入模板 Excel。"""
    buf = io.BytesIO(pimp.get_price_template_bytes())
    return StreamingResponse(buf, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", headers={"Content-Disposition": "attachment; filename=price_template.xlsx"})


@router.post("/api/import/price-preview", response_model=dict)
async def price_preview(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """上传价格文件，返回匹配预览。"""
    if not file.filename:
        raise HTTPException(status_code=400, detail="请选择文件")
    content = await file.read()
    ok, rows, err = pimp.parse_price_file(content, file.filename)
    if not ok:
        return {"success": False, "total_rows": 0, "rows": [], "matched_count": 0, "no_match_count": 0, "duplicate_count": 0, "message": err}
    preview_rows, matched, no_match, dup = pimp.preview_price_import(db, rows)
    return {
        "success": True,
        "total_rows": len(preview_rows),
        "rows": preview_rows,
        "matched_count": matched,
        "no_match_count": no_match,
        "duplicate_count": dup,
        "message": None,
    }


@router.post("/api/import/price-confirm", response_model=dict)
def price_confirm(body: PriceConfirmRequest, db: Session = Depends(get_db), file_name: str | None = None):
    """确认执行价格更新。body.rows 为预览接口返回的 rows。"""
    rows = body.rows or []
    success, batch_id, updated, msg = pimp.confirm_price_import(db, rows, file_name)
    if not success:
        return {"success": False, "batch_id": None, "updated_count": 0, "message": msg}
    return {"success": True, "batch_id": batch_id, "updated_count": updated, "message": msg}


@router.post("/api/import/price-rollback/{batch_id}", response_model=dict)
def price_rollback(batch_id: int, db: Session = Depends(get_db)):
    """回滚指定批次的价格导入。"""
    ok, msg = pimp.rollback_batch(db, batch_id)
    if not ok:
        raise HTTPException(status_code=400, detail=msg)
    return {"success": True, "message": msg}


@router.get("/api/import/batches", response_model=dict)
def list_import_batches(db: Session = Depends(get_db), limit: int = 20):
    """导入批次列表（用于价格回滚选择）。"""
    batches = db.query(ImportBatch).order_by(ImportBatch.id.desc()).limit(limit).all()
    return {"success": True, "data": [{"id": b.id, "import_type": b.import_type, "file_name": b.file_name, "status": b.status, "summary": b.summary, "created_at": b.created_at.isoformat() if b.created_at else None} for b in batches]}
