"""
商品种子数据脚本

运行方式：
    python -m scripts.seed_data

数据来源：京东/天猫等电商平台 2024 年热销商品参考价格
"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import engine, SessionLocal, Base
from models.product import Category, Product


# ============================================================
# 分类数据
# ============================================================

CATEGORIES = [
    {"id": 1, "name": "手机通讯", "level": 1, "sort_order": 1},
    {"id": 2, "name": "电脑办公", "level": 1, "sort_order": 2},
    {"id": 3, "name": "智能穿戴", "level": 1, "sort_order": 3},
    {"id": 4, "name": "数码配件", "level": 1, "sort_order": 4},
    {"id": 5, "name": "家用电器", "level": 1, "sort_order": 5},
]


# ============================================================
# 商品数据（2024年热销款）
# ============================================================

PRODUCTS = [
    # ---- 手机通讯 ----
    {
        "name": "Apple iPhone 16 Pro Max 256GB",
        "description": "A18 Pro 芯片，钛金属设计，4800 万像素相机系统，支持 Apple Intelligence",
        "price": 9999.00,
        "original_price": 9999.00,
        "stock": 50,
        "category_id": 1,
        "brand": "Apple",
        "specs": {"storage": "256GB", "color": "原色钛金属", "screen": "6.9英寸"},
        "sales_count": 12580,
    },
    {
        "name": "Apple iPhone 16 128GB",
        "description": "A18 芯片，4800 万像素融合相机，操作按钮，USB-C",
        "price": 5999.00,
        "original_price": 5999.00,
        "stock": 100,
        "category_id": 1,
        "brand": "Apple",
        "specs": {"storage": "128GB", "color": "黑色", "screen": "6.1英寸"},
        "sales_count": 28930,
    },
    {
        "name": "华为 Mate 70 Pro 512GB",
        "description": "麒麟 9100 芯片，红枫原色影像，超长续航，鸿蒙 AI",
        "price": 6999.00,
        "original_price": 6999.00,
        "stock": 30,
        "category_id": 1,
        "brand": "华为",
        "specs": {"storage": "512GB", "color": "雅川青", "screen": "6.9英寸"},
        "sales_count": 8560,
    },
    {
        "name": "小米 15 Pro 12GB+256GB",
        "description": "骁龙 8 至尊版，徕卡光学，5400mAh 大电池，120W 快充",
        "price": 4499.00,
        "original_price": 4799.00,
        "stock": 200,
        "category_id": 1,
        "brand": "小米",
        "specs": {"storage": "256GB", "ram": "12GB", "color": "白色", "screen": "6.73英寸"},
        "sales_count": 15670,
    },
    {
        "name": "Redmi K70 12GB+256GB",
        "description": "骁龙 8 Gen 2，2K 中国屏，OIS 光学防抖，120W 快充",
        "price": 2099.00,
        "original_price": 2399.00,
        "stock": 300,
        "category_id": 1,
        "brand": "小米",
        "specs": {"storage": "256GB", "ram": "12GB", "color": "墨羽", "screen": "6.67英寸"},
        "sales_count": 42350,
    },
    {
        "name": "OPPO Find X7 Ultra 16GB+256GB",
        "description": "骁龙 8 Gen 3，双潜望长焦，哈苏影像，100W 超级闪充",
        "price": 5999.00,
        "original_price": 5999.00,
        "stock": 60,
        "category_id": 1,
        "brand": "OPPO",
        "specs": {"storage": "256GB", "ram": "16GB", "color": "海阔天空", "screen": "6.82英寸"},
        "sales_count": 5620,
    },
    {
        "name": "vivo X200 Pro 12GB+256GB",
        "description": "天玑 9400，蔡司 APO 超级长焦，蓝图影像，6000mAh 蓝海电池",
        "price": 4299.00,
        "original_price": 4299.00,
        "stock": 120,
        "category_id": 1,
        "brand": "vivo",
        "specs": {"storage": "256GB", "ram": "12GB", "color": "钛色", "screen": "6.78英寸"},
        "sales_count": 9870,
    },
    {
        "name": "荣耀 Magic7 Pro 12GB+256GB",
        "description": "骁龙 8 至尊版，荣耀 AI 鹰眼相机，青海湖电池，100W 快充",
        "price": 4499.00,
        "original_price": 4499.00,
        "stock": 80,
        "category_id": 1,
        "brand": "荣耀",
        "specs": {"storage": "256GB", "ram": "12GB", "color": "绒黑色", "screen": "6.8英寸"},
        "sales_count": 7230,
    },
    {
        "name": "三星 Galaxy S24 Ultra 12GB+256GB",
        "description": "骁龙 8 Gen 3，Galaxy AI，钛金属框架，S Pen，2 亿像素",
        "price": 9699.00,
        "original_price": 9699.00,
        "stock": 40,
        "category_id": 1,
        "brand": "三星",
        "specs": {"storage": "256GB", "ram": "12GB", "color": "钛灰", "screen": "6.8英寸"},
        "sales_count": 4560,
    },
    {
        "name": "一加 13 12GB+256GB",
        "description": "骁龙 8 至尊版，哈苏影像，6000mAh 冰川电池，100W 超级闪充",
        "price": 4299.00,
        "original_price": 4299.00,
        "stock": 90,
        "category_id": 1,
        "brand": "一加",
        "specs": {"storage": "256GB", "ram": "12GB", "color": "黑曜秘境", "screen": "6.82英寸"},
        "sales_count": 6780,
    },

    # ---- 蓝牙耳机 ----
    {
        "name": "Apple AirPods Pro 2 (USB-C)",
        "description": "H2 芯片，自适应降噪，空间音频，MagSafe 充电盒",
        "price": 1899.00,
        "original_price": 1899.00,
        "stock": 150,
        "category_id": 4,
        "brand": "Apple",
        "specs": {"type": "入耳式", "noise_cancelling": "自适应", "battery": "6h+30h"},
        "sales_count": 35680,
    },
    {
        "name": "Sony WF-1000XM5 真无线降噪耳机",
        "description": "集成处理器 V2，行业领先降噪，30 小时续航，Hi-Res 音质",
        "price": 1699.00,
        "original_price": 1999.00,
        "stock": 80,
        "category_id": 4,
        "brand": "Sony",
        "specs": {"type": "入耳式", "noise_cancelling": "专业级", "battery": "8h+24h"},
        "sales_count": 12350,
    },
    {
        "name": "华为 FreeBuds Pro 3",
        "description": "麒麟 A2 芯片，智慧降噪 3.0，LDAC 高清音频，31 小时续航",
        "price": 1199.00,
        "original_price": 1199.00,
        "stock": 200,
        "category_id": 4,
        "brand": "华为",
        "specs": {"type": "入耳式", "noise_cancelling": "智慧降噪", "battery": "6.5h+24.5h"},
        "sales_count": 18920,
    },
    {
        "name": "小米 Buds 4 Pro",
        "description": "50dB 自适应降噪，LHDC 5.0，空间音频，38 小时续航",
        "price": 699.00,
        "original_price": 999.00,
        "stock": 300,
        "category_id": 4,
        "brand": "小米",
        "specs": {"type": "入耳式", "noise_cancelling": "50dB", "battery": "9h+29h"},
        "sales_count": 25670,
    },
    {
        "name": "漫步者 Neobuds Pro 2",
        "description": "圈铁混合驱动，-43dB 降噪，LDAC，游戏低延迟",
        "price": 499.00,
        "original_price": 599.00,
        "stock": 250,
        "category_id": 4,
        "brand": "漫步者",
        "specs": {"type": "入耳式", "noise_cancelling": "-43dB", "battery": "5.5h+16.5h"},
        "sales_count": 31240,
    },
    {
        "name": "三星 Galaxy Buds3 Pro",
        "description": "双驱动单元，智能降噪，360 音频，IP57 防水",
        "price": 1499.00,
        "original_price": 1499.00,
        "stock": 100,
        "category_id": 4,
        "brand": "三星",
        "specs": {"type": "入耳式", "noise_cancelling": "智能", "battery": "7h+26h"},
        "sales_count": 8760,
    },

    # ---- 笔记本电脑 ----
    {
        "name": "Apple MacBook Air 13 M3 8GB+256GB",
        "description": "M3 芯片，18 小时续航，Liquid Retina 显示屏，MagSafe 充电",
        "price": 8999.00,
        "original_price": 8999.00,
        "stock": 60,
        "category_id": 2,
        "brand": "Apple",
        "specs": {"cpu": "M3", "ram": "8GB", "storage": "256GB SSD", "screen": "13.6英寸"},
        "sales_count": 15680,
    },
    {
        "name": "华为 MateBook X Pro 2024",
        "description": "酷睿 Ultra 9，3.1K OLED 触控屏，980g 超轻机身",
        "price": 10999.00,
        "original_price": 11999.00,
        "stock": 30,
        "category_id": 2,
        "brand": "华为",
        "specs": {"cpu": "Core Ultra 9", "ram": "16GB", "storage": "1TB SSD", "screen": "14.2英寸"},
        "sales_count": 4560,
    },
    {
        "name": "联想 ThinkPad X1 Carbon Gen 12",
        "description": "酷睿 Ultra 7，2.8K OLED，14 英寸商务旗舰，1.08kg",
        "price": 9999.00,
        "original_price": 12999.00,
        "stock": 45,
        "category_id": 2,
        "brand": "联想",
        "specs": {"cpu": "Core Ultra 7", "ram": "16GB", "storage": "512GB SSD", "screen": "14英寸 2.8K"},
        "sales_count": 6780,
    },
    {
        "name": "Redmi Book 14 2024 i5",
        "description": "13代酷睿 i5，2.8K 120Hz 屏，56Wh 电池，金属机身",
        "price": 3499.00,
        "original_price": 3999.00,
        "stock": 150,
        "category_id": 2,
        "brand": "小米",
        "specs": {"cpu": "i5-13500H", "ram": "16GB", "storage": "512GB SSD", "screen": "14英寸 2.8K"},
        "sales_count": 22340,
    },
    {
        "name": "联想 ThinkBook 14+ 2024 R7",
        "description": "锐龙 7 8845H，2.8K 90Hz 屏，62Wh 大电池，丰富接口",
        "price": 4999.00,
        "original_price": 5499.00,
        "stock": 100,
        "category_id": 2,
        "brand": "联想",
        "specs": {"cpu": "R7-8845H", "ram": "16GB", "storage": "512GB SSD", "screen": "14英寸 2.8K"},
        "sales_count": 18920,
    },
    {
        "name": "华硕 Zenbook 14 OLED",
        "description": "酷睿 Ultra 7，2.8K OLED 华硕好屏，75Wh 大电池，1.2kg",
        "price": 6999.00,
        "original_price": 7499.00,
        "stock": 55,
        "category_id": 2,
        "brand": "华硕",
        "specs": {"cpu": "Core Ultra 7", "ram": "16GB", "storage": "512GB SSD", "screen": "14英寸 2.8K OLED"},
        "sales_count": 7890,
    },

    # ---- 智能手表 ----
    {
        "name": "Apple Watch Ultra 2",
        "description": "S9 芯片，49mm 钛金属表壳，双频 GPS，100m 防水",
        "price": 6499.00,
        "original_price": 6499.00,
        "stock": 40,
        "category_id": 3,
        "brand": "Apple",
        "specs": {"size": "49mm", "material": "钛金属", "battery": "36h", "water_resistant": "100m"},
        "sales_count": 5670,
    },
    {
        "name": "华为 WATCH GT 5 Pro",
        "description": "钛金属表壳，高尔夫/潜水模式，14 天超长续航",
        "price": 2488.00,
        "original_price": 2488.00,
        "stock": 80,
        "category_id": 3,
        "brand": "华为",
        "specs": {"size": "46mm", "material": "钛金属", "battery": "14天", "water_resistant": "50m"},
        "sales_count": 12340,
    },
    {
        "name": "小米 Watch S4",
        "description": "1.43 英寸 AMOLED，独立通话，150+ 运动模式，16 天续航",
        "price": 999.00,
        "original_price": 1299.00,
        "stock": 200,
        "category_id": 3,
        "brand": "小米",
        "specs": {"size": "46mm", "material": "铝合金", "battery": "16天", "water_resistant": "5ATM"},
        "sales_count": 28970,
    },
    {
        "name": "三星 Galaxy Watch Ultra",
        "description": "钛合金表壳，双频 GPS，100m 防水，运动手表",
        "price": 4799.00,
        "original_price": 4799.00,
        "stock": 35,
        "category_id": 3,
        "brand": "三星",
        "specs": {"size": "47mm", "material": "钛合金", "battery": "60h", "water_resistant": "100m"},
        "sales_count": 3450,
    },

    # ---- 家用电器 ----
    {
        "name": "戴森 V15 Detect 无绳吸尘器",
        "description": "激光探测灰尘，压电式传感器，240AW 吸力，60 分钟续航",
        "price": 4490.00,
        "original_price": 5490.00,
        "stock": 50,
        "category_id": 5,
        "brand": "戴森",
        "specs": {"power": "240AW", "battery": "60min", "weight": "2.61kg"},
        "sales_count": 8760,
    },
    {
        "name": "石头 G20 扫拖机器人",
        "description": "双超声波震动拖布，6000Pa 大吸力，智能避障，自动集尘",
        "price": 3999.00,
        "original_price": 4599.00,
        "stock": 70,
        "category_id": 5,
        "brand": "石头",
        "specs": {"suction": "6000Pa", "battery": "180min", "noise": "67dB"},
        "sales_count": 15680,
    },
    {
        "name": "追觅 X30 Ultra 扫拖机器人",
        "description": "12000Pa 超强吸力，机械臂贴边拖布，60°C 热水洗拖布",
        "price": 4299.00,
        "original_price": 4999.00,
        "stock": 45,
        "category_id": 5,
        "brand": "追觅",
        "specs": {"suction": "12000Pa", "battery": "180min", "hot_water": "60°C"},
        "sales_count": 9870,
    },
    {
        "name": "米家空气净化器 4 Pro",
        "description": "CADR 500m³/h，OLED 触控屏，滤芯寿命 6-12 个月",
        "price": 1499.00,
        "original_price": 1699.00,
        "stock": 120,
        "category_id": 5,
        "brand": "小米",
        "specs": {"cadr": "500m³/h", "area": "35-60㎡", "noise": "33-65dB"},
        "sales_count": 32450,
    },
]


def seed_database():
    """初始化数据库种子数据"""
    print("正在创建数据库表...")
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        # 检查是否已有数据
        existing_count = db.query(Product).count()
        if existing_count > 0:
            print(f"数据库已有 {existing_count} 条商品记录，跳过初始化")
            confirm = input("是否清空后重新导入？(y/N): ").strip().lower()
            if confirm != "y":
                print("已取消")
                return
            db.query(Product).delete()
            db.query(Category).delete()
            db.commit()
            print("已清空现有数据")

        # 插入分类
        print(f"正在插入 {len(CATEGORIES)} 个分类...")
        for cat_data in CATEGORIES:
            category = Category(**cat_data)
            db.add(category)
        db.commit()

        # 插入商品
        print(f"正在插入 {len(PRODUCTS)} 个商品...")
        for product_data in PRODUCTS:
            product = Product(**product_data)
            db.add(product)
        db.commit()

        print(f"✅ 种子数据初始化完成！")
        print(f"   - 分类：{len(CATEGORIES)} 个")
        print(f"   - 商品：{len(PRODUCTS)} 个")

    except Exception as e:
        db.rollback()
        print(f"❌ 初始化失败: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
