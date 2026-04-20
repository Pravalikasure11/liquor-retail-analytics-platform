"""Seasonal Analytics Service — Fixed for Zach's store"""
from datetime import datetime, date, timedelta
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, extract

SEASONS = {
    "new_year":      {"label":"New Year's",       "month":1,  "day_start":1,  "day_end":3},
    "super_bowl":    {"label":"Super Bowl",        "month":2,  "day_start":8,  "day_end":12},
    "st_patricks":   {"label":"St. Patrick's Day", "month":3,  "day_start":14, "day_end":18},
    "cinco_de_mayo": {"label":"Cinco de Mayo",     "month":5,  "day_start":3,  "day_end":6},
    "memorial_day":  {"label":"Memorial Day",      "month":5,  "day_start":24, "day_end":27},
    "july_4th":      {"label":"4th of July",       "month":7,  "day_start":2,  "day_end":6},
    "labor_day":     {"label":"Labor Day",         "month":9,  "day_start":1,  "day_end":3},
    "halloween":     {"label":"Halloween",         "month":10, "day_start":29, "day_end":31},
    "thanksgiving":  {"label":"Thanksgiving",      "month":11, "day_start":27, "day_end":30},
    "christmas":     {"label":"Christmas",         "month":12, "day_start":22, "day_end":26},
    "new_year_eve":  {"label":"New Year's Eve",    "month":12, "day_start":28, "day_end":31},
}

def get_season_windows(season_key: str, year: int) -> list:
    if season_key not in SEASONS:
        return []
    s = SEASONS[season_key]
    try:
        return [{"key": season_key, "label": s["label"],
                 "start": date(year, s["month"], s["day_start"]).isoformat(),
                 "end":   date(year, s["month"], s["day_end"]).isoformat(),
                 "year":  year}]
    except ValueError:
        return []

async def compute_yoy_comparison(db: AsyncSession, windows: list, season_key: str) -> dict:
    from app.models.models import Sale, SaleItem, Product
    if not windows or season_key not in SEASONS:
        return {"error": "unknown season"}
    
    s = SEASONS[season_key]
    results = {}
    
    for year in [2024, 2025, 2026]:
        try:
            start = datetime(year, s["month"], s["day_start"])
            end   = datetime(year, s["month"], s["day_end"], 23, 59, 59)
        except ValueError:
            continue
        
        r = await db.execute(select(
            func.coalesce(func.sum(Sale.total_revenue), 0),
            func.coalesce(func.sum(Sale.total_profit), 0),
            func.count(Sale.id))
            .where(Sale.sale_date >= start, Sale.sale_date <= end))
        rev, profit, txns = r.one()
        
        # Top category
        rc = await db.execute(select(
            Product.category,
            func.coalesce(func.sum(SaleItem.subtotal), 0).label("rev"))
            .join(SaleItem, SaleItem.product_id == Product.id)
            .join(Sale, Sale.id == SaleItem.sale_id)
            .where(Sale.sale_date >= start, Sale.sale_date <= end)
            .group_by(Product.category)
            .order_by(func.sum(SaleItem.subtotal).desc())
            .limit(3))
        top_cats = [{"category": row[0], "revenue": round(row[1], 2)} for row in rc]
        
        results[str(year)] = {
            "year": year, "revenue": round(rev, 2),
            "profit": round(profit, 2), "transactions": txns,
            "top_categories": top_cats,
        }
    
    # Compute YoY changes
    def pct(a, b): return round((a-b)/b*100, 1) if b else None
    
    y25 = results.get("2025", {})
    y24 = results.get("2024", {})
    y26 = results.get("2026", {})
    
    return {
        "season": s["label"],
        "season_key": season_key,
        "years": results,
        "yoy_2025_vs_2024": {
            "revenue_pct": pct(y25.get("revenue",0), y24.get("revenue",0)),
            "profit_pct":  pct(y25.get("profit",0),  y24.get("profit",0)),
        },
        "yoy_2026_vs_2025": {
            "revenue_pct": pct(y26.get("revenue",0), y25.get("revenue",0)),
            "profit_pct":  pct(y26.get("profit",0),  y25.get("profit",0)),
        },
        "recommended_stock": _get_stock_recommendations(season_key),
    }

def _get_stock_recommendations(season_key: str) -> list:
    recs = {
        "super_bowl":    [("Beer — cases & 24-packs","High"),("Chips & Snacks","High"),("Soda 2L","Medium")],
        "st_patricks":   [("Jameson Irish Whiskey","High"),("Beer — Guinness, Heineken","High"),("Green beer mixers","Medium")],
        "cinco_de_mayo": [("Don Julio all sizes","High"),("Patron Silver","High"),("Jose Cuervo","High"),("Corona & Modelo","High")],
        "memorial_day":  [("Beer 24-packs","High"),("Vodka liters","Medium"),("Soda & mixers","Medium")],
        "july_4th":      [("Beer cases","High"),("Tequila liters","High"),("Vodka liters","High"),("Soda & ice","High")],
        "labor_day":     [("Beer cases","High"),("Liquor liters","Medium"),("Wine","Low")],
        "halloween":     [("Tequila minis (50ml)","High"),("Vodka","Medium"),("Beer","Medium")],
        "thanksgiving":  [("Wine — all types","High"),("Whiskey","High"),("Hennessy","Medium")],
        "christmas":     [("Hennessy gift sizes","High"),("Don Julio 1942","High"),("Wine","High"),("Whiskey","High")],
        "new_year_eve":  [("Don Julio 1942","High"),("Champagne/sparkling","High"),("Patron","High"),("Tequila minis","High")],
        "new_year":      [("Hennessy","High"),("Tequila","Medium"),("Beer","Medium")],
    }
    return [{"item": item, "priority": pri} for item, pri in recs.get(season_key, [])]
