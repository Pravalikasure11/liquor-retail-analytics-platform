"""
Zach's Liquor Store — POS Photo Import Router
Reads all photos from pos_photos/ folder, extracts products using Claude vision,
and saves them directly to the PostgreSQL database.

Endpoint: POST /admin/import-pos-photos
"""
import anthropic
import base64
import json
import os
import asyncio
from pathlib import Path
from fastapi import APIRouter, Depends, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from app.database import get_db
from app.models.models import Product, Sale, SaleItem, User
from app.core.security import get_current_user

router = APIRouter(prefix="/admin", tags=["admin"])

# ── Config ────────────────────────────────────────────────────────────────────
PHOTOS_DIR = Path(__file__).parent.parent.parent / "pos_photos"

CAT_MAP = {
    "BEER": "Beer", "LIQUOR": "Hard Liquor", "WINE": "Wine",
    "CIGARETTES": "Cigarettes", "CIGARETTES1": "Cigarettes",
    "GROCERY": "Snacks & Chips", "MISC": "Accessories",
    "ELECTRONIC SMOKING D": "E-Cigarettes", "ELECTRONIC SMOKING": "E-Cigarettes",
    "SODA": "Cool Drinks", "NON TAX": None,
}
MARGINS = {
    "Beer": 0.38, "Hard Liquor": 0.42, "Wine": 0.45,
    "Cigarettes": 0.20, "Snacks & Chips": 0.40,
    "Accessories": 0.50, "E-Cigarettes": 0.38, "Cool Drinks": 0.38,
}
SKIP = {
    "BAG", "REUSABLE BAG", "CREDIT CARD FEE", "1.47 BEER", "1.01 BEER",
    "1.00 BEER", "2.75 BEER", "1.38 BEER", "2.99 CIGARETTES",
    "3.99 GROCERY", "4.99 GROCERY", "1.49 GROCERY", "2.00 GROCERY",
}

PROMPT = """This is a photo of an Aenasys POS Best Items sales report from a liquor store.
Extract EVERY row visible in the table. Columns: No, Item Group, Item Name, Size, Qty, Total.

Return ONLY a raw JSON array, no markdown, no explanation:
[{"no":3,"group":"BEER","name":"NATURAL ICE 25OZ","size":"25","qty":2157,"total":3454.8}]

Rules:
- Extract every row you can see, even partial ones at screen edges
- Size "N/A" should be null
- Total is a plain number (no $ sign)
- Include ALL rows, not just some"""


def image_to_b64(path: Path) -> str:
    with open(path, "rb") as f:
        return base64.standard_b64encode(f.read()).decode()


def process_row(row: dict) -> dict | None:
    grp  = (row.get("group") or "").upper().strip()
    name = (row.get("name")  or "").strip().upper()
    qty  = int(row.get("qty") or 0)
    tot  = float(row.get("total") or 0)

    if not name or qty == 0: return None
    if CAT_MAP.get(grp) is None: return None
    if name in SKIP: return None

    cat  = CAT_MAP.get(grp, "Accessories")
    sell = round(tot / qty, 2) if qty > 0 else 0
    cost = round(sell * (1 - MARGINS.get(cat, 0.40)), 2)
    size = row.get("size")
    size = None if not size or str(size).upper() in ("N/A", "NA", "") else str(size)
    no   = int(row.get("no", 0))

    monthly = max(1, round(qty / 3.6))  # 108 days = 3.6 months

    return {
        "no":            no,
        "name":          name.title(),
        "sku":           name.replace(" ", "-")[:18] + f"-{no:04d}",
        "category":      cat,
        "subcategory":   grp.title(),
        "size":          size,
        "unit":          size or "each",
        "qty_sold":      qty,
        "total_revenue": round(tot, 2),
        "sell_price":    sell,
        "cost_price":    cost,
        "margin_pct":    round(MARGINS.get(cat, 0.40) * 100),
        "stock":         max(5, monthly),
        "reorder_point": max(3, round(monthly * 0.3)),
        "reorder_qty":   max(12, monthly),
    }


async def extract_from_image(client: anthropic.Anthropic, path: Path) -> list:
    """Send one image to Claude vision and extract product rows."""
    try:
        b64 = image_to_b64(path)
        ext = path.suffix.lower()
        media = {"jpg": "image/jpeg", ".jpeg": "image/jpeg",
                 ".png": "image/png", ".webp": "image/webp"}.get(ext, "image/jpeg")

        response = client.messages.create(
            model="claude-opus-4-5",
            max_tokens=4096,
            messages=[{
                "role": "user",
                "content": [
                    {"type": "image", "source": {"type": "base64", "media_type": media, "data": b64}},
                    {"type": "text",  "text": PROMPT}
                ]
            }]
        )

        text = response.content[0].text.strip()
        if "```" in text:
            text = text.split("```")[1]
            if text.startswith("json"): text = text[4:]

        return json.loads(text.strip())
    except json.JSONDecodeError:
        return []
    except Exception as e:
        return []


