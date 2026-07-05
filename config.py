"""
项目配置
"""

# MySQL 配置
# 格式: mysql+pymysql://用户名:密码@主机:端口/数据库名
MYSQL_USER = "root"
MYSQL_PASSWORD = "123456"  # 改成你的 MySQL 密码
MYSQL_HOST = "localhost"
MYSQL_PORT = 3306
MYSQL_DATABASE = "ecommerce"

DATABASE_URL = f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}?charset=utf8mb4"

# Redis 配置
REDIS_HOST = "localhost"
REDIS_PORT = 6379
REDIS_DB = 0
REDIS_URL = f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}"

# JWT 配置
SECRET_KEY = "your-secret-key-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 小时

# 购物车配置
CART_KEY_PREFIX = "cart:"
CART_EXPIRE_DAYS = 7  # 购物车 7 天过期

# 订单配置
ORDER_TIMEOUT_MINUTES = 30  # 订单 30 分钟未支付自动取消
