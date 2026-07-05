"""
认证服务：密码加密、JWT 生成/验证
"""

from datetime import datetime, timedelta

import bcrypt
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from config import ALGORITHM, SECRET_KEY, ACCESS_TOKEN_EXPIRE_MINUTES
from models.user import User


def hash_password(password: str) -> str:
    """加密密码"""
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    password_bytes = plain_password.encode('utf-8')
    hashed_bytes = hashed_password.encode('utf-8')
    return bcrypt.checkpw(password_bytes, hashed_bytes)


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """
    创建 JWT Token

    参数:
        data: 载荷数据（通常是 {"sub": user_id}）
        expires_delta: 过期时间增量
    """
    to_encode = data.copy()
    expire = datetime.now() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict | None:
    """
    解码 JWT Token

    返回:
        解码后的数据，失败返回 None
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


def register_user(db: Session, username: str, email: str, password: str, phone: str | None = None) -> User:
    """
    注册用户

    异常:
        ValueError: 用户名或邮箱已存在
    """
    # 检查用户名是否已存在
    existing = db.query(User).filter(User.username == username).first()
    if existing:
        raise ValueError("用户名已存在")

    # 检查邮箱是否已存在
    existing = db.query(User).filter(User.email == email).first()
    if existing:
        raise ValueError("邮箱已存在")

    # 创建用户
    user = User(
        username=username,
        email=email,
        hashed_password=hash_password(password),
        phone=phone,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, username: str, password: str) -> User | None:
    """
    验证用户

    返回:
        验证成功返回 User，失败返回 None
    """
    user = db.query(User).filter(User.username == username).first()
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user
