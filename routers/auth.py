"""
认证路由：注册、登录
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from schemas.user import UserCreate, UserLogin, UserResponse, Token
from services.auth_service import authenticate_user, create_access_token, register_user

router = APIRouter(prefix="/auth", tags=["认证"])


@router.post("/register", response_model=UserResponse, summary="用户注册")
async def register(data: UserCreate, db: Session = Depends(get_db)):
    """
    用户注册

    - 用户名和邮箱必须唯一
    - 密码至少 6 位
    """
    try:
        user = register_user(db, data.username, data.email, data.password, data.phone)
        return user
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/login", response_model=Token, summary="用户登录")
async def login(data: UserLogin, db: Session = Depends(get_db)):
    """
    用户登录

    - 返回 JWT Token
    """
    user = authenticate_user(db, data.username, data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
        )

    access_token = create_access_token(data={"sub": str(user.id)})
    return {"access_token": access_token}


@router.get("/me", response_model=UserResponse, summary="获取当前用户信息")
async def get_me(current_user=Depends(__import__("dependencies").get_current_user)):
    """获取当前登录用户信息"""
    return current_user
