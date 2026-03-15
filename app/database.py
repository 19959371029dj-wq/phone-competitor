"""
数据库连接与会话管理。
SQLAlchemy 同步方式，SQLite 支持多线程。
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from app.config import settings

connect_args = {}
if settings.database_url.startswith("sqlite"):
    connect_args["check_same_thread"] = False

engine = create_engine(
    settings.database_url,
    connect_args=connect_args,
    echo=False,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db() -> Session:
    """依赖注入：请求内使用 Session，结束后关闭。"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
