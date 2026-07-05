"""
数据库连接配置（MySQL）
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from config import DATABASE_URL

# 创建引擎（MySQL 不需要 check_same_thread）
engine = create_engine(
    DATABASE_URL,
    echo=False,  # 设为 True 可以看到 SQL 语句
    pool_size=10,  # 连接池大小
    max_overflow=20,  # 最大溢出连接数
    pool_recycle=3600,  # 连接回收时间（秒）
)

# 创建 Session 工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# 声明基类
class Base(DeclarativeBase):
    pass


# 获取数据库 Session（用于 FastAPI 依赖注入）
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# 创建所有表
def create_tables():
    Base.metadata.create_all(bind=engine)
