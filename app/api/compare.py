"""
多机型对比表与 AI 竞品分析报告。
"""
import io

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.phone import Product, ComparisonReport
from app.schemas.compare import CompareTableRequest, CompareReportRequest
from app.services import product_service as psvc
from app.services import ai_service as ai_svc

router = APIRouter(tags=["compare"])


def _product_to_compare_dict(p: Product) -> dict:
    """将 Product 转为给对比表/AI 用的扁平 dict。"""
    return {
        "id": p.id,
        "brand": p.brand,
        "model": p.model,
        "full_name": p.full_name,
        "launch_date": p.launch_date,
        "os": p.os,
        "chipset": p.chipset,
        "cpu": p.cpu,
        "gpu": p.gpu,
        "display_type": p.display_type,
        "display_size": p.display_size,
        "resolution": p.resolution,
        "refresh_rate": p.refresh_rate,
        "battery": p.battery,
        "charging": p.charging,
        "main_camera": p.main_camera,
        "selfie_camera": p.selfie_camera,
        "memory_summary": p.memory_summary,
        "price": str(p.price) if p.price is not None else None,
        "currency": p.currency,
    }


def _build_compare_table(product_ids: list[int], db: Session) -> tuple[list[dict], list[dict]]:
    """构建对比表 headers 与 rows，供 table 与 export 复用。"""
    if len(product_ids) < 2 or len(product_ids) > 10:
        return [], []
    products = [psvc.get_product(db, pid) for pid in product_ids]
    if any(p is None for p in products):
        return [], []
    headers = [{"id": p.id, "full_name": p.full_name, "brand": p.brand, "model": p.model} for p in products]
    main_fields = ["os", "chipset", "cpu", "gpu", "display_type", "display_size", "resolution", "refresh_rate", "battery", "charging", "main_camera", "selfie_camera", "memory_summary", "price"]
    rows = []
    for f in main_fields:
        values = []
        for p in products:
            v = getattr(p, f, None)
            values.append(str(v) if v is not None else "")
        rows.append({"spec_group": "Basic", "spec_key": f, "values": values})
    seen_spec = set()
    for p in products:
        for s in p.spec_items:
            g, k = (s.spec_group or ""), (s.spec_key or "")
            if (g, k) in seen_spec:
                continue
            seen_spec.add((g, k))
            values = []
            for p2 in products:
                spec = next((x for x in p2.spec_items if (x.spec_group or "") == g and (x.spec_key or "") == k), None)
                values.append(spec.spec_value or "" if spec else "")
            rows.append({"spec_group": g, "spec_key": k, "values": values})
    return headers, rows


@router.post("/api/compare/table", response_model=dict)
def compare_table(body: CompareTableRequest, db: Session = Depends(get_db)):
    """生成多机型参数对比表。"""
    headers, rows = _build_compare_table(body.product_ids, db)
    if not headers:
        raise HTTPException(status_code=400, detail="请选择 2～10 个机型")
    if not rows and headers:
        raise HTTPException(status_code=404, detail="部分机型不存在")
    return {"success": True, "product_headers": headers, "rows": rows}


@router.get("/api/compare/export")
def export_compare_table(
    product_ids: str = Query(..., description="机型 ID，逗号分隔，2～10 个"),
    db: Session = Depends(get_db),
):
    """下载当前对比表为 Excel。"""
    try:
        ids = [int(x.strip()) for x in product_ids.split(",") if x.strip()]
    except ValueError:
        raise HTTPException(status_code=400, detail="product_ids 格式错误")
    headers, rows = _build_compare_table(ids, db)
    if not headers or not rows:
        raise HTTPException(status_code=400, detail="请选择 2～10 个有效机型")
    col_names = ["参数分类", "参数项"] + [h.get("full_name") or f"机型{h.get('id')}" for h in headers]
    table_rows = [[r["spec_group"], r["spec_key"]] + r["values"] for r in rows]
    df = pd.DataFrame(table_rows, columns=col_names)
    buf = io.BytesIO()
    df.to_excel(buf, index=False, engine="openpyxl")
    buf.seek(0)
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=compare_table.xlsx"},
    )


@router.post("/api/compare/report", response_model=dict)
def compare_report(body: CompareReportRequest, db: Session = Depends(get_db)):
    """调用 DeepSeek 生成竞品分析报告，并保存到 comparison_reports。"""
    if len(body.product_ids) < 2 or len(body.product_ids) > 10:
        raise HTTPException(status_code=400, detail="请选择 2～10 个机型")
    products = [psvc.get_product(db, pid) for pid in body.product_ids]
    if any(p is None for p in products):
        raise HTTPException(status_code=404, detail="部分机型不存在")
    products_data = [_product_to_compare_dict(p) for p in products]
    success, markdown, err = ai_svc.generate_competitor_report(products_data)
    if not success:
        return {"success": False, "report_markdown": None, "report_id": None, "message": err}
    title = " vs ".join(p.full_name or p.model or str(p.id) for p in products)
    report = ComparisonReport(
        title=title,
        selected_product_ids=",".join(str(pid) for pid in body.product_ids),
        report_markdown=markdown,
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    return {"success": True, "report_markdown": markdown, "report_id": report.id, "message": None}
