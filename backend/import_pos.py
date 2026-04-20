"""
Run from your backend folder:
    cd ~/Downloads/zachs/backend
    source venv/bin/activate
    python import_pos.py
"""
import anthropic, asyncio, base64, json, os
from pathlib import Path
from app.database import AsyncSessionLocal, create_tables
from app.models.models import Product
from sqlalchemy import delete

PHOTOS_DIR = Path(__file__).parent.parent / "pos_photos"
API_KEY    = os.environ.get("ANTHROPIC_API_KEY", "")

CAT_MAP = {
    "BEER":"Beer","LIQUOR":"Hard Liquor","WINE":"Wine",
    "CIGARETTES":"Cigarettes","CIGARETTES1":"Cigarettes",
    "GROCERY":"Snacks & Chips","MISC":"Accessories",
    "ELECTRONIC SMOKING D":"E-Cigarettes","SODA":"Cool Drinks","NON TAX":None,
}
MARGINS = {
    "Beer":0.38,"Hard Liquor":0.42,"Wine":0.45,"Cigarettes":0.20,
    "Snacks & Chips":0.40,"Accessories":0.50,"E-Cigarettes":0.38,"Cool Drinks":0.38,
}
SKIP = {"BAG","REUSABLE BAG","CREDIT CARD FEE","1.47 BEER","1.01 BEER",
        "1.00 BEER","2.75 BEER","3.99 GROCERY","4.99 GROCERY","1.49 GROCERY"}

PROMPT = """Aenasys POS Best Items photo. Extract ALL rows.
Return ONLY JSON array, no markdown:
[{"no":3,"group":"BEER","name":"NATURAL ICE 25OZ","size":"25","qty":2157,"total":3454.8}]
Size N/A = null. Total = plain number."""


def extract_from_image(client, path):
    b64 = base64.standard_b64encode(open(path,"rb").read()).decode()
    try:
        r = client.messages.create(
            model="claude-opus-4-5", max_tokens=4096,
            messages=[{"role":"user","content":[
                {"type":"image","source":{"type":"base64","media_type":"image/jpeg","data":b64}},
                {"type":"text","text":PROMPT}
            ]}]
        )
        text = r.content[0].text.strip()
        if "```" in text:
            text = text.split("```")[1]
            if text.startswith("json"): text = text[4:]
        return json.loads(text.strip())
    except:
        return []


async def main():
    if not API_KEY:
        print("❌ Set ANTHROPIC_API_KEY first:")
        print("   export ANTHROPIC_API_KEY=your-key")
        return

    images = sorted([f for f in PHOTOS_DIR.iterdir()
                     if f.suffix.lower() in {".jpg",".jpeg",".png"}])
    print(f"🥃 Found {len(images)} photos — importing to your app database...")

    client   = anthropic.Anthropic(api_key=API_KEY)
    products = {}

    for i, img in enumerate(images, 1):
        print(f"[{i:3}/{len(images)}] {img.name}", end=" ", flush=True)
        rows = extract_from_image(client, img)
        new  = 0
        for row in rows:
            grp  = (row.get("group") or "").upper().strip()
            name = (row.get("name")  or "").strip().upper()
            qty  = int(row.get("qty") or 0)
            tot  = float(row.get("total") or 0)
            if not name or qty==0 or CAT_MAP.get(grp) is None or name in SKIP: continue
            cat  = CAT_MAP.get(grp,"Accessories")
            sell = round(tot/qty,2)
            cost = round(sell*(1-MARGINS.get(cat,0.40)),2)
            size = row.get("size")
            size = None if not size or str(size).upper() in ("N/A","NA","") else str(size)
            no   = int(row.get("no",0))
            key  = (name, size or "")
            if key in products:
                products[key]["qty_sold"]      += qty
                products[key]["total_revenue"] += tot
                s = round(products[key]["total_revenue"]/products[key]["qty_sold"],2)
                products[key]["sell_price"] = s
                products[key]["cost_price"] = round(s*(1-MARGINS.get(cat,0.40)),2)
            else:
                monthly = max(1, round(qty/3.6))
                products[key] = {
                    "name":name.title(),"sku":name.replace(" ","-")[:18]+f"-{no:04d}",
                    "category":cat,"subcategory":grp.title(),"size":size,"unit":size or "each",
                    "qty_sold":qty,"total_revenue":round(tot,2),"sell_price":sell,"cost_price":cost,
                    "stock":max(5,monthly),"reorder_point":max(3,round(monthly*0.3)),
                    "reorder_qty":max(12,monthly),
                    "description":f"Rank #{no}. {qty:,} units sold Jan-Apr 2026.",
                }
                new += 1
        print(f"→ {len(rows)} rows | {new} new | {len(products)} total")

    # Save to your existing database
    print(f"\n💾 Saving {len(products)} products to your database...")
    async with AsyncSessionLocal() as db:
        # Clear old demo products
        from app.models.models import SaleItem, Sale
        await db.execute(delete(SaleItem))
        await db.execute(delete(Sale))
        await db.execute(delete(Product))
        await db.flush()

        for p in sorted(products.values(), key=lambda x: x["qty_sold"], reverse=True):
            db.add(Product(
                name=p["name"], sku=p["sku"],
                category=p["category"], subcategory=p["subcategory"],
                unit=p["unit"], cost_price=p["cost_price"],
                sell_price=p["sell_price"],
                predicted_price=round(p["sell_price"]*1.05,2),
                stock=p["stock"], reorder_point=p["reorder_point"],
                reorder_qty=p["reorder_qty"],
                description=p["description"], is_active=True,
            ))
        await db.commit()

    print(f"✅ Done! {len(products)} real products from Zach's store are now in your app!")
    print(f"   Open http://localhost:5173 → Inventory to see them all.")

asyncio.run(main())