@router.post("/import-pos-photos")
async def import_pos_photos(
    background_tasks: BackgroundTasks,
    clear_existing: bool = True,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Import all products from POS photos folder into database.
    Streams progress as Server-Sent Events.
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return {"error": "ANTHROPIC_API_KEY not set in environment"}

    if not PHOTOS_DIR.exists():
        return {"error": f"Photos folder not found: {PHOTOS_DIR}"}

    images = sorted([
        f for f in PHOTOS_DIR.iterdir()
        if f.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}
    ])

    if not images:
        return {"error": "No images found in pos_photos folder"}

    async def stream_import():
        client = anthropic.Anthropic(api_key=api_key)
        products = {}  # (name, size) -> product dict

        yield f"data: {json.dumps({'status': 'starting', 'total': len(images)})}\n\n"

        # Clear existing products if requested
        if clear_existing:
            async with AsyncSessionLocal() as clear_db:
                await clear_db.execute(delete(SaleItem))
                await clear_db.execute(delete(Sale))
                await clear_db.execute(delete(Product))
                await clear_db.commit()
            yield f"data: {json.dumps({'status': 'cleared', 'message': 'Existing products cleared'})}\n\n"

        # Process each image
        for i, img_path in enumerate(images, 1):
            rows = await asyncio.get_event_loop().run_in_executor(
                None, lambda p=img_path: asyncio.run(extract_from_image(client, p))
            )

            new_count = 0
            for row in rows:
                p = process_row(row)
                if not p: continue
                key = (p["name"].upper(), p["size"] or "")
                if key in products:
                    products[key]["qty_sold"]      += p["qty_sold"]
                    products[key]["total_revenue"] += p["total_revenue"]
                    if products[key]["qty_sold"] > 0:
                        s = round(products[key]["total_revenue"] / products[key]["qty_sold"], 2)
                        products[key]["sell_price"] = s
                        m = MARGINS.get(products[key]["category"], 0.40)
                        products[key]["cost_price"] = round(s * (1 - m), 2)
                else:
                    products[key] = p
                    new_count += 1

            yield f"data: {json.dumps({'status': 'processing', 'image': i, 'total': len(images), 'filename': img_path.name, 'rows': len(rows), 'new': new_count, 'total_products': len(products)})}\n\n"

            await asyncio.sleep(0.5)

        # Save all products to database
        yield f"data: {json.dumps({'status': 'saving', 'message': f'Saving {len(products)} products to database...'})}\n\n"

        final = sorted(products.values(), key=lambda x: x["qty_sold"], reverse=True)

        async with AsyncSessionLocal() as save_db:
            saved = 0
            for p in final:
                product = Product(
                    name=p["name"],
                    sku=p["sku"],
                    category=p["category"],
                    subcategory=p.get("subcategory"),
                    unit=p["unit"],
                    cost_price=p["cost_price"],
                    sell_price=p["sell_price"],
                    predicted_price=round(p["sell_price"] * 1.05, 2),
                    stock=p["stock"],
                    reorder_point=p["reorder_point"],
                    reorder_qty=p["reorder_qty"],
                    description=f"Rank #{p['no']}. {p['qty_sold']:,} units sold Jan-Apr 2026.",
                    is_active=True,
                )
                save_db.add(product)
                saved += 1

            await save_db.commit()

        yield f"data: {json.dumps({'status': 'complete', 'products_saved': saved, 'message': f'Successfully imported {saved} real products from Zach store POS data!'})}\n\n"

    return StreamingResponse(stream_import(), media_type="text/event-stream")


@router.get("/import-status")
async def import_status():
    """Check if photos folder exists and how many images are ready."""
    if not PHOTOS_DIR.exists():
        return {"ready": False, "message": f"Photos folder not found: {PHOTOS_DIR}"}
    images = [f for f in PHOTOS_DIR.iterdir() if f.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}]
    return {
        "ready": len(images) > 0,
        "photo_count": len(images),
        "folder": str(PHOTOS_DIR),
        "message": f"{len(images)} photos ready to import"
    }


# Need this for the streaming endpoint
from app.database import AsyncSessionLocal
