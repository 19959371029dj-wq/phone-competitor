"""
手机产品参数查询与竞品分析工具 - FastAPI 入口。
仅使用 phone 相关模型与 API，供前端 Next.js 调用。
"""
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import engine, get_db
from app.models.phone import Base, Product, ProductSpecItem, PriceHistory, ImportBatch, ComparisonReport
from app.api import products, gsmarena, import_api, compare, settings_api


@asynccontextmanager
async def lifespan(app: FastAPI):
    if "sqlite" in settings.database_url:
        Path("./data").mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="手机产品参数查询与竞品分析工具",
    description="GSMArena 抓取、Profile 导入、价格批量更新、DeepSeek 竞品分析",
    version="1.0.0",
    lifespan=lifespan,
)

_origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
if not _origins:
    _origins = ["http://localhost:3000", "http://127.0.0.1:3000"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(products.router)
app.include_router(gsmarena.router)
app.include_router(import_api.router)
app.include_router(compare.router)
app.include_router(settings_api.router)


@app.get("/")
def root():
    return {"message": "手机产品参数查询与竞品分析 API", "docs": "/docs"}
