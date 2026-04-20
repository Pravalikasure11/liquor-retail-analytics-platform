"""
Zach's Liquor Store — Real Store Data Seed
Loads: expenses, suppliers (Breakthru + RNDC), store promotions, FIFA Don Julio

Run:
    cd ~/Downloads/zachs/backend
    source venv/bin/activate
    python seed_store_data.py
"""
import asyncio
from datetime import datetime, timedelta
from app.database import AsyncSessionLocal, create_tables
from app.models.models import (
    Supplier, Expense, ExpenseCategory, Promotion, Product, User
)
from sqlalchemy import select, delete

async def main():
    await create_tables()
    async with AsyncSessionLocal() as db:

        # ── Get admin user ────────────────────────────────────────────────────
        r = await db.execute(select(User).where(User.username == "zach"))
        admin = r.scalar_one_or_none()
        if not admin:
            print("❌ Run seed.py first"); return

        print("🥃 Loading real store data...")

        # ── SUPPLIERS ─────────────────────────────────────────────────────────
        print("\n📦 Adding suppliers...")
        suppliers_data = [
            {
                "name": "Breakthru Beverage Maryland",
                "contact_email": "md.orders@breakthrubeverage.com",
                "phone": "410-712-7100",
                "address": "7901 Oceano Ave, Jessup, MD 20794",
                "website": "https://www.breakthrubeverage.com",
                "portal_type": "breakthru",
                "lead_days": 3,
                "notes": "Main beer + domestic spirits supplier. Reps visit weekly. "
                         "Handles: Budweiser, Coors, Miller, Corona, Modelo, Heineken, "
                         "Jim Beam, Fireball, Smirnoff, New Amsterdam, Malibu, Bacardi.",
                "is_active": True,
                "monitor_deals": True,
            },
            {
                "name": "RNDC Maryland",
                "contact_email": "md@rndc-usa.com",
                "phone": "443-920-7600",
                "address": "7001 Quad Ave, Baltimore, MD 21237",
                "website": "https://www.rndc-usa.com",
                "portal_type": "rndc",
                "lead_days": 4,
                "notes": "Premium spirits supplier. "
                         "Handles: Hennessy, Don Julio, Patron, Casamigos, Grey Goose, "
                         "Tito's, Crown Royal, Jack Daniels, Remy Martin, Ciroc.",
                "is_active": True,
                "monitor_deals": True,
            },
            {
                "name": "McLane Company",
                "contact_email": "orders@mclaneco.com",
                "phone": "254-771-7500",
                "website": "https://www.mclaneco.com",
                "portal_type": "custom",
                "lead_days": 2,
                "notes": "Tobacco, snacks, candy, cool drinks, vapes. "
                         "Handles: Newport, Marlboro, Camel, Swisher, Backwoods, "
                         "Monster, Red Bull, Gatorade, Doritos, Lays, Snickers.",
                "is_active": True,
                "monitor_deals": False,
            },
        ]
        for sd in suppliers_data:
            r = await db.execute(select(Supplier).where(Supplier.name == sd["name"]))
            if not r.scalar_one_or_none():
                db.add(Supplier(**sd))
                print(f"   ✓ {sd['name']}")
            else:
                print(f"   → {sd['name']} already exists")
        await db.flush()

        # ── EXPENSE CATEGORIES ────────────────────────────────────────────────
        print("\n💰 Setting up expense categories...")
        cat_map = {}
        cats = [
            ("Rent", "#E24B4A"),
            ("Utilities", "#BA7517"),
            ("Payroll", "#378ADD"),
            ("Inventory", "#639922"),
            ("Maintenance", "#534AB7"),
            ("Insurance", "#0F6E56"),
            ("Marketing", "#D4537E"),
            ("Supplies", "#888780"),
            ("Snacks / Staff", "#d4af37"),
            ("Other", "#666666"),
        ]
        for name, color in cats:
            r = await db.execute(select(ExpenseCategory).where(ExpenseCategory.name == name))
            cat = r.scalar_one_or_none()
            if not cat:
                cat = ExpenseCategory(name=name, color=color)
                db.add(cat)
                await db.flush()
            cat_map[name] = cat.id
        await db.flush()

        # ── EXPENSES (real recurring store costs) ─────────────────────────────
        print("\n📋 Loading expenses...")
        now = datetime.utcnow()

        # Monthly recurring expenses — load last 4 months
        monthly_expenses = [
            ("Monthly Rent",          2800.00, "Rent",        "Landlord"),
            ("Electric / BGE",         420.00, "Utilities",   "BGE"),
            ("Water & Sewer",           85.00, "Utilities",   "City"),
            ("Internet / Phone",        120.00, "Utilities",  "Comcast"),
            ("Payroll — Staff",        3200.00, "Payroll",    "ADP"),
            ("General Liability Insurance", 310.00, "Insurance", "State Farm"),
            ("Security System",         89.00, "Utilities",  "ADT"),
            ("Cleaning Supplies",       65.00, "Supplies",   "Sysco"),
            ("POS System (Aenasys)",    79.00, "Supplies",   "Aenasys"),
            ("Trash Removal",           95.00, "Utilities",  "County"),
        ]
        for month_offset in range(4):
            month_date = (now.replace(day=1) - timedelta(days=month_offset*30)).replace(day=3)
            for title, amount, cat_name, vendor in monthly_expenses:
                db.add(Expense(
                    title=title, amount=amount,
                    category_id=cat_map.get(cat_name, cat_map["Other"]),
                    expense_date=month_date,
                    vendor=vendor, is_recurring=True, recurrence="monthly",
                    created_by=admin.id,
                    notes=f"Auto-loaded recurring expense"
                ))

        # One-time expenses from the CSV
        one_time = [
            ("Restock Vodka Order",     200.00, "Inventory",    "Breakthru",    "2024-01-01"),
            ("Electricity Bill (Jan)",  150.00, "Utilities",    "BGE",          "2024-01-02"),
            ("Fridge Repair",           300.00, "Maintenance",  "HVAC Pro",     "2024-01-05"),
            ("Staff Snacks",             75.00, "Snacks / Staff","Internal",    "2024-01-04"),
            ("Cooler Door Repair",      425.00, "Maintenance",  "Repair Co",    "2024-03-15"),
            ("Signage Update",          280.00, "Marketing",    "Print Shop",   "2024-02-10"),
            ("Register Paper Rolls",     45.00, "Supplies",     "Office Depot", "2024-04-01"),
        ]
        for title, amount, cat_name, vendor, date_str in one_time:
            db.add(Expense(
                title=title, amount=amount,
                category_id=cat_map.get(cat_name, cat_map["Other"]),
                expense_date=datetime.fromisoformat(date_str),
                vendor=vendor, is_recurring=False, created_by=admin.id,
            ))
        await db.flush()
        print(f"   ✓ Recurring monthly expenses (4 months) + one-time expenses loaded")

        # ── PROMOTIONS ────────────────────────────────────────────────────────
        print("\n🏷️  Loading in-store promotions...")
        promos = [
            {
                "title": "Weekend Beer Deal — Natural Ice",
                "description": "Buy 2 Natural Ice 25oz, get $0.50 off each. Weekends only.",
                "promo_type": "Dollar Off",
                "discount_value": 0.50,
                "category": "Beer",
                "product_name": "Natural Ice 25oz",
                "start_date": now.replace(day=1),
                "end_date": now + timedelta(days=60),
                "is_active": True,
                "notes": "High velocity impulse item — drives traffic",
            },
            {
                "title": "Hennessy VS Bundle — Any Size",
                "description": "10% off any Hennessy VS purchase over $40. Great for gifting.",
                "promo_type": "Percentage Off",
                "discount_value": 10.0,
                "category": "Hard Liquor",
                "product_name": "Hennessy VS",
                "start_date": now,
                "end_date": now + timedelta(days=30),
                "is_active": True,
                "notes": "Hennessy is our top cognac — this drives premium basket size",
            },
            {
                "title": "Newport Carton Deal",
                "description": "Buy a Newport carton, save $5 vs buying 10 packs separately.",
                "promo_type": "Dollar Off",
                "discount_value": 5.00,
                "category": "Tobacco",
                "product_name": "Newport Core Carton",
                "start_date": now,
                "end_date": now + timedelta(days=90),
                "is_active": True,
                "notes": "Encourages bulk tobacco purchase — better margin per unit",
            },
            {
                "title": "Don Julio Happy Hour — Fridays 4-7PM",
                "description": "Any Don Julio mini shot (50ml) — $4.99. Regular price $5.99.",
                "promo_type": "Dollar Off",
                "discount_value": 1.00,
                "category": "Hard Liquor",
                "product_name": "Don Julio Core 50ml",
                "start_date": now,
                "end_date": now + timedelta(days=60),
                "is_active": True,
                "notes": "Friday 4-7PM only. Drives premium tequila trial.",
            },
            {
                "title": "Modelo 12-Pack Weekend Special",
                "description": "Modelo 12-pack — $16.99 this weekend only (reg $17.99).",
                "promo_type": "Dollar Off",
                "discount_value": 1.00,
                "category": "Beer",
                "product_name": "Modelo Core 12-pack",
                "start_date": now,
                "end_date": now + timedelta(days=14),
                "is_active": True,
                "notes": "Top imported beer — weekend volume driver",
            },
            {
                "title": "Buy 2 Vapes Get $3 Off",
                "description": "Buy any 2 disposable vapes, get $3 off total.",
                "promo_type": "Buy X Get Y",
                "discount_value": 3.00,
                "buy_qty": 2,
                "get_qty": 0,
                "category": "Vapes",
                "start_date": now,
                "end_date": now + timedelta(days=45),
                "is_active": True,
                "notes": "High margin category — bundle deal increases basket size",
            },
            {
                "title": "Cinco de Mayo — Tequila Week",
                "description": "All tequila 750ml bottles — 5% off May 1–5. Patron, Don Julio, 1800.",
                "promo_type": "Percentage Off",
                "discount_value": 5.0,
                "category": "Hard Liquor",
                "product_name": "All Tequila 750ml",
                "start_date": datetime(2026, 5, 1),
                "end_date": datetime(2026, 5, 5),
                "is_active": True,
                "notes": "Seasonal — Cinco de Mayo tequila spike. Stock up ahead of May 1.",
            },
            {
                "title": "Memorial Day Weekend — Beer Cases",
                "description": "All 24-pack beer cases — $2 off. Stock up for the cookout.",
                "promo_type": "Dollar Off",
                "discount_value": 2.00,
                "category": "Beer",
                "product_name": "All 24-pack Cases",
                "start_date": datetime(2026, 5, 23),
                "end_date": datetime(2026, 5, 26),
                "is_active": True,
                "notes": "Memorial Day is our biggest beer weekend of the year",
            },
        ]
        for p in promos:
            db.add(Promotion(**p))
        await db.flush()
        print(f"   ✓ {len(promos)} promotions loaded")

        # ── FIFA EDITION DON JULIO 1942 ────────────────────────────────────────
        print("\n⚽ Adding FIFA Edition Don Julio 1942...")
        r = await db.execute(select(Product).where(Product.sku == "DON-JULIO-1942-FIFA"))
        if not r.scalar_one_or_none():
            db.add(Product(
                name="Don Julio 1942 FIFA World Cup Edition",
                display_name="Don Julio 1942 FIFA World Cup Edition",
                raw_name="DON JULIO 1942 FIFA EDITION",
                sku="DON-JULIO-1942-FIFA",
                brand_family="Don Julio",
                category="Hard Liquor",
                subcategory="Tequila",
                product_line="1942 FIFA Edition",
                size_label="750ml",
                size_bucket="Fifth",
                nominal_ml=750,
                pack_type="Bottle",
                unit="750ml",
                price_tier="Premium",
                demand_type="Seasonal",
                demand_band="High",
                quantity_sold_proxy=3,
                reorder_priority="High",
                sell_price=199.99,
                cost_price=115.99,
                predicted_price=199.99,
                stock=6,
                reorder_point=2,
                reorder_qty=6,
                supplier_name="RNDC Maryland",
                description="Limited edition Don Julio 1942 Añejo Tequila — FIFA World Cup 2026 "
                            "commemorative bottle. Same premium 1942 liquid in special collector's "
                            "packaging. Aged 2.5 years in American white-oak barrels. "
                            "Perfect for collectors and gifting.",
                notes="FIFA World Cup 2026 limited edition. Display prominently near register. "
                      "Priced at $199.99 same as standard 1942. Reorder from RNDC.",
                is_active=True,
                is_seasonal=True,
                season_tags=["fifa", "world_cup", "limited_edition", "collector"],
                exclude_flag=False,
            ))
            print("   ✓ Don Julio 1942 FIFA World Cup Edition — $199.99")
        else:
            print("   → FIFA Don Julio already exists")

        await db.commit()

        print(f"\n{'='*55}")
        print(f"✅ STORE DATA LOADED!")
        print(f"   Suppliers:  3 (Breakthru, RNDC, McLane)")
        print(f"   Expenses:   4 months recurring + one-time")
        print(f"   Promotions: {len(promos)}")
        print(f"   New product: Don Julio 1942 FIFA Edition — $199.99")
        print(f"\n🎯 Refresh http://localhost:5173")
        print(f"   Expenses → will show monthly costs")
        print(f"   Suppliers → Breakthru + RNDC + McLane")
        print(f"   Promotions → 8 active deals")
        print(f"   Inventory → search 'FIFA' to find the new bottle")

asyncio.run(main())
