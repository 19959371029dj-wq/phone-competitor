"""
价格批量导入：模板生成、预览匹配、确认更新、回滚。
"""
import io
from decimal import Decimal
from typing import Any

import pandas as pd
from sqlalchemy.orm import Session

from app.models.phone import Product, PriceHistory, ImportBatch
from app.services.product_service import _parse_price


TEMPLATE_COLUMNS = [
    "brand", "model", "full_name", "price", "currency", "market_region", "sales_channel", "price_date"
]


def get_price_template_bytes() -> bytes:
    """生成价格模板 Excel（表头 + 一行示例）。"""
    df = pd.DataFrame(
        [
            ["Xiaomi", "14", "Xiaomi 14", "3999", "CNY", "CN", "官网", "2024-01-01"],
        ],
        columns=TEMPLATE_COLUMNS,
    )
    buf = io.BytesIO()
    df.to_excel(buf, index=False)
    return buf.getvalue()


def parse_price_file(content: bytes, filename: str) -> tuple[bool, list[dict], str | None]:
    """
    解析上传的 Excel/CSV 为行列表，每行 dict 含 TEMPLATE_COLUMNS。
    返回: (success, rows, error_message)
    """
    fn = (filename or "").lower()
    try:
        if fn.endswith(".csv"):
            df = pd.read_csv(io.BytesIO(content), encoding="utf-8", on_bad_lines="skip")
            if df.shape[1] < 4:
                df = pd.read_csv(io.BytesIO(content), encoding="gbk", on_bad_lines="skip")
        else:
            df = pd.read_excel(io.BytesIO(content), header=0)
    except Exception as e:
        return False, [], f"文件解析失败: {e}"
    rows = []
    for idx, r in df.iterrows():
        row = {c: (r.get(c) if pd.notna(r.get(c)) else None) for c in TEMPLATE_COLUMNS if c in r}
        if not row.get("price") and not row.get("full_name"):
            continue
        price = _parse_price(row.get("price"))
        if price is None and row.get("price") is not None:
            price = _parse_price(str(row.get("price")))
        row["price"] = price
        row["_row_index"] = int(idx) + 2  # Excel 行号从 2 起
        rows.append(row)
    if not rows:
        return False, [], "未解析到有效数据行（需包含 price 或 full_name）"
    return True, rows, None


def preview_price_import(db: Session, rows: list[dict]) -> tuple[list[dict], int, int, int]:
    """
    预览：按 brand+model 或 full_name 匹配产品，返回每行匹配状态。
    返回: (preview_rows, matched_count, no_match_count, duplicate_count)
    """
    preview = []
    matched_ids = set()
    matched_count = no_match_count = duplicate_count = 0
    for r in rows:
        brand = (r.get("brand") or "").strip() or None
        model = (r.get("model") or "").strip() or None
        full_name = (r.get("full_name") or "").strip() or None
        price = r.get("price")
        if price is not None and not isinstance(price, Decimal):
            price = _parse_price(price)
        # 匹配：先 full_name，再 brand+model
        product = None
        if full_name:
            product = db.query(Product).filter(Product.full_name == full_name).first()
        if not product and brand and model:
            product = db.query(Product).filter(
                Product.brand == brand,
                Product.model == model,
            ).first()
        if not product and full_name:
            product = db.query(Product).filter(Product.full_name.ilike(f"%{full_name}%")).first()
        status = "no_match"
        matched_id = None
        matched_name = None
        if product:
            if product.id in matched_ids:
                status = "duplicate"
                duplicate_count += 1
            else:
                status = "matched"
                matched_ids.add(product.id)
                matched_count += 1
            matched_id = product.id
            matched_name = product.full_name
        else:
            no_match_count += 1
        preview.append({
            "row_index": r.get("_row_index", 0),
            "brand": brand,
            "model": model,
            "full_name": full_name,
            "price": price,
            "currency": r.get("currency"),
            "market_region": r.get("market_region"),
            "sales_channel": r.get("sales_channel"),
            "price_date": r.get("price_date"),
            "match_status": status,
            "matched_product_id": matched_id,
            "matched_full_name": matched_name,
        })
    return preview, matched_count, no_match_count, duplicate_count


def confirm_price_import(
    db: Session,
    preview_rows: list[dict],
    file_name: str | None = None,
) -> tuple[bool, int | None, int, str]:
    """
    执行价格更新：只处理 match_status=matched 的行，写 price_history 并更新 product.price。
    返回: (success, batch_id, updated_count, message)
    """
    to_update = [r for r in preview_rows if r.get("match_status") == "matched" and r.get("matched_product_id")]
    if not to_update:
        return False, None, 0, "没有可更新的匹配记录"
    batch = ImportBatch(import_type="price_bulk", file_name=file_name, status="success", summary=None)
    db.add(batch)
    db.flush()
    updated = 0
    for r in to_update:
        pid = r["matched_product_id"]
        product = db.query(Product).filter(Product.id == pid).first()
        if not product:
            continue
        price = r.get("price")
        if price is None:
            continue
        if not isinstance(price, Decimal):
            price = _parse_price(price)
        if price is None:
            continue
        product.price = price
        product.currency = r.get("currency") or product.currency
        product.market_region = r.get("market_region") or product.market_region
        product.sales_channel = r.get("sales_channel") or product.sales_channel
        ph = PriceHistory(
            product_id=pid,
            price=price,
            currency=r.get("currency"),
            market_region=r.get("market_region"),
            sales_channel=r.get("sales_channel"),
            price_date=r.get("price_date"),
            import_batch_id=batch.id,
        )
        db.add(ph)
        updated += 1
    batch.summary = f"updated={updated}"
    db.commit()
    return True, batch.id, updated, f"已更新 {updated} 条价格记录"


def rollback_batch(db: Session, batch_id: int) -> tuple[bool, str]:
    """
    回滚该批次：将该批次写入的 price_history 对应的 product 恢复为上一笔历史价格（或清空），
    并删除该批次的 price_history，将 import_batches.status 设为 rolled_back。
    """
    batch = db.query(ImportBatch).filter(ImportBatch.id == batch_id).first()
    if not batch:
        return False, "批次不存在"
    if batch.status == "rolled_back":
        return False, "该批次已回滚"
    histories = db.query(PriceHistory).filter(PriceHistory.import_batch_id == batch_id).all()
    for h in histories:
        # 该 product 在非本批次中最近一条 price_history
        prev = (
            db.query(PriceHistory)
            .filter(PriceHistory.product_id == h.product_id, PriceHistory.import_batch_id != batch_id)
            .order_by(PriceHistory.id.desc())
            .first()
        )
        product = db.query(Product).filter(Product.id == h.product_id).first()
        if product:
            if prev:
                product.price = prev.price
                product.currency = prev.currency
                product.market_region = prev.market_region
                product.sales_channel = prev.sales_channel
            else:
                product.price = None
                product.currency = None
        db.delete(h)
    batch.status = "rolled_back"
    batch.summary = (batch.summary or "") + "; rolled_back"
    db.commit()
    return True, "回滚成功"
