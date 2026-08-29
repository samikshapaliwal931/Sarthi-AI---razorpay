from __future__ import annotations

import random
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import hash_api_key, hash_password, utcnow

DEMO_AI_BUYER_API_KEY = "sk_aib_demo_stride_athletics_2026"
from app.models import (
    Merchant,
    MerchantSettings,
    Product,
    ProductVariant,
    Inventory,
    Customer,
    Order,
    OrderItem,
    Cart,
    CartItem,
    CartStatus,
    Payment,
    PaymentStatus,
    OrderStatus,
    Policy,
    AbandonedCart,
)
from app.database import async_session_factory

logger = structlog.get_logger()

CATEGORIES = {
    "Running Shoes": [
        ("Nike Air Zoom Pegasus", 4999, "Nike"),
        ("Adidas Ultraboost Light", 7999, "Adidas"),
        ("Asics Gel-Kayano 30", 6499, "Asics"),
        ("New Balance Fresh Foam 1080", 5999, "New Balance"),
        ("Brooks Ghost 15", 5499, "Brooks"),
        ("Puma Velocity Nitro", 3999, "Puma"),
        ("Reebok Floatride Energy", 3499, "Reebok"),
        ("Saucony Ride 16", 4999, "Saucony"),
        ("Under Armour HOVR", 4499, "Under Armour"),
        ("Skechers GoRun Ride", 2999, "Skechers"),
    ],
    "Training Shoes": [
        ("Nike Metcon 9", 5999, "Nike"),
        ("Adidas Dropset 2", 4499, "Adidas"),
        ("Reebok Nano X3", 4999, "Reebok"),
        ("Nike Free Metcon 5", 4999, "Nike"),
        ("Under Armour TriBase", 3999, "Under Armour"),
    ],
    "Sports Socks": [
        ("Nike Everyday Cushioned (3-pack)", 599, "Nike"),
        ("Adidas Performance (3-pack)", 499, "Adidas"),
        ("Puma Athletic Socks (6-pack)", 699, "Puma"),
        ("Asics Tabio Running Socks", 899, "Asics"),
        ("Balega Hidden Comfort", 1299, "Balega"),
    ],
    "Sports Apparel": [
        ("Nike Dri-FIT Running Tee", 1999, "Nike"),
        ("Adidas Aeroready Shorts", 1499, "Adidas"),
        ("Under Armour Tech Polo", 1799, "Under Armour"),
        ("Puma Running Tights", 2499, "Puma"),
        ("New Balance Speed Shorts", 1299, "New Balance"),
    ],
    "Accessories": [
        ("Running Belt", 999, "FlipBelt"),
        ("Sports Water Bottle 750ml", 699, "HydroForce"),
        ("Reflective Running Vest", 1299, "NightRunner"),
        ("Compression Calf Sleeves", 799, "CompFit"),
        ("GPS Running Watch", 8999, "Garmin"),
        ("Heart Rate Monitor", 3999, "Polar"),
    ],
    "Recovery": [
        ("Foam Roller Pro", 1499, "TriggerPoint"),
        ("Massage Gun Mini", 4999, "Theragun"),
        ("Ice Pack Wrap", 899, "RecoveryPro"),
        ("Resistance Bands Set", 999, "FitBand"),
        ("Yoga Mat Premium", 1999, "Manduka"),
    ],
    "Nutrition": [
        ("Protein Bar (12-pack)", 2499, "MuscleBlaze"),
        ("Electrolyte Drink Mix", 999, "Fast&Up"),
        ("Energy Gel (6-pack)", 799, "GU"),
        ("BCAA Powder 300g", 1499, "OptimumNutrition"),
        ("Creatine Monohydrate", 999, "AsItIs"),
    ],
}

DESCRIPTIONS = {
    "Running Shoes": "High-performance running shoe with responsive cushioning and breathable upper. Designed for road running with excellent grip and durability.",
    "Training Shoes": "Versatile training shoe built for gym workouts, cross-training, and functional fitness. Stable platform with flexible forefoot.",
    "Sports Socks": "Moisture-wicking athletic socks with arch support and cushioned sole. Keeps feet dry and comfortable during intense activity.",
    "Sports Apparel": "Lightweight, breathable sports apparel with sweat-wicking technology. Designed for freedom of movement during workouts.",
    "Accessories": "Essential running and fitness accessories to enhance your training experience and performance.",
    "Recovery": "Professional-grade recovery tools to help muscles recover faster and prevent injury after intense training.",
    "Nutrition": "Sports nutrition supplements formulated for athletes. Clean ingredients for optimal performance and recovery.",
}


