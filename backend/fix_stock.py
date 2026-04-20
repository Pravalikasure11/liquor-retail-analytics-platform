"""
Fix stock levels + add supplier deals.
Run: python fix_stock.py
"""
import asyncio, random
from datetime import datetime, timedelta
from app.database import AsyncSessionLocal, create_tables
from app.models.models import Product, SupplierDeal, Supplier
from sqlalchemy import select

async def main():
    await create_tables()
    async with AsyncSessionLocal() as db:

        # Fix stock levels
        print("📦 Setting realistic stock levels...")
        r = await db.execute(select(Product).where(Product.is_active==True))
        products = list(r.scalars())
        stock_ranges = {"High":(8,20),"Medium":(5,12),"Low":(2,8)}
        for p in products:
            lo,hi = stock_ranges.get(p.demand_band or "Low",(2,8))
            p.stock = random.randint(lo,hi)
            if random.random() < 0.08: p.stock = 0
            elif random.random() < 0.12: p.stock = max(1, p.reorder_point - 1)
        await db.flush()
        out = sum(1 for p in products if p.stock==0)
        low = sum(1 for p in products if 0 < p.stock <= p.reorder_point)
        print(f"   ✓ {len(products)} products | {out} out of stock | {low} low stock")

        # Get supplier IDs
        r = await db.execute(select(Supplier))
        sups = {s.name:s.id for s in r.scalars()}
        breakthru = sups.get("Breakthru Beverage Maryland",1)
        rndc      = sups.get("RNDC Maryland",1)
        mclane    = sups.get("McLane Company",1)
        now = datetime.utcnow()

        # Add supplier deals
        print("\n🏷️  Adding supplier deals...")
        deals = [
            SupplierDeal(supplier_id=breakthru,title="Modelo 12-Pack — Save $8/case (Buy 4+)",
                description="Buy 4+ cases of Modelo 12-pack, save $8 per case through end of month.",
                discount_pct=5.0,deal_price=None,product_name="Modelo Core 12-pack",
                category="Beer",valid_until=now+timedelta(days=30),source="breakthru",is_read=False,is_active=True),
            SupplierDeal(supplier_id=breakthru,title="Natural Ice 24-Pack — Summer Stock-Up $16.99",
                description="Natural Ice 24-pack: buy 6+ cases at $16.99 (reg $18.99). Top summer seller.",
                discount_pct=10.6,original_price=18.99,deal_price=16.99,product_name="Natural Ice 24pk",
                category="Beer",valid_until=now+timedelta(days=45),source="breakthru",is_read=False,is_active=True),
            SupplierDeal(supplier_id=breakthru,title="Fireball Minis — Free POS Display (Buy 2 Cases)",
                description="Order 2 cases of Fireball 50ml, get free countertop display. Great checkout impulse driver.",
                product_name="Fireball Core 50ml",category="Hard Liquor",
                valid_until=now+timedelta(days=60),source="breakthru",is_read=False,is_active=True),
            SupplierDeal(supplier_id=rndc,title="Hennessy VS — Spring Deal 8% Off All Sizes",
                description="Hennessy VS 50ml, 200ml, 375ml, 750ml, 1.75L — all 8% off through May 31.",
                discount_pct=8.0,original_price=59.99,deal_price=55.19,product_name="Hennessy VS 750ml",
                category="Hard Liquor",valid_until=now+timedelta(days=30),source="rndc",is_read=False,is_active=True),
            SupplierDeal(supplier_id=rndc,title="Don Julio 1942 FIFA Edition — Pre-Order Now",
                description="Don Julio 1942 FIFA World Cup 2026 Edition available. Cost $115.99/bottle. "
                            "Limited allocation — sell for $199.99. Pre-order through RNDC rep.",
                deal_price=115.99,product_name="Don Julio 1942 FIFA Edition",
                category="Hard Liquor",valid_until=now+timedelta(days=90),source="rndc",is_read=False,is_active=True),
            SupplierDeal(supplier_id=rndc,title="Patron Silver — Cinco de Mayo Bundle $52.99",
                description="Patron Silver 750ml + branded cup set. $52.99 cost (reg $56.99). "
                            "Shelf-ready display. Perfect Cinco de Mayo push May 1-5.",
                discount_pct=6.1,original_price=56.99,deal_price=52.99,product_name="Patron Silver 750ml",
                category="Hard Liquor",valid_until=datetime(2026,5,6),source="rndc",is_read=False,is_active=True),
            SupplierDeal(supplier_id=rndc,title="Tito's 1.75L — $2 Off Per Bottle (Buy 6+)",
                description="Tito's Handmade Vodka 1.75L: buy 6+ bottles, save $2 each. Strong everyday mover.",
                discount_pct=4.6,original_price=43.59,deal_price=41.59,product_name="Titos 1.75 Ltr 1.75L",
                category="Hard Liquor",valid_until=now+timedelta(days=30),source="rndc",is_read=False,is_active=True),
            SupplierDeal(supplier_id=mclane,title="Newport Carton — $3 Off Per Carton (Buy 10+)",
                description="Buy 10+ Newport cartons, save $3/carton. Stack with in-store promo for max pull-through.",
                discount_pct=2.3,product_name="Newport Core Carton",
                category="Tobacco",valid_until=now+timedelta(days=45),source="mclane",is_read=False,is_active=True),
            SupplierDeal(supplier_id=mclane,title="Monster Energy — Buy 2 Cases Get 1 Free",
                description="Monster Energy 24-can cases: buy 2 get 1 free. Strong summer energy drink demand.",
                discount_pct=33.0,product_name="Monster Energy Single",
                category="Cool Drinks",valid_until=now+timedelta(days=30),source="mclane",is_read=False,is_active=True),
            SupplierDeal(supplier_id=mclane,title="Backwoods Honey — New Flavor In Stock",
                description="Backwoods Honey cigar wraps now available. $2.28/pack. High demand from tobacco customers.",
                product_name="Backwoods Honey",category="Tobacco",
                valid_until=now+timedelta(days=60),source="mclane",is_read=False,is_active=True),
        ]
        for d in deals: db.add(d)
        await db.commit()
        print(f"   ✓ {len(deals)} deals added")
        print(f"\n✅ Done! Restart backend then refresh http://localhost:5173")
        print(f"   Stock Alerts → {out} out of stock, {low} low")
        print(f"   Supplier Deals → {len(deals)} deals from Breakthru, RNDC, McLane")
        print(f"   Seasonal → click any season card to see YoY data")

asyncio.run(main())
