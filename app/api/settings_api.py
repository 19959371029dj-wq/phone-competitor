"""
系统设置：仅返回前端需要的非敏感配置；API Key 不通过接口暴露。
"""
from fastapi import APIRouter

from app.config import settings

router = APIRouter(tags=["settings"])


@router.get("/api/settings", response_model=dict)
def get_settings():
    """返回默认币种、市场区域、抓取超时等；不含 API Key。"""
    return {
        "success": True,
        "data": {
            "default_currency": settings.default_currency,
            "default_market_region": settings.default_market_region,
            "gsmarena_timeout_seconds": settings.gsmarena_timeout_seconds,
            "deepseek_configured": bool(settings.deepseek_api_key),
        },
    }


@router.put("/api/settings", response_model=dict)
def put_settings():
    """设置项建议通过 .env 修改，此处仅占位。"""
    return {"success": True, "message": "请通过 .env 修改配置后重启服务"}
