"""
API 测试脚本
"""

import json
import urllib.request

BASE_URL = "http://localhost:8000"
TOKEN = None


def request(method, path, data=None, headers=None):
    url = BASE_URL + path
    req = urllib.request.Request(url, method=method)
    req.add_header("Content-Type", "application/json")
    if headers:
        for k, v in headers.items():
            req.add_header(k, v)
    if data:
        req.data = json.dumps(data).encode("utf-8")
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return json.loads(e.read().decode("utf-8"))


def test_full_flow():
    global TOKEN

    print("=" * 60)
    print("电商 API 完整测试")
    print("=" * 60)

    # 1. 注册
    print("\n【1】注册用户")
    result = request("POST", "/api/auth/register", {
        "username": "buyer1",
        "email": "buyer1@test.com",
        "password": "test123"
    })
    print(f"  结果: {result}")

    # 2. 登录
    print("\n【2】登录")
    result = request("POST", "/api/auth/login", {
        "username": "buyer1",
        "password": "test123"
    })
    TOKEN = result.get("access_token")
    print(f"  Token: {TOKEN[:20]}...")

    # 3. 创建商品（用 testuser 的 token）
    print("\n【3】创建商品")
    headers = {"Authorization": f"Bearer {TOKEN}"}

    for product in [
        {"name": "Python Book", "price": 59, "stock": 100},
        {"name": "FastAPI Book", "price": 89, "stock": 50},
        {"name": "Redis Book", "price": 49, "stock": 200},
    ]:
        result = request("POST", "/api/products", product, headers)
        print(f"  创建: {result.get('name', result)}")

    # 4. 商品列表
    print("\n【4】商品列表")
    result = request("GET", "/api/products")
    for item in result.get("items", []):
        print(f"  - {item['name']}: {item['price']} (库存: {item['stock']})")

    # 5. 添加购物车
    print("\n【5】添加购物车")
    result = request("POST", "/api/cart", {"product_id": 4, "quantity": 2}, headers)
    print(f"  结果: {result}")
    result = request("POST", "/api/cart", {"product_id": 5, "quantity": 1}, headers)
    print(f"  结果: {result}")

    # 6. 查看购物车
    print("\n【6】购物车")
    result = request("GET", "/api/cart", headers=headers)
    for item in result.get("items", []):
        print(f"  - {item['product_name']} x{item['quantity']} = CNY {item['subtotal']}")
    print(f"  总计: CNY {result.get('total_amount', 0)}")

    # 7. 创建订单
    print("\n【7】创建订单")
    result = request("POST", "/api/orders", {
        "address": {"receiver": "张三", "phone": "13800138000", "address": "北京市朝阳区"},
        "cart_item_ids": [4, 5]
    }, headers)
    print(f"  订单号: {result.get('order_no')}")
    print(f"  状态: {result.get('status')}")
    print(f"  总金额: CNY {result.get('total_amount')}")
    order_id = result.get("id")

    # 8. 订单列表
    print("\n【8】我的订单")
    result = request("GET", "/api/orders", headers=headers)
    for item in result.get("items", []):
        print(f"  - {item['order_no']}: {item['status']} CNY {item['total_amount']}")

    # 9. 支付订单
    print(f"\n【9】支付订单 {order_id}")
    result = request("PUT", f"/api/orders/{order_id}/pay", headers=headers)
    print(f"  状态: {result.get('status')}")

    # 10. 管理员发货（需要先登录管理员）
    print(f"\n【10】管理员发货")
    # 创建管理员账号
    request("POST", "/api/auth/register", {
        "username": "admin1",
        "email": "admin1@test.com",
        "password": "admin123"
    })
    # 设置为管理员（直接修改数据库）
    import sqlite3
    try:
        import pymysql
        conn = pymysql.connect(host='localhost', user='root', password='123456', database='ecommerce')
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET is_admin=1 WHERE username='admin1'")
        conn.commit()
        conn.close()
    except:
        pass

    # 管理员登录
    admin_result = request("POST", "/api/auth/login", {"username": "admin1", "password": "admin123"})
    admin_token = admin_result.get("access_token")
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # 发货
    result = request("PUT", f"/api/admin/orders/{order_id}/ship", headers=admin_headers)
    print(f"  状态: {result.get('status')}")

    # 11. 确认收货
    print(f"\n【11】确认收货")
    result = request("PUT", f"/api/orders/{order_id}/confirm", headers=headers)
    print(f"  状态: {result.get('status')}")

    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)


if __name__ == "__main__":
    test_full_flow()
