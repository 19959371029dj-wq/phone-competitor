"""
GSMArena 搜索与导入相关 schema。
"""
from pydantic import BaseModel, Field


class GsmArenaSearchResult(BaseModel):
    """搜索候选：单条机型。"""
    name: str
    url: str
    img_src: str | None = None


class GsmArenaSearchResponse(BaseModel):
    """搜索接口返回。"""
    success: bool = True
    query: str = ""
    results: list[GsmArenaSearchResult] = []
    message: str | None = None


class GsmArenaImportRequest(BaseModel):
    """用户选择机型后请求导入：传详情页 URL 或 slug。"""
    url: str | None = None
    slug: str | None = None  # 如 xiaomi_14-12345.php


class GsmArenaImportResponse(BaseModel):
    """导入结果。"""
    success: bool
    product_id: int | None = None
    message: str
    duplicate_action: str | None = None  # overwrite | new_version | cancel
    existing_id: int | None = None
