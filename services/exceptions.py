"""
业务异常定义

服务层抛出，路由层捕获并映射为 HTTP 状态码。
"""


class BusinessError(Exception):
    """业务逻辑异常基类"""
    status_code: int = 400

    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        if status_code is not None:
            self.status_code = status_code


class NotFoundError(BusinessError):
    """资源不存在"""
    status_code = 404


class ConflictError(BusinessError):
    """资源状态冲突（如库存不足、已下架）"""
    status_code = 409