async def seed_demo_data() -> None:
    async with async_session_factory() as session:
        from sqlalchemy import select
        existing = await session.execute(select(Merchant).where(Merchant.store_name == "Stride Athletics"))
        if existing.scalar_one_or_none():
            logger.info("demo_data_already_seeded")
            return

        merchant = Merchant(
            name="Demo Merchant",
            email="demo@strideathletics.com",
            password_hash=hash_password("demo123456"),
            store_name="Stride Athletics",
            store_url="https://strideathletics.demo.sarthi.ai",
            ai_buyer_api_key_hash=hash_api_key(DEMO_AI_BUYER_API_KEY),
        )
        session.add(merchant)
        await session.flush()
        logger.info("demo_ai_buyer_api_key", api_key=DEMO_AI_BUYER_API_KEY)

        m_settings = MerchantSettings(
            merchant_id=merchant.id,
            max_discount_percent=10.0,
            max_campaign_budget=50000.0,
            max_daily_spend=10000.0,
            max_actions_per_hour=10,
            approval_required_above_amount=5000.0,
            auto_approve_below_amount=1000.0,
        )
        session.add(m_settings)
        await session.flush()

        default_policies = [
            Policy(
                merchant_id=merchant.id,
                name="Max Discount",
                policy_type="discount_limit",
                rules={"max_discount_percent": 10, "action_types": ["apply_discount"]},
                priority=100,
            ),
            Policy(
                merchant_id=merchant.id,
                name="Campaign Budget Cap",
                policy_type="budget_limit",
                rules={"max_budget": 50000, "action_types": ["create_campaign"]},
                priority=90,
            ),
            Policy(
                merchant_id=merchant.id,
                name="High Value Approval",
                policy_type="approval_threshold",
                rules={"approval_above_amount": 5000, "action_types": ["create_campaign", "apply_discount"]},
                priority=80,
            ),
            Policy(
                merchant_id=merchant.id,
                name="Hourly Action Limit",
                policy_type="action_frequency",
                rules={"max_per_hour": 10},
                priority=70,
            ),
        ]
        for p in default_policies:
            session.add(p)
        await session.flush()

        products: list[Product] = []
        inventories: list[Inventory] = []
        product_map: dict[str, Product] = {}

        for category, items in CATEGORIES.items():
            for name, price, brand in items:
                product = Product(
                    merchant_id=merchant.id,
                    name=name,
                    description=DESCRIPTIONS.get(category, f"Quality {category.lower()} product."),
                    category=category,
                    brand=brand,
                    base_price=float(price),
                    sale_price=float(price * 0.9) if random.random() > 0.5 else None,
                    currency="INR",
                    images=[f"https://images.strideathletics.demo/{name.lower().replace(' ', '-')}.jpg"],
                    tags=[category.lower(), brand.lower()],
                    is_active=True,
                )
                session.add(product)
                await session.flush()
                products.append(product)
                product_map[name] = product

                stock = random.randint(10, 200)
                inventory = Inventory(
                    product_id=product.id,
                    merchant_id=merchant.id,
                    quantity=stock,
                    reserved=random.randint(0, min(5, stock)),
                    low_stock_threshold=5,
                )
                session.add(inventory)
                inventories.append(inventory)

        while len(products) < 150:
            cat = random.choice(list(CATEGORIES.keys()))
            base_items = CATEGORIES[cat]
            base_name, base_price, base_brand = random.choice(base_items)
            suffix = f"V{random.randint(2, 5)}"
            name = f"{base_name} {suffix}"
            product = Product(
                merchant_id=merchant.id,
                name=name,
                description=DESCRIPTIONS.get(cat, f"Quality {cat.lower()} product."),
                category=cat,
                brand=base_brand,
                base_price=float(base_price + random.randint(-500, 500)),
                currency="INR",
                tags=[cat.lower()],
                is_active=True,
            )
            session.add(product)
            await session.flush()
            products.append(product)
            product_map[name] = product

            inventory = Inventory(
                product_id=product.id,
                merchant_id=merchant.id,
                quantity=random.randint(5, 100),
                reserved=random.randint(0, 3),
                low_stock_threshold=5,
            )
            session.add(inventory)

        await session.flush()

        customers: list[Customer] = []
        first_names = ["Aarav", "Vivaan", "Aditya", "Vihaan", "Arjun", "Sai", "Reyansh", "Ayaan", "Krishna", "Ishaan",
                       "Ananya", "Diya", "Myra", "Sara", "Aadhya", "Kiara", "Riya", "Prisha", "Anika", "Navya"]
        last_names = ["Sharma", "Verma", "Patel", "Singh", "Kumar", "Gupta", "Joshi", "Mehta", "Reddy", "Nair",
                      "Iyer", "Das", "Rao", "Pillai", "Menon", "Chopra", "Kapoor", "Malhotra", "Banerjee", "Mukherjee"]

        for i in range(200):
            customer = Customer(
                merchant_id=merchant.id,
                email=f"customer{i+1}@example.com",
                phone=f"+91{random.randint(7000000000, 9999999999)}",
                name=f"{random.choice(first_names)} {random.choice(last_names)}",
                segment=random.choice(["new", "regular", "vip", "at_risk"]),
                lifetime_value=round(random.uniform(500, 50000), 2),
                order_count=random.randint(0, 30),
            )
            session.add(customer)
            customers.append(customer)

        await session.flush()

        orders: list[Order] = []
        now = utcnow()
        for i in range(400):
            customer = random.choice(customers)
            num_items = random.randint(1, 4)
            selected_products = random.sample(products, min(num_items, len(products)))

            subtotal = 0.0
            order_items_data = []
            for p in selected_products:
                qty = random.randint(1, 3)
                price = p.sale_price or p.base_price
                total = price * qty
                subtotal += total
                order_items_data.append((p, qty, price, total))

            days_ago = random.randint(0, 180)
            created = now - timedelta(days=days_ago, hours=random.randint(0, 23))

            status_choices = [OrderStatus.PAID] * 8 + [OrderStatus.CREATED, OrderStatus.FAILED]
            order_status = random.choice(status_choices)

            order = Order(
                merchant_id=merchant.id,
                customer_id=customer.id,
                order_number=f"ORD-{uuid.uuid4().hex[:10].upper()}",
                status=order_status,
                subtotal=round(subtotal, 2),
                total=round(subtotal, 2),
                currency="INR",
                created_at=created,
            )
            session.add(order)
            orders.append(order)
            await session.flush()

            for p, qty, price, total in order_items_data:
                item = OrderItem(
                    order_id=order.id,
                    merchant_id=merchant.id,
                    product_id=p.id,
                    quantity=qty,
                    unit_price=price,
                    total_price=total,
                )
                session.add(item)

            if order_status == OrderStatus.PAID:
                payment = Payment(
                    order_id=order.id,
                    merchant_id=merchant.id,
                    razorpay_payment_id=f"pay_{uuid.uuid4().hex[:14]}",
                    status=PaymentStatus.CAPTURED,
                    amount=order.total,
                    currency="INR",
                    method=random.choice(["card", "upi", "netbanking", "wallet"]),
                )
                session.add(payment)

        await session.flush()

        for i in range(50):
            customer = random.choice(customers)
            num_items = random.randint(1, 3)
            selected_products = random.sample(products, min(num_items, len(products)))

            subtotal = sum((p.sale_price or p.base_price) * random.randint(1, 2) for p in selected_products)

            cart = Cart(
                merchant_id=merchant.id,
                customer_id=customer.id,
                session_id=f"session_{uuid.uuid4().hex[:12]}",
                status=CartStatus.ABANDONED,
                subtotal=round(subtotal, 2),
                currency="INR",
            )
            session.add(cart)
            await session.flush()

            for p in selected_products:
                qty = random.randint(1, 2)
                price = p.sale_price or p.base_price
                item = CartItem(
                    cart_id=cart.id,
                    merchant_id=merchant.id,
                    product_id=p.id,
                    quantity=qty,
                    unit_price=price,
                )
                session.add(item)

            abandoned = AbandonedCart(
                cart_id=cart.id,
                merchant_id=merchant.id,
                customer_id=customer.id,
                cart_value=round(subtotal, 2),
                item_count=len(selected_products),
                abandoned_at=now - timedelta(days=random.randint(1, 30)),
            )
            session.add(abandoned)

        await session.flush()

        for customer in customers:
            customer.order_count = sum(1 for o in orders if o.customer_id == customer.id and o.status == OrderStatus.PAID)
            customer.lifetime_value = sum(
                o.total for o in orders if o.customer_id == customer.id and o.status == OrderStatus.PAID
            )

        await session.commit()
        logger.info(
            "demo_data_seeded",
            merchant="Stride Athletics",
            products=len(products),
            customers=len(customers),
            orders=len(orders),
        )
